import pytest
from fastapi.testclient import TestClient

from app.content import load_exercises_from_directory


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
