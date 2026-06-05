import logging
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.anki import export_to_anki
from app.content import filter_exercises, load_exercises_from_directory
from app.models import MCQ, Difficulty, Domain, ExamType, ExerciseType

# Configure logging
logger = logging.getLogger(__name__)


# Startup event to load exercises
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load exercises on startup."""
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


@app.get("/api/exercises")
def get_exercises(
    domain: str = Query(None, description="Filter by domain (one of the 5 Associate domains)"),
    difficulty: str = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    exam: str = Query(None, description="Filter by exam (associate, professional)"),
    exercise_type: str = Query(
        None, description="Filter by type (single_choice, multi_choice, code_completion)"
    ),
):
    """
    Get exercises with optional filtering.

    Query Parameters:
    - domain: Filter by one of the 5 Associate domains (case-insensitive)
      Valid values: "Databricks Lakehouse Platform", "ELT with Spark SQL and Python",
      "Incremental Data Processing", "Production Pipelines", "Data Governance"
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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
