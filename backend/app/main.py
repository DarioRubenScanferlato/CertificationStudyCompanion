import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import feedback_store, store
from app.anki import export_to_anki
from app.content import filter_exercises, load_exercises_from_directory
from app.feedback import (
    FeedbackValidationError,
    find_exercise,
    score_single_select,
)
from app.models import MCQ, Difficulty, Domain, ExamType, ExerciseType
from app.session import MOCK_EXAM_CONFIGS, build_mock_session, build_session
from app.store import init_db

# Configure logging
logger = logging.getLogger(__name__)


# Startup event to load exercises
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load exercises on startup."""
    # Create the local SQLite attempt store if absent (AR-16 / Story 7.1).
    init_db()
    logger.info("Loading exercises...")
    exercises, error_count, error_log = load_exercises_from_directory()
    app.state.exercises = exercises
    app.state.error_log = error_log
    logger.info(f"Loaded {len(exercises)} exercises with {error_count} errors")
    if error_log:
        logger.warning(f"First error example: {error_log[0]}")
    yield
    # Cleanup on shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Databricks DE Cert Study Companion API",
    description="Backend API for studying for Databricks Data Engineer certification",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS with environment-based origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"success": True, "data": {"status": "healthy", "version": "0.1.0"}, "error": None}


@app.get("/api/health")
def api_health():
    """API health check endpoint."""
    return {"success": True, "data": {"status": "API healthy"}, "error": None}


def _validate_exercise_types(exercise_types: "list[str] | None") -> list[str]:
    """Validate a (repeatable) exercise_type filter, returning any error strings.

    Accepts a list of type values (the Start-screen multiselect, Story 4.7) and
    checks each against the ExerciseType enum, case-insensitively. An empty/None
    filter is valid (means "all types").
    """
    if not exercise_types:
        return []
    valid_values = [member.value for member in ExerciseType]
    valid_lower = [v.lower() for v in valid_values]
    errors = []
    for value in exercise_types:
        if value is None or value.strip().lower() not in valid_lower:
            errors.append(
                f"Invalid exercise type '{value}'. Valid values are: {', '.join(valid_values)}"
            )
            logger.warning(f"Invalid exercise type filter attempted: {value}")
    return errors


@app.get("/api/exercises")
def get_exercises(
    domain: str = Query(None, description="Filter by domain (one of the 7 Associate sections)"),
    difficulty: str = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
    exercise_type: str = Query(
        None, description="Filter by type (single_choice, multi_choice, code_completion)"
    ),
):
    """
    Get exercises with optional filtering.

    Query Parameters:
    - domain: Filter by one of the 7 Associate sections (case-insensitive)
      Valid values: "Databricks Intelligence Platform", "Data Ingestion and Loading",
      "Data Transformation and Modeling", "Working with Lakeflow Jobs",
      "Implementing CI/CD", "Troubleshooting, Monitoring, and Optimization",
      "Governance and Security"
    - difficulty: Filter by difficulty level (easy, medium, hard)
    - exam: Filter by exam type (associate, professional)
    - exercise_type: Filter by exercise type (single_choice, multi_choice, code_completion)

    Returns:
    {
        "success": bool,
        "data": [...exercises...],
        "error": null | error_message
    }
    """
    # Guard against the endpoint being hit before startup populated state.
    exercises = getattr(app.state, "exercises", [])
    errors = []

    # All filters are validated case-insensitively and whitespace-tolerantly,
    # matching the behavior of filter_exercises.
    for label, value, enum_cls, valid_noun in (
        ("domain", domain, Domain, "domains"),
        ("difficulty", difficulty, Difficulty, "values"),
        ("exam type", exam, ExamType, "values"),
        ("exercise type", exercise_type, ExerciseType, "values"),
    ):
        if not value:
            continue
        valid_values = [member.value for member in enum_cls]
        if value.strip().lower() not in [v.lower() for v in valid_values]:
            errors.append(
                f"Invalid {label} '{value}'. Valid {valid_noun} are: {', '.join(valid_values)}"
            )
            logger.warning(f"Invalid {label} filter attempted: {value}")

    # Return validation errors
    if errors:
        error_message = "; ".join(errors)
        return {"success": False, "data": [], "error": error_message}

    # Apply filters
    filtered = filter_exercises(
        exercises, domain=domain, difficulty=difficulty, exam=exam, exercise_type=exercise_type
    )

    # Serialize to dict for JSON response
    exercise_dicts = [e.dict() for e in filtered]

    return {"success": True, "data": exercise_dicts, "error": None}


@app.get("/api/sessions")
def get_session(
    domain: str = Query(None, description="Filter by domain (case-insensitive)"),
    difficulty: str = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
    exercise_type: Annotated[
        list[str] | None,
        Query(
            description=(
                "Filter by type(s) (single_choice, multi_choice, code_completion). "
                "Repeatable — pass several to include multiple types (Start-screen multiselect)."
            ),
        ),
    ] = None,
    mode: str = Query(None, description="'mock' for a full-length domain-weighted mock exam"),
):
    """
    Build a randomized practice session.

    Filters the loaded exercises (same domain/difficulty/exam semantics as
    ``GET /api/exercises``) and runs the result through the session randomizer.
    MCQs are returned in randomized order, each with exactly 4 flag-less
    ``displayedOptions`` (no ``correct`` flags are ever leaked to the client).
    Code-completion exercises are delivered too (carrying their template/answer
    for client-side feedback); the client routes by entry ``type``. Pass
    ``exercise_type=code_completion`` to scope a session to the code-completion
    drill (or ``single_choice`` for MCQ-only).

    Query Parameters:
    - domain: Filter by domain (case-insensitive)
    - difficulty: Filter by difficulty level (easy, medium, hard)
    - exam: Filter by exam type (associate, professional; case-insensitive)
    - exercise_type: Filter by exercise type (single_choice, multi_choice,
      code_completion; case-insensitive)

    Default-exam policy: a session must never mix the Associate and
    Professional corpora. When ``exam`` is omitted it defaults to
    ``associate`` before filtering, so this endpoint never returns a
    mixed-exam result (the frontend always sends an explicit ``exam``; the
    default only governs raw/no-UI callers).

    Returns:
    {
        "success": bool,
        "data": [...session entries...],  # [] when no exercises match
        "error": null | error_message
    }

    Each session entry has the shape::

        {
            "exerciseId": str,
            "type": str,
            "domain": str,
            "difficulty": str,
            "question": str,
            "codeContext": str | None,
            "displayedOptions": [{"id": str, "text": str}, ... x4],
        }
    """
    # Guard against the endpoint being hit before startup populated state.
    exercises = getattr(app.state, "exercises", [])
    errors = []

    # Validate filters case-insensitively, matching GET /api/exercises.
    for label, value, enum_cls, valid_noun in (
        ("domain", domain, Domain, "domains"),
        ("difficulty", difficulty, Difficulty, "values"),
        ("exam type", exam, ExamType, "values"),
    ):
        if not value:
            continue
        valid_values = [member.value for member in enum_cls]
        if value.strip().lower() not in [v.lower() for v in valid_values]:
            errors.append(
                f"Invalid {label} '{value}'. Valid {valid_noun} are: {', '.join(valid_values)}"
            )
            logger.warning(f"Invalid {label} filter attempted: {value}")

    # exercise_type is a (repeatable) list — validate each value.
    errors.extend(_validate_exercise_types(exercise_type))

    if errors:
        return {"success": False, "data": [], "error": "; ".join(errors)}

    # Mock-Exam mode (FR-27): a full-length, domain-weighted set scoped to one
    # exam, NOT unseen-first. Exam is required (a mock is exam-specific) and the
    # response stamps the exam's countdown duration (the timer is frontend).
    if mode and mode.strip().lower() == "mock":
        if not exam:
            return {
                "success": False,
                "data": [],
                "error": "Mock exam requires an 'exam' (associate or professional).",
            }
        exam_norm = exam.strip().lower()
        exam_enum = ExamType(exam_norm)
        scoped = filter_exercises(exercises, exam=exam_norm)
        session = build_mock_session(scoped, exam=exam_enum)
        return {
            "success": True,
            "data": session,
            "error": None,
            "durationMinutes": MOCK_EXAM_CONFIGS[exam_enum].duration_minutes,
        }

    # Default-exam policy: never pass exam=None to filter_exercises (a no-op
    # that would mix the Associate + Professional corpora). Default to
    # associate when the caller omits exam.
    exam = exam or ExamType.ASSOCIATE.value

    # Reuse the shared filter helper (same approach as GET /api/exercises).
    filtered = filter_exercises(
        exercises, domain=domain, difficulty=difficulty, exam=exam, exercise_type=exercise_type
    )

    # An empty filter result is a successful empty session, not an error.
    session = build_session(filtered)

    return {"success": True, "data": session, "error": None}


@app.get("/api/exercises/count")
def get_exercise_count(
    domain: str = Query(None, description="Filter by domain (case-insensitive)"),
    difficulty: str = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
    exercise_type: Annotated[
        list[str] | None,
        Query(
            description=(
                "Filter by type(s) (single_choice, multi_choice, code_completion). "
                "Repeatable — pass several to include multiple types (Start-screen multiselect)."
            ),
        ),
    ] = None,
):
    """
    Count the exercises matching the given filters (Start-screen preview).

    Returns a lightweight match count so the Start screen can show
    "{n} questions match" before a session is started. The response carries
    ONLY the count -- no exercise objects, options, pools, displayedOptions,
    explanations, references, or ``correct`` flags are ever serialized
    (preserving the FR-20 non-leakage rule).

    Query Parameters:
    - domain: Filter by domain (case-insensitive)
    - difficulty: Filter by difficulty level (easy, medium, hard)
    - exam: Filter by exam type (associate, professional; case-insensitive)

    Default-exam policy: the count must never reflect a mixed-exam corpus.
    When ``exam`` is omitted it defaults to ``associate`` before filtering,
    mirroring ``GET /api/sessions`` so the preview count and the resulting
    session population always agree (the frontend always sends an explicit
    ``exam``; the default only governs raw/no-UI callers).

    Returns:
    {
        "success": bool,
        "data": {"count": int} | null,
        "error": null | error_message
    }
    """
    # Guard against the endpoint being hit before startup populated state.
    exercises = getattr(app.state, "exercises", [])
    errors = []

    # Validate filters case-insensitively, matching GET /api/sessions.
    for label, value, enum_cls, valid_noun in (
        ("domain", domain, Domain, "domains"),
        ("difficulty", difficulty, Difficulty, "values"),
        ("exam type", exam, ExamType, "values"),
    ):
        if not value:
            continue
        valid_values = [member.value for member in enum_cls]
        if value.strip().lower() not in [v.lower() for v in valid_values]:
            errors.append(
                f"Invalid {label} '{value}'. Valid {valid_noun} are: {', '.join(valid_values)}"
            )
            logger.warning(f"Invalid {label} filter attempted: {value}")

    # exercise_type is a (repeatable) list — validate each value.
    errors.extend(_validate_exercise_types(exercise_type))

    if errors:
        return {"success": False, "data": None, "error": "; ".join(errors)}

    # Default-exam policy: never count across mixed corpora (see get_session).
    exam = exam or ExamType.ASSOCIATE.value

    # Reuse the shared filter helper; serialize only the count (no exercises).
    filtered = filter_exercises(
        exercises, domain=domain, difficulty=difficulty, exam=exam, exercise_type=exercise_type
    )

    return {"success": True, "data": {"count": len(filtered)}, "error": None}


class SessionByIdsRequest(BaseModel):
    """Request body for POST /api/sessions.

    ``exerciseIds`` are the ORIGINAL authored exercise ids (e.g.
    ``"dbx-de-0001"``). The endpoint builds a fresh, re-sampled and re-shuffled
    session over just those exercises so "Restart" / "Practice these again"
    never replay identical questions (FR-20/21). Unknown ids are dropped and
    logged at WARNING, never treated as fatal.
    """

    exerciseIds: list[str] = Field(
        ...,
        description="Original authored exercise ids to build a session from (e.g. 'dbx-de-0001')",
    )
    exam: str | None = Field(
        default=None,
        description=(
            "Optional exam scope (associate, professional). When provided, the "
            "replay is restricted to exercises of that exam so it can never mix "
            "the Associate and Professional corpora."
        ),
    )


@app.post("/api/sessions")
def post_session(request: SessionByIdsRequest):
    """Build a fresh randomized session from an explicit set of exercise ids.

    Filters the loaded exercises down to those whose ``id`` is in
    ``request.exerciseIds``, then runs the matched subset through the same
    session randomizer as ``GET /api/sessions``. Because ``build_session``
    re-shuffles order and re-samples + re-shuffles each MCQ's displayed options
    on every call, replays are automatically fresh with no extra randomization
    logic (FR-20/21). Code-completion exercises are skipped by the builder.

    Request body::

        {"exerciseIds": ["dbx-de-0001", "dbx-de-0002", ...], "exam": "associate"}

    ``exam`` is optional (associate, professional; case-insensitive). When
    given, it scopes the replay to that exam so a session never mixes the two
    corpora; an invalid value is an error. Because POST replays an explicit,
    already-scoped id set rather than the whole corpus, omitting ``exam`` does
    NOT default to associate here (that would silently drop a legitimately
    Professional id set the caller asked to replay).

    Unknown / unmatched ids are dropped and logged at WARNING; the request still
    succeeds over the recognized subset. An empty (or all-unknown)
    ``exerciseIds`` returns a successful empty list, not an error.

    Returns the standard ``{success, data, error}`` wrapper; ``data`` has the
    exact same shape as ``GET /api/sessions`` (see :func:`get_session`).
    """
    # Validate the optional exam scope case-insensitively, mirroring the GET
    # endpoints' validation pattern.
    if request.exam:
        valid_values = [member.value for member in ExamType]
        if request.exam.strip().lower() not in [v.lower() for v in valid_values]:
            logger.warning(f"Invalid exam type filter attempted: {request.exam}")
            return {
                "success": False,
                "data": [],
                "error": (
                    f"Invalid exam type '{request.exam}'. "
                    f"Valid values are: {', '.join(valid_values)}"
                ),
            }

    # Guard against the endpoint being hit before startup populated state.
    exercises = getattr(app.state, "exercises", [])

    # Build a lookup of recognized exercises by id.
    by_id = {ex.id: ex for ex in exercises}

    # Partition requested ids into matched vs unknown, preserving request order
    # for selection determinism (build_session re-randomizes order anyway).
    matched = []
    unknown = []
    for exercise_id in request.exerciseIds:
        exercise = by_id.get(exercise_id)
        if exercise is None:
            unknown.append(exercise_id)
        else:
            matched.append(exercise)

    # A stale frontend id set should be diagnosable but never fatal.
    if unknown:
        logger.warning(
            "POST /api/sessions: dropping %d unknown exercise id(s): %s",
            len(unknown),
            unknown,
        )

    # When an exam scope is supplied, reuse filter_exercises to keep only that
    # exam's exercises -- a replay must never mix corpora (no new filter path).
    if request.exam:
        matched = filter_exercises(matched, exam=request.exam)

    # Reuse the Story 5.3 randomizer; an empty match list yields an empty session.
    # Replay is an explicit id set ("Restart" / "Practice these again") — do NOT
    # apply unseen-first ordering (those ids are deliberately chosen and usually
    # all already-seen); keep it freshly sampled + randomly ordered.
    session = build_session(matched, prioritize_unseen=False)

    return {"success": True, "data": session, "error": None}


@app.get("/api/export/anki")
def export_anki(
    domain: str = Query(None, description="Filter by domain"),
    difficulty: str = Query(None, description="Filter by difficulty (easy, medium, hard)"),
):
    """Export MCQ exercises to Anki .apkg format."""
    exercises = app.state.exercises

    # Apply filters
    filtered = filter_exercises(
        exercises,
        domain=domain,
        difficulty=difficulty,
    )

    # Filter to only MCQ exercises
    mcq_exercises = [e for e in filtered if isinstance(e, MCQ)]

    if not mcq_exercises:
        return {
            "success": False,
            "data": None,
            "error": "No MCQ exercises found matching the filters",
        }

    # Create temporary file for the .apkg
    with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        # Export to Anki format
        export_to_anki(mcq_exercises, tmp_path)

        # Return the file as a download
        return FileResponse(
            tmp_path,
            media_type="application/octet-stream",
            filename="databricks-de-cert.apkg",
            headers={"Content-Disposition": "attachment; filename='databricks-de-cert.apkg'"},
        )
    except Exception as e:
        return {"success": False, "data": None, "error": f"Failed to export to Anki: {str(e)}"}


class FeedbackRequest(BaseModel):
    """Request body for POST /api/feedback.

    All ids are the ORIGINAL authored option ids (e.g. "a", "b"). Of the
    ``displayedOptionIds`` shown to the user, exactly one maps to a correct
    option, and ``selectedId`` is the user's choice among them.
    """

    exerciseId: str = Field(..., description="Id of the exercise being answered")
    displayedOptionIds: list[str] = Field(
        ..., description="Original ids of the options that were displayed (the 4 shown)"
    )
    selectedId: str = Field(..., description="Original id of the option the user selected")
    type: str = Field(default="mcq", description="Exercise type ('mcq' / 'single_choice')")
    timeTakenMs: int | None = Field(
        default=None,
        ge=0,
        description="Per-question time in milliseconds (FR-28); null if not tracked",
    )


# Types this endpoint can grade. Code-completion is a later epic.
_SUPPORTED_FEEDBACK_TYPES = {"mcq", "single_choice"}


@app.post("/api/feedback")
def post_feedback(request: FeedbackRequest):
    """Score a single-select MCQ answer server-side.

    Request body: ``{exerciseId, displayedOptionIds, selectedId, type}``.

    Returns the standard ``{success, data, error}`` wrapper. On success,
    ``data`` is ``{correct, correctOptionId, explanation, references}``.
    """
    # Only single-select grading is supported for now.
    if request.type not in _SUPPORTED_FEEDBACK_TYPES:
        return {
            "success": False,
            "data": None,
            "error": (
                f"Unsupported feedback type '{request.type}'. "
                f"Only single-select MCQ scoring is supported."
            ),
        }

    exercises = getattr(app.state, "exercises", [])
    exercise = find_exercise(exercises, request.exerciseId)
    if exercise is None:
        return {
            "success": False,
            "data": None,
            "error": f"Exercise '{request.exerciseId}' not found",
        }

    try:
        result = score_single_select(
            exercise,
            request.displayedOptionIds,
            request.selectedId,
        )
    except FeedbackValidationError as e:
        logger.warning(f"Feedback validation error for '{request.exerciseId}': {e}")
        return {"success": False, "data": None, "error": str(e)}

    # Record the graded attempt to the local SQLite store (FR-22/FR-28, AR-17).
    # Best-effort write-hook: a persistence failure must never alter or break
    # the feedback response, so it is logged and swallowed.
    try:
        store.record_attempt(
            exercise_id=exercise.id,
            exam=str(exercise.exam.value),
            domain=str(exercise.domain.value),
            correct=bool(result["correct"]),
            selected_id=request.selectedId,
            time_taken_ms=request.timeTakenMs,
        )
    except Exception as e:  # noqa: BLE001 - best-effort; grading must not break
        logger.warning(f"Failed to record attempt for '{request.exerciseId}': {e}")

    return {"success": True, "data": result, "error": None}


def _validate_exam(exam: str | None) -> str | None:
    """Validate the optional ``exam`` query param case-insensitively.

    Returns an error message string if invalid, else ``None`` (valid/absent).
    Mirrors the validation loop used by GET /api/exercises and /api/sessions.
    """
    if not exam:
        return None
    valid_values = [member.value for member in ExamType]
    if exam.strip().lower() not in [v.lower() for v in valid_values]:
        logger.warning(f"Invalid exam type filter attempted: {exam}")
        return f"Invalid exam type '{exam}'. Valid values are: {', '.join(valid_values)}"
    return None


@app.get("/api/stats")
def get_stats(
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
):
    """Aggregate stats over the recorded attempt history (FR-23, rev 4).

    Returns the standard ``{success, data, error}`` wrapper. On success,
    ``data`` has the shape::

        {
            "overall": {"attempts": int, "correct": int, "accuracy": float},
            "byDomain": {<domain>: {"attempts": int, "correct": int, "accuracy": float}},
            "trend": [{"date", "attempts", "correct", "accuracy"}, ...]  # per day
        }

    Query Parameters:
    - exam: Optional exam scope (associate, professional; case-insensitive).

    Empty history is a successful response with zeroed overall stats and empty
    ``byDomain`` / ``trend``, never an error. Leak-free: every value is an
    aggregate over recorded attempts -- no exercise content, options, or
    per-option ``correct`` flags are ever read or returned (FR-20).
    """
    error = _validate_exam(exam)
    if error:
        return {"success": False, "data": None, "error": error}

    # Normalize to the canonical (lowercase) stored value so a case-variant
    # query (?exam=Associate) matches rows instead of silently returning zeros.
    exam_filter = exam.strip().lower() if exam else None
    stats = store.overall_stats(exam=exam_filter)
    trend = store.daily_stats(exam=exam_filter)

    data = {
        "overall": {
            "attempts": stats["total"],
            "correct": stats["correct"],
            "accuracy": stats["accuracy"],
        },
        "byDomain": stats["by_domain"],
        "trend": trend,
    }
    return {"success": True, "data": data, "error": None}


@app.get("/api/readiness")
def get_readiness(
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
):
    """Rolling-window readiness vs the ~70% planning heuristic (FR-25, rev 4).

    Returns the standard ``{success, data, error}`` wrapper. On success,
    ``data`` has the shape::

        {
            "overall": {"accuracy": float, "ready": bool, "window": int},
            "byDomain": {<domain>: {"accuracy": float, "ready": bool}}
        }

    ``ready`` is ``rolling-window accuracy >= 0.70`` over the last
    ``store.READINESS_WINDOW`` attempts (per-domain readiness uses each domain's
    own rolling window). The ~70% bar is a *planning heuristic* surfaced as
    guidance, not an official cut (addendum §C); the window/threshold used are
    surfaced on the overall block (``window``) and at the top level
    (``threshold``, ``window``).

    Query Parameters:
    - exam: Optional exam scope (associate, professional; case-insensitive).

    Empty history -> overall accuracy 0.0, ready False, empty ``byDomain``;
    success, not an error. Leak-free: aggregates over attempts only (FR-20).
    """
    error = _validate_exam(exam)
    if error:
        return {"success": False, "data": None, "error": error}

    # Normalize to the canonical stored value (see GET /api/stats).
    exam_filter = exam.strip().lower() if exam else None
    result = store.readiness(exam=exam_filter)

    data = {
        "overall": {
            "accuracy": result["overall"]["accuracy"],
            "ready": result["overall"]["ready"],
            "window": result["overall"]["window"],
        },
        "byDomain": {
            domain: {"accuracy": block["accuracy"], "ready": block["ready"]}
            for domain, block in result["byDomain"].items()
        },
        "threshold": result["threshold"],
        "window": result["window"],
    }
    return {"success": True, "data": data, "error": None}


class ExerciseFeedbackRequest(BaseModel):
    """Request body for POST /api/exercise-feedback (Story 11.1, FR-32).

    A free-text learner note flagging a problem with an Exercise. Persisted to
    the sidecar ``exercises/feedback.yaml`` (never the authored Exercise file).
    """

    exerciseId: str = Field(..., description="Id of the exercise the note is about")
    note: str = Field(..., description="Free-text feedback note")


@app.post("/api/exercise-feedback")
def post_exercise_feedback(request: ExerciseFeedbackRequest):
    """Record a free-text feedback note for an exercise (FR-32).

    Appends to the sidecar feedback store (``feedback_store``); the authored
    Exercise YAML is never modified. Validates the exercise id exists and the
    note is non-empty. Distinct from the MCQ-grading ``POST /api/feedback``.
    """
    exercises = getattr(app.state, "exercises", [])
    if not any(e.id == request.exerciseId for e in exercises):
        return {
            "success": False,
            "data": None,
            "error": f"Exercise '{request.exerciseId}' not found",
        }
    try:
        entry = feedback_store.add_note(request.exerciseId, request.note)
    except ValueError as e:
        return {"success": False, "data": None, "error": str(e)}
    except feedback_store.FeedbackStoreError as e:
        # Corrupt sidecar — surface a clear failure instead of a 500.
        return {"success": False, "data": None, "error": str(e)}
    return {"success": True, "data": entry, "error": None}


@app.get("/api/exercise-feedback")
def get_exercise_feedback(
    exerciseId: str = Query(..., description="Exercise id to list feedback notes for"),
):
    """List the feedback notes recorded for an exercise (FR-32, read path)."""
    try:
        notes = feedback_store.notes_for(exerciseId)
    except feedback_store.FeedbackStoreError as e:
        return {"success": False, "data": None, "error": str(e)}
    return {"success": True, "data": {"notes": notes}, "error": None}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
