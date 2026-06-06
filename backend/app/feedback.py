"""Server-side scoring for single-select MCQ exercises.

Grading lives on the backend so the client never holds the answers. Given an
exercise, the option ids that were displayed to the user, and the user's
selected id, score the answer and return the explanation/references.
"""

from app.models import MCQ


class FeedbackError(Exception):
    """Base class for feedback scoring errors."""


class FeedbackValidationError(FeedbackError):
    """Raised when the request payload is inconsistent with the exercise.

    Examples: an exercise that is not a single-select MCQ, displayed option
    ids that aren't valid for the exercise, or a displayed set that does not
    contain exactly one correct option.
    """


def find_exercise(exercises: list, exercise_id: str):
    """Return the loaded exercise with the given id, or None if not found."""
    for exercise in exercises:
        if exercise.id == exercise_id:
            return exercise
    return None


def score_single_select(
    exercise,
    displayed_option_ids: list[str],
    selected_id: str,
) -> dict:
    """Score a single-select MCQ answer.

    Args:
        exercise: The loaded exercise object (expected to be an ``MCQ``).
        displayed_option_ids: The (original) option ids that were shown to the
            user. Exactly one of these must map to a ``correct: true`` option.
        selected_id: The (original) option id the user selected. Must be one of
            ``displayed_option_ids``.

    Returns:
        ``{correct, correctOptionId, explanation, references}`` where
        ``correctOptionId`` is the displayed id whose pool option is correct
        and ``correct`` is ``selected_id == correctOptionId``.

    Raises:
        FeedbackValidationError: If the exercise is not a single-select MCQ,
            the displayed ids aren't valid for the exercise, there isn't
            exactly one correct option among the displayed ids, or the selected
            id wasn't among the displayed ids.
    """
    if not isinstance(exercise, MCQ):
        raise FeedbackValidationError(
            f"exercise '{getattr(exercise, 'id', '<unknown>')}' is not a "
            f"single-select MCQ and cannot be scored as one"
        )

    # Map original option ids -> Option for fast, authoritative lookup.
    options_by_id = {opt.id: opt for opt in exercise.options}

    # The display contract is exactly 4 distinct options (1 correct + 3
    # distractors). Enforce it so a crafted/buggy request can't be scored
    # against a smaller or duplicated displayed set.
    if len(displayed_option_ids) != 4:
        raise FeedbackValidationError(
            f"displayedOptionIds must contain exactly 4 options for exercise "
            f"'{exercise.id}', found {len(displayed_option_ids)}"
        )
    if len(set(displayed_option_ids)) != len(displayed_option_ids):
        raise FeedbackValidationError(
            f"displayedOptionIds must not contain duplicate ids for exercise '{exercise.id}'"
        )

    # Every displayed id must be a real option id for this exercise.
    unknown = [oid for oid in displayed_option_ids if oid not in options_by_id]
    if unknown:
        raise FeedbackValidationError(
            f"displayedOptionIds contains ids not valid for exercise "
            f"'{exercise.id}': {', '.join(unknown)}"
        )

    # Exactly one displayed option must be the correct one (1-correct +
    # distractors display contract).
    correct_displayed = [oid for oid in displayed_option_ids if options_by_id[oid].correct]
    if len(correct_displayed) != 1:
        raise FeedbackValidationError(
            f"displayedOptionIds must contain exactly one correct option for "
            f"exercise '{exercise.id}', found {len(correct_displayed)}"
        )

    # The selected id must be one of the ids actually shown.
    if selected_id not in displayed_option_ids:
        raise FeedbackValidationError(
            f"selectedId '{selected_id}' was not among the displayed options "
            f"for exercise '{exercise.id}'"
        )

    correct_option_id = correct_displayed[0]

    return {
        "correct": selected_id == correct_option_id,
        "correctOptionId": correct_option_id,
        "explanation": exercise.explanation,
        "references": list(exercise.references),
    }
