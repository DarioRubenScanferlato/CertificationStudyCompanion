"""Pydantic models for exercise content."""

from enum import Enum

from pydantic import BaseModel, Field, root_validator, validator


class ExerciseType(str, Enum):
    """Exercise type enum."""

    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    CODE_COMPLETION = "code_completion"


class ExamType(str, Enum):
    """Certification exam type."""

    ASSOCIATE = "associate"
    PROFESSIONAL = "professional"


class Difficulty(str, Enum):
    """Exercise difficulty level."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Domain(str, Enum):
    """Exam domain (Associates)."""

    # Associate domains (5 total)
    LAKEHOUSE_PLATFORM = "Databricks Lakehouse Platform"
    ELT_SPARK = "ELT with Spark SQL and Python"
    INCREMENTAL_PROCESSING = "Incremental Data Processing"
    PRODUCTION_PIPELINES = "Production Pipelines"
    DATA_GOVERNANCE = "Data Governance"

    # Professional domains (for future) - commented out for now
    # DATABRICKS_TOOLING = "Databricks Tooling"
    # DATA_PROCESSING = "Data Processing"
    # DATA_MODELING = "Data Modeling"
    # SECURITY_GOVERNANCE = "Security & Governance"
    # MONITORING_LOGGING = "Monitoring & Logging"
    # TESTING_DEPLOYMENT = "Testing & Deployment"


class Option(BaseModel):
    """MCQ option."""

    id: str = Field(..., description="Option identifier (a, b, c, d, etc.)")
    text: str = Field(..., description="Option text")
    correct: bool = Field(..., description="Whether this option is correct")


class BaseExercise(BaseModel):
    """Base exercise model with common fields."""

    id: str = Field(..., description="Unique exercise identifier")
    type: ExerciseType = Field(..., description="Exercise type")
    exam: ExamType = Field(..., description="Target exam")
    domain: Domain = Field(..., description="Exam domain")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    question: str = Field(..., description="Question text or prompt")
    explanation: str = Field(..., description="Explanation of the answer")
    references: list[str] = Field(default_factory=list, description="Reference URLs")
    tags: list[str] = Field(default_factory=list, description="Topic tags")
    source: str = Field(default="original", description="Question source/provenance")


class MCQ(BaseExercise):
    """Multiple choice question.

    The correct answers are derived from the options flagged ``correct: true``.
    ``answer`` is computed, not author-supplied, so the option ``correct`` flags
    are the single source of truth — any ``answer`` provided in input is ignored
    and overwritten.
    """

    type: ExerciseType = Field(default=ExerciseType.SINGLE_CHOICE)
    options: list[Option] = Field(..., description="Answer options")
    answer: list[str] = Field(
        default_factory=list,
        description="Correct option IDs (derived from options where correct=true)",
    )

    @validator("options")
    def options_not_empty(cls, v):
        """Ensure at least one option."""
        if not v:
            raise ValueError("Must have at least one option")
        return v

    @root_validator(skip_on_failure=True)
    def derive_answer_from_correct(cls, values):
        """Derive ``answer`` from the options marked correct.

        Enforces that at least one option is correct, and that a
        ``single_choice`` exercise has exactly one correct option.
        """
        options = values.get("options")
        if not options:
            return values

        correct_ids = [opt.id for opt in options if opt.correct]
        if not correct_ids:
            raise ValueError("MCQ must have at least one option marked correct")

        exercise_type = values.get("type")
        if exercise_type == ExerciseType.SINGLE_CHOICE and len(correct_ids) != 1:
            raise ValueError(
                f"single_choice exercise must have exactly one correct option, "
                f"found {len(correct_ids)}"
            )

        values["answer"] = correct_ids
        return values


class CodeCompletion(BaseExercise):
    """Code completion (Wordle-style) exercise."""

    type: ExerciseType = Field(default=ExerciseType.CODE_COMPLETION)
    language: str = Field(..., description="Programming language (sql, pyspark, python)")
    template: str = Field(..., description="Code template with ___ blank")
    answer: str = Field(..., description="Canonical answer")
    accepted: list[str] = Field(default_factory=list, description="Alternative accepted answers")
    case_sensitive: bool = Field(default=False, description="Whether answer is case-sensitive")
    ignore_whitespace: bool = Field(default=True, description="Whether to ignore whitespace")

    @validator("template")
    def template_has_blank(cls, v):
        """Ensure template has a blank."""
        if "___" not in v:
            raise ValueError("Template must contain '___' for the blank")
        return v

    @validator("answer")
    def answer_not_empty(cls, v):
        """Ensure answer is not empty."""
        if not v or not v.strip():
            raise ValueError("Answer must not be empty")
        return v


# Discriminated union type
Exercise = MCQ | CodeCompletion
