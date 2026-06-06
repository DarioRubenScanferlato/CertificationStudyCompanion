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

from app import store
from app.models import MCQ, ExerciseType

# A Displayed Option is intentionally just {id, text} — no `correct` flag.
DisplayedOption = dict[str, str]

# A built session entry. See ``build_session_entry`` / ``build_session``.
SessionEntry = dict[str, object]


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
