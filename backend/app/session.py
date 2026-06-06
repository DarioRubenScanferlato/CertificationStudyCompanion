"""Server-side session randomizer (Epic 5, Story 5.3).

This module turns authored exercises into a *displayed* practice session. It is
stateless and non-deterministic by design: every call samples and shuffles
uniformly at random with no seed and no anti-repeat memory. This is what powers
MCQ variety so the same exercise looks different across sessions (FR-21).

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


def build_session(exercises: list) -> list[SessionEntry]:
    """Build a randomized session from a list of exercises.

    Returns the exercises in **randomized order** (FR-21). Each MCQ carries its
    freshly sampled + shuffled ``displayedOptions``. Non-MCQ exercises (e.g.
    ``code_completion``) are **skipped** — MCQ is the focus of this session
    builder and the endpoint can build code-completion payloads separately.

    The input list is not mutated; a shuffled copy is produced internally.

    Args:
        exercises: A list of exercise objects (``MCQ`` and/or ``CodeCompletion``).

    Returns:
        A list of session-entry dicts (see :func:`build_session_entry`) for the
        MCQs only, in randomized order.
    """
    mcqs = [
        ex for ex in exercises if isinstance(ex, MCQ) and ex.type != ExerciseType.CODE_COMPLETION
    ]

    order = list(mcqs)
    random.shuffle(order)

    return [build_session_entry(mcq) for mcq in order]
