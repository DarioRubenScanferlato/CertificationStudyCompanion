"""Exercise content loader."""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.models import MCQ, CodeCompletion

# Explicit type -> model dispatch. Anything not listed here is reported as an
# unknown type rather than silently coerced into an MCQ.
TYPE_MODELS = {
    "single_choice": MCQ,
    "multi_choice": MCQ,
    "code_completion": CodeCompletion,
}


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ContentValidationError:
    """Represents a validation error during content loading."""

    def __init__(
        self,
        error_type: str,
        file_path: str,
        exercise_id: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize a content validation error.

        Args:
            error_type: Type of error (yaml_syntax, missing_field, invalid_enum, etc.)
            file_path: Path to the YAML file
            exercise_id: Exercise ID if applicable
            message: Error message
            details: Additional error details
        """
        self.error_type = error_type
        self.file_path = file_path
        self.exercise_id = exercise_id
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the error."""
        parts = [f"[{self.error_type}]", f"File: {self.file_path}"]
        if self.exercise_id:
            parts.append(f"Exercise: {self.exercise_id}")
        if self.message:
            parts.append(f"Message: {self.message}")
        if self.details:
            details_str = ", ".join(f"{k}: {v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")
        return " | ".join(parts)


def load_exercises_from_directory(
    base_path: str | None = None,
) -> tuple[list, int, list[ContentValidationError]]:
    """
    Load all exercises from YAML files in a directory.

    Args:
        base_path: Root directory containing exercise subdirectories.
                  If None, resolves to project root/exercises

    Returns:
        Tuple of:
            - exercises: List of validated Exercise objects
            - error_count: Number of errors encountered
            - error_log: List of ContentValidationError objects with detailed info
    """
    exercises = []
    error_count = 0
    error_log: list[ContentValidationError] = []
    seen_ids = set()

    if base_path is None:
        # Find project root by going up from this file until we find exercises/
        current_dir = Path(__file__).parent
        while current_dir != current_dir.parent:
            candidate = current_dir.parent / "exercises"
            if candidate.exists():
                base_path = str(candidate)
                break
            current_dir = current_dir.parent
        if base_path is None:
            base_path = "exercises"

    base_dir = Path(base_path)
    if not base_dir.exists():
        msg = f"Content directory {base_path} does not exist"
        logger.warning(msg)
        return exercises, error_count, error_log

    logger.info(f"Loading exercises from {base_dir}")

    # Find all YAML files recursively
    yaml_files = list(base_dir.glob("**/*.yaml")) + list(base_dir.glob("**/*.yml"))
    logger.info(f"Found {len(yaml_files)} YAML files to process")

    for yaml_file in sorted(yaml_files):
        logger.info(f"Processing {yaml_file.name}")

        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "exercises" not in data:
                error = ContentValidationError(
                    error_type="missing_exercises_key",
                    file_path=str(yaml_file),
                    message="YAML file missing 'exercises' key",
                )
                error_log.append(error)
                error_count += 1
                logger.warning(f"Missing 'exercises' key in {yaml_file.name}")
                continue

            logger.info(f"Found {len(data['exercises'])} exercises in {yaml_file.name}")

            for idx, exercise_data in enumerate(data["exercises"]):
                try:
                    # Determine exercise type and create appropriate model.
                    # A missing type defaults to MCQ (the model defaults to
                    # single_choice). An explicitly-provided but unknown type is
                    # reported as such, rather than silently coerced into MCQ.
                    exercise_type = exercise_data.get("type")
                    exercise_id = exercise_data.get("id", f"UNKNOWN_{idx}")

                    if exercise_type is None:
                        model_cls = MCQ
                    else:
                        model_cls = TYPE_MODELS.get(exercise_type)
                    if model_cls is None:
                        error_count += 1
                        error = ContentValidationError(
                            error_type="unknown_type",
                            file_path=str(yaml_file),
                            exercise_id=exercise_id,
                            message=(
                                f"Unknown exercise type {exercise_type!r}. "
                                f"Valid types: {', '.join(sorted(TYPE_MODELS))}"
                            ),
                        )
                        error_log.append(error)
                        logger.error(str(error))
                        continue

                    # Reject duplicate IDs: they silently collide downstream
                    # (e.g. as Anki note GUIDs), causing content loss.
                    if exercise_id in seen_ids:
                        error_count += 1
                        error = ContentValidationError(
                            error_type="duplicate_id",
                            file_path=str(yaml_file),
                            exercise_id=exercise_id,
                            message=f"Duplicate exercise id '{exercise_id}' (already loaded)",
                        )
                        error_log.append(error)
                        logger.error(str(error))
                        continue

                    exercise = model_cls(**exercise_data)
                    seen_ids.add(exercise_id)

                    exercises.append(exercise)
                    logger.debug(f"Successfully loaded exercise {exercise_id}")

                except ValidationError as e:
                    error_count += 1
                    exercise_id = exercise_data.get("id", f"UNKNOWN_{idx}")

                    # Extract detailed validation error information
                    error_details = {}
                    error_messages = []
                    for error_item in e.errors():
                        field = ".".join(str(x) for x in error_item.get("loc", []))
                        error_msg = error_item.get("msg", "Unknown error")
                        error_type = error_item.get("type", "validation_error")
                        error_details[field] = f"{error_type}: {error_msg}"
                        error_messages.append(f"{field}: {error_msg}")

                    validation_error = ContentValidationError(
                        error_type="validation_error",
                        file_path=str(yaml_file),
                        exercise_id=exercise_id,
                        message="; ".join(error_messages),
                        details=error_details,
                    )
                    error_log.append(validation_error)
                    logger.error(str(validation_error))

                except Exception as e:
                    error_count += 1
                    exercise_id = exercise_data.get("id", f"UNKNOWN_{idx}")

                    error = ContentValidationError(
                        error_type="parsing_error",
                        file_path=str(yaml_file),
                        exercise_id=exercise_id,
                        message=str(e),
                        details={"exception_type": type(e).__name__},
                    )
                    error_log.append(error)
                    logger.error(str(error))

        except yaml.YAMLError as e:
            error_count += 1

            # problem_mark may be absent OR present-but-None; guard both.
            mark = getattr(e, "problem_mark", None)
            error = ContentValidationError(
                error_type="yaml_syntax_error",
                file_path=str(yaml_file),
                message=str(e),
                details={"line": mark.line if mark is not None else None},
            )
            error_log.append(error)
            logger.error(str(error))

        except Exception as e:
            error_count += 1

            error = ContentValidationError(
                error_type="file_read_error",
                file_path=str(yaml_file),
                message=str(e),
                details={"exception_type": type(e).__name__},
            )
            error_log.append(error)
            logger.error(str(error))

    logger.info(
        f"Content loading complete: {len(exercises)} exercises loaded, "
        f"{error_count} errors encountered"
    )

    return exercises, error_count, error_log


def filter_exercises(
    exercises: list,
    domain: str | None = None,
    difficulty: str | None = None,
    exam: str | None = None,
    exercise_type: str | None = None,
) -> list:
    """
    Filter exercises by criteria.

    Args:
        exercises: List of exercise objects
        domain: Filter by domain (case-insensitive)
        difficulty: Filter by difficulty (easy, medium, hard)
        exam: Filter by exam (associate, professional)
        exercise_type: Filter by type (single_choice, multi_choice, code_completion)

    Returns:
        Filtered list of exercises
    """
    result = exercises
    filters_applied = []

    # All filters are case-insensitive and whitespace-tolerant. Enum members
    # subclass str, so compare against the normalized ``.value``.
    if domain:
        domain_norm = domain.strip().lower()
        result = [e for e in result if e.domain.value.lower() == domain_norm]
        filters_applied.append(f"domain={domain}")

    if difficulty:
        difficulty_norm = difficulty.strip().lower()
        result = [e for e in result if e.difficulty.value.lower() == difficulty_norm]
        filters_applied.append(f"difficulty={difficulty}")

    if exam:
        exam_norm = exam.strip().lower()
        result = [e for e in result if e.exam.value.lower() == exam_norm]
        filters_applied.append(f"exam={exam}")

    if exercise_type:
        type_norm = exercise_type.strip().lower()
        result = [e for e in result if e.type.value.lower() == type_norm]
        filters_applied.append(f"type={exercise_type}")

    if filters_applied:
        logger.info(
            f"Filtered {len(exercises)} exercises -> {len(result)} results "
            f"with filters: {', '.join(filters_applied)}"
        )
    else:
        logger.debug(f"No filters applied, returning all {len(exercises)} exercises")

    return result
