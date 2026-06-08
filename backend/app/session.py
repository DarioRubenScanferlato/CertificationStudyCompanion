"""Server-side session randomizer (Epic 5, Story 5.3; Epic 7, Story 7.3).

This module turns authored exercises into a *displayed* practice session.

Per-MCQ rendering is stateless and non-deterministic by design: every call
samples and shuffles options uniformly at random with no seed. This is what
powers MCQ variety so the same exercise looks different across sessions (FR-20).

Cross-exercise *ordering*, however, is history-aware (FR-24, supersedes FR-21's
pure-random ordering): :func:`build_session` partitions MCQs into *unseen* (no
recorded attempt) and *seen* (>=1 recorded attempt) using the attempt store, and
serves unseen first (randomized within the unseen group), then seen ordered
least-recently-seen first. Callers that want representative, non-history-aware
ordering (e.g. the Mock-Exam builder) pass ``prioritize_unseen=False``.

Shared contract (downstream endpoint + frontend stories depend on it):

* Each MCQ is an *Option Pool*: >=1 option with ``correct: true`` and >=3 with
  ``correct: false`` (enforced by :class:`app.models.MCQ`).
* A *Displayed Option* is ``{"id": <original authored id>, "text": <text>}``.
  Exactly **1** correct option and **3** incorrect options are sampled from the
  pool and returned in **randomized array order**. The ``id`` is always the
  option's ORIGINAL authored id (e.g. ``"a"``, ``"b"``...). Shuffling only
  affects the array order of the 4 displayed options — ids are never renumbered
  or relabelled.
* Displayed Options NEVER include the ``correct`` flag (no answer leakage to the
  client). The endpoint/frontend must resolve correctness server-side against
  the original authored options, not against the displayed payload.

These are pure functions over passed-in exercises. They do not load files; the
endpoint story is responsible for loading exercises and passing them in.
"""

import random
from dataclasses import dataclass

from app import store
from app.models import MCQ, Domain, ExamType, ExerciseType

# A Displayed Option is intentionally just {id, text} — no `correct` flag.
DisplayedOption = dict[str, str]

# A built session entry. See ``build_session_entry`` / ``build_session``.
SessionEntry = dict[str, object]


@dataclass(frozen=True)
class MockExamConfig:
    """Per-exam Mock-Exam shape (Story 8.3, FR-27).

    Single source of truth for the full-length mock builder:

    * ``total_questions`` — the exam's full length (Associate 45, Professional 59).
    * ``duration_minutes`` — the exam clock the response stamps (Associate 90,
      Professional 120). The backend only stamps it; the countdown is frontend
      (FR-26/28).
    * ``domain_weights`` — the published per-Domain weight split (percent),
      keyed by the :class:`~app.models.Domain` members that belong to this exam.
      Weights sum to 100; per-domain target counts are derived from these via
      largest-remainder rounding so they total ``total_questions`` exactly.

    Sourced from PRD addendum §C (both exams VERIFIED against the official
    Databricks exam guides; OQ-1 resolved 2026-06-07).
    """

    total_questions: int
    duration_minutes: int
    domain_weights: dict[Domain, int]


# Authoritative Mock-Exam config per exam (addendum §C — both verified).
#
# Associate: 45Q / 90min, 7 domains (May 2026 blueprint weights).
# Professional: 59Q / 120min, 10 domains (2026 blueprint weights).
# Each weight vector sums to 100 and is keyed only by that exam's Domain members.
MOCK_EXAM_CONFIGS: dict[ExamType, MockExamConfig] = {
    ExamType.ASSOCIATE: MockExamConfig(
        total_questions=45,
        duration_minutes=90,
        domain_weights={
            Domain.INTELLIGENCE_PLATFORM: 6,
            Domain.DATA_INGESTION_LOADING: 21,
            Domain.DATA_TRANSFORMATION_MODELING: 22,
            Domain.LAKEFLOW_JOBS: 16,
            Domain.CICD: 10,
            Domain.TROUBLESHOOTING_MONITORING_OPTIMIZATION: 10,
            Domain.GOVERNANCE_SECURITY: 15,
        },
    ),
    ExamType.PROFESSIONAL: MockExamConfig(
        total_questions=59,
        duration_minutes=120,
        domain_weights={
            Domain.DEV_CODE_PROCESSING: 22,
            Domain.COST_PERFORMANCE: 13,
            Domain.DATA_TRANSFORMATION: 10,
            Domain.MONITORING_ALERTING: 10,
            Domain.DATA_SECURITY_COMPLIANCE: 10,
            Domain.DEBUGGING_DEPLOYING: 10,
            Domain.DATA_INGESTION: 7,
            Domain.DATA_GOVERNANCE: 7,
            Domain.DATA_MODELLING: 6,
            Domain.DATA_SHARING_FEDERATION: 5,
        },
    ),
}


def _largest_remainder_targets(weights: dict[Domain, int], total: int) -> dict[Domain, int]:
    """Allocate ``total`` across domains by their weights (largest remainder).

    Each domain's ideal share is ``weight / sum(weights) * total``. Every domain
    first gets the floor of its ideal share; the leftover seats (``total`` minus
    the sum of the floors) are then handed out one each to the domains with the
    largest fractional remainders (ties broken by larger weight, then Domain
    order) so the per-domain counts sum to ``total`` exactly with no rounding
    drift.

    Returns a dict mapping every domain in ``weights`` to its integer target
    (always sums to ``total`` when ``total >= 0`` and at least one weight is
    positive).
    """
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        return {domain: 0 for domain in weights}

    floors: dict[Domain, int] = {}
    remainders: list[tuple[float, int, Domain]] = []
    for domain, weight in weights.items():
        ideal = weight * total / weight_sum
        floor = int(ideal)
        floors[domain] = floor
        # Sort key: larger remainder first, then larger weight, then enum order
        # (negated so Python's ascending sort yields the desired descending one).
        remainders.append((ideal - floor, -weight, domain))

    leftover = total - sum(floors.values())
    # Hand the leftover seats to the largest remainders.
    remainders.sort(key=lambda item: (-item[0], item[1], item[2].value))
    for _, _, domain in remainders[: max(leftover, 0)]:
        floors[domain] += 1

    return floors


def build_displayed_options(mcq: MCQ) -> list[DisplayedOption]:
    """Build the 4 Displayed Options for a single MCQ.

    Samples exactly 1 option from the pool's *correct* set and 3 from the
    *incorrect* set, then returns them as ``{"id", "text"}`` dicts in randomized
    array order. The ``correct`` flag is deliberately omitted so the correct
    answer is never leaked to the client.

    Args:
        mcq: An Option Pool MCQ (>=1 correct, >=3 incorrect — guaranteed by the
            model validator).

    Returns:
        A list of exactly 4 Displayed Options, ``{"id": <original id>,
        "text": <text>}``, in randomized order. Exactly one of them corresponds
        to a correct option from the pool.
    """
    correct = [opt for opt in mcq.options if opt.correct]
    incorrect = [opt for opt in mcq.options if not opt.correct]

    # The model guarantees >=1 correct and >=3 incorrect, but stay defensive so
    # a malformed object fails loudly rather than silently emitting <4 options.
    if len(correct) < 1 or len(incorrect) < 3:
        raise ValueError(
            f"MCQ '{mcq.id}' is not a valid Option Pool: need >=1 correct and "
            f">=3 incorrect, found {len(correct)} correct / {len(incorrect)} "
            f"incorrect"
        )

    chosen = random.sample(correct, 1) + random.sample(incorrect, 3)
    random.shuffle(chosen)

    return [{"id": opt.id, "text": opt.text} for opt in chosen]


def build_session_entry(mcq: MCQ) -> SessionEntry:
    """Build a single session entry for one MCQ.

    The shape (consumed by the endpoint and frontend) is::

        {
            "exerciseId": str,
            "type": "single_choice",
            "domain": str,            # Domain enum value
            "difficulty": str,        # Difficulty enum value
            "question": str,
            "codeContext": str | None,  # currently always None for MCQ
            "displayedOptions": [{"id": str, "text": str}, ... x4],
        }

    Args:
        mcq: The MCQ to render.

    Returns:
        A session-entry dict with sampled + shuffled ``displayedOptions``.
    """
    return {
        "exerciseId": mcq.id,
        "type": mcq.type.value,
        "domain": mcq.domain.value,
        "difficulty": mcq.difficulty.value,
        "question": mcq.question,
        "codeContext": None,
        "displayedOptions": build_displayed_options(mcq),
    }


def _order_unseen_first(mcqs: list[MCQ]) -> list[MCQ]:
    """Order MCQs unseen-first using the attempt store (FR-24).

    Partitions the MCQs into *unseen* (no recorded attempt) and *seen* (>=1
    recorded attempt), then returns unseen first — randomized within the unseen
    group — followed by seen ordered least-recently-seen first (oldest
    ``last_seen`` timestamp first). When every MCQ is seen this naturally falls
    back to the full set in least-recently-seen order (no empty/blocked state).

    The store is read exactly once each for ``attempted_ids`` and
    ``last_seen_map`` to keep the build efficient.
    """
    attempted = store.attempted_ids()
    last_seen = store.last_seen_map()

    unseen = [mcq for mcq in mcqs if mcq.id not in attempted]
    seen = [mcq for mcq in mcqs if mcq.id in attempted]

    # Randomize within the unseen group (variety among new material).
    random.shuffle(unseen)

    # Seen: least-recently-seen first. Missing timestamps (shouldn't happen for
    # an attempted id, but stay defensive) sort first as "" so they're served
    # before anything with a real timestamp.
    seen.sort(key=lambda mcq: last_seen.get(mcq.id, ""))

    return unseen + seen


def build_session(
    exercises: list,
    *,
    prioritize_unseen: bool = True,
) -> list[SessionEntry]:
    """Build a session from a list of exercises.

    Each MCQ carries its freshly sampled + shuffled ``displayedOptions`` (FR-20,
    always random). Non-MCQ exercises (e.g. ``code_completion``) are **skipped**
    — MCQ is the focus of this session builder and the endpoint can build
    code-completion payloads separately.

    Cross-exercise ordering depends on ``prioritize_unseen``:

    * ``True`` (default): **unseen-first** (FR-24). Unseen MCQs (no recorded
      attempt in the store) are served first, randomized within that group;
      seen MCQs follow, ordered least-recently-seen first. Reads the attempt
      store once via :func:`_order_unseen_first`.
    * ``False``: the prior **pure-random** ordering (FR-21), with no dependence
      on history — used by callers like the Mock-Exam builder that want a
      representative set that may repeat seen exercises.

    The input list is not mutated; a reordered copy is produced internally.

    Args:
        exercises: A list of exercise objects (``MCQ`` and/or ``CodeCompletion``).
        prioritize_unseen: Order unseen exercises before seen ones (default
            ``True``). Pass ``False`` for history-independent random ordering.

    Returns:
        A list of session-entry dicts (see :func:`build_session_entry`) for the
        MCQs only, ordered per ``prioritize_unseen``.
    """
    mcqs = [
        ex for ex in exercises if isinstance(ex, MCQ) and ex.type != ExerciseType.CODE_COMPLETION
    ]

    if prioritize_unseen:
        order = _order_unseen_first(mcqs)
    else:
        order = list(mcqs)
        random.shuffle(order)

    return [build_session_entry(mcq) for mcq in order]


def build_mock_session(exercises: list, *, exam: ExamType) -> list[SessionEntry]:
    """Build a domain-weighted, full-length Mock-Exam session for one exam (FR-27).

    Unlike :func:`build_session`, this is **representative, not unseen-first**:
    it groups the (already exam-scoped) MCQs by domain, allocates per-domain
    target counts from the exam's published weights via largest-remainder
    rounding (summing to ``total_questions``), and samples that many per domain
    at random — **without consulting the attempt store** (a mock may repeat
    already-seen questions). The selected MCQs are then shuffled and rendered.

    If a domain has fewer MCQs than its target, all available are taken (the
    session is capped at the available corpus rather than crashing). Non-MCQ
    exercises are skipped. Each entry still carries 4 sampled + shuffled,
    flag-less ``displayedOptions``.

    Args:
        exercises: Exercises already scoped to ``exam`` (caller filters by exam).
        exam: The exam whose :data:`MOCK_EXAM_CONFIGS` sizing/weights to apply.

    Returns:
        A list of session-entry dicts in randomized order. The caller stamps the
        exam ``durationMinutes`` (from the config) onto the response.
    """
    config = MOCK_EXAM_CONFIGS.get(exam)
    if config is None:
        return []

    mcqs = [
        ex for ex in exercises if isinstance(ex, MCQ) and ex.type != ExerciseType.CODE_COMPLETION
    ]
    by_domain: dict[Domain, list[MCQ]] = {}
    for mcq in mcqs:
        by_domain.setdefault(mcq.domain, []).append(mcq)

    targets = _largest_remainder_targets(config.domain_weights, config.total_questions)

    selected: list[MCQ] = []
    for domain, target in targets.items():
        pool = by_domain.get(domain, [])
        take = min(target, len(pool))
        if take > 0:
            selected.extend(random.sample(pool, take))

    random.shuffle(selected)
    return [build_session_entry(mcq) for mcq in selected]
