import pytest
from fastapi.testclient import TestClient

from app import feedback_store, store
from app.content import load_exercises_from_directory


@pytest.fixture(autouse=True)
def isolated_attempt_db(tmp_path, monkeypatch):
    """Point the SQLite attempt store at a throwaway per-test DB.

    Autouse so NO test (incl. feedback/session endpoints that record or read
    attempts) ever touches the real `backend/data/progress.db`. Each test gets
    a fresh, empty store — keeping unseen-first ordering deterministic.
    """
    monkeypatch.setenv("ATTEMPT_DB_PATH", str(tmp_path / "test_progress.db"))
    store.init_db()
    yield


@pytest.fixture(autouse=True)
def isolated_feedback_store(tmp_path, monkeypatch):
    """Point the sidecar feedback store at a throwaway per-test file (Story 11.1).

    Autouse so the `POST /api/exercise-feedback` endpoint never writes to the
    real `exercises/feedback.yaml` during tests.
    """
    fb = tmp_path / "feedback.yaml"
    monkeypatch.setattr(feedback_store, "_default_feedback_path", lambda: fb)
    yield


@pytest.fixture(scope="session", autouse=True)
def load_test_exercises():
    """Fixture that loads exercises once per test session."""
    from app.main import app

    exercises, error_count, error_log = load_exercises_from_directory()
    app.state.exercises = exercises
    app.state.error_log = error_log
    yield
    # Cleanup after all tests


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI app."""
    from app.main import app

    return TestClient(app)
