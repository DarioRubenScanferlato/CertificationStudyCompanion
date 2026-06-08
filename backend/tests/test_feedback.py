"""Tests for POST /api/feedback single-select scoring."""

import pytest

from app import store
from app.feedback import (
    FeedbackValidationError,
    find_exercise,
    score_single_select,
)
from app.models import MCQ


@pytest.fixture
def temp_attempt_db(tmp_path, monkeypatch):
    """Point the attempt store at a throwaway DB so tests don't touch the real db.

    Sets ATTEMPT_DB_PATH (honored by store._resolve_path) and initializes the
    schema, then yields the path so tests can assert on persisted rows.
    """
    db_path = tmp_path / "test_progress.db"
    monkeypatch.setenv("ATTEMPT_DB_PATH", str(db_path))
    store.init_db()
    yield db_path


def _make_mcq(exercise_id: str = "test-mcq-0001") -> MCQ:
    """Build a single-select MCQ with one correct option ('a') and 3 distractors."""
    return MCQ(
        id=exercise_id,
        type="single_choice",
        exam="associate",
        domain="Databricks Intelligence Platform",
        difficulty="easy",
        question="Which option is correct?",
        options=[
            {"id": "a", "text": "Correct one", "correct": True},
            {"id": "b", "text": "Wrong one", "correct": False},
            {"id": "c", "text": "Wrong two", "correct": False},
            {"id": "d", "text": "Wrong three", "correct": False},
        ],
        explanation="Option a is correct.",
        references=["https://docs.databricks.com/example"],
    )


def _make_mcq_5opt(exercise_id: str = "test-mcq-5opt") -> MCQ:
    """Build an MCQ with one correct option ('a') and four distractors (b-e)."""
    return MCQ(
        id=exercise_id,
        type="single_choice",
        exam="associate",
        domain="Databricks Intelligence Platform",
        difficulty="easy",
        question="Which option is correct?",
        options=[
            {"id": "a", "text": "Correct one", "correct": True},
            {"id": "b", "text": "Wrong one", "correct": False},
            {"id": "c", "text": "Wrong two", "correct": False},
            {"id": "d", "text": "Wrong three", "correct": False},
            {"id": "e", "text": "Wrong four", "correct": False},
        ],
        explanation="Option a is correct.",
        references=["https://docs.databricks.com/example"],
    )


class TestScoreSingleSelectPure:
    """Tests for the pure scoring function."""

    def test_correct_answer(self):
        mcq = _make_mcq()
        result = score_single_select(mcq, ["a", "b", "c", "d"], "a")
        assert result["correct"] is True
        assert result["correctOptionId"] == "a"
        assert result["explanation"] == "Option a is correct."
        assert result["references"] == ["https://docs.databricks.com/example"]

    def test_incorrect_answer(self):
        mcq = _make_mcq()
        result = score_single_select(mcq, ["a", "b", "c", "d"], "b")
        assert result["correct"] is False
        assert result["correctOptionId"] == "a"

    def test_unknown_displayed_id_raises(self):
        mcq = _make_mcq()
        with pytest.raises(FeedbackValidationError):
            score_single_select(mcq, ["a", "b", "c", "z"], "a")

    def test_no_correct_option_displayed_raises(self):
        # 5-option pool so a valid 4-length displayed set can exclude the
        # only correct option 'a'.
        mcq = _make_mcq_5opt()
        with pytest.raises(FeedbackValidationError):
            score_single_select(mcq, ["b", "c", "d", "e"], "b")

    def test_wrong_length_displayed_raises(self):
        mcq = _make_mcq()
        # The display contract is exactly 4 options.
        with pytest.raises(FeedbackValidationError):
            score_single_select(mcq, ["a", "b", "c"], "a")

    def test_duplicate_displayed_raises(self):
        mcq = _make_mcq()
        with pytest.raises(FeedbackValidationError):
            score_single_select(mcq, ["a", "b", "b", "c"], "a")

    def test_selected_not_displayed_raises(self):
        mcq = _make_mcq()
        with pytest.raises(FeedbackValidationError):
            score_single_select(mcq, ["a", "b", "c", "d"], "z")


class TestFeedbackEndpoint:
    """Tests for the POST /api/feedback endpoint."""

    def _first_mcq(self, client):
        """Return a loaded single_choice exercise dict from the API."""
        resp = client.get("/api/exercises?exercise_type=single_choice")
        data = resp.json()["data"]
        assert data, "Expected at least one single_choice exercise to be loaded"
        return data[0]

    def _displayed_ids(self, exercise):
        """Build a valid displayed set: the correct option + 3 distractors."""
        correct = [o["id"] for o in exercise["options"] if o["correct"]]
        incorrect = [o["id"] for o in exercise["options"] if not o["correct"]]
        return [correct[0], *incorrect[:3]], correct[0]

    def test_correct_answer(self, client):
        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": correct_id,
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["correct"] is True
        assert body["data"]["correctOptionId"] == correct_id
        assert body["data"]["explanation"]

    def test_incorrect_answer(self, client):
        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)
        wrong_id = next(oid for oid in displayed if oid != correct_id)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": wrong_id,
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["correct"] is False
        assert body["data"]["correctOptionId"] == correct_id

    def test_unknown_exercise(self, client):
        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": "does-not-exist-9999",
                "displayedOptionIds": ["a", "b", "c", "d"],
                "selectedId": "a",
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert "not found" in body["error"].lower()

    def test_malformed_displayed_wrong_length(self, client):
        exercise = self._first_mcq(client)
        incorrect = [o["id"] for o in exercise["options"] if not o["correct"]]
        # Only 3 ids -> violates the exactly-4 display contract.
        displayed = incorrect[:3]

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": displayed[0],
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert "exactly 4" in body["error"]

    def test_records_attempt_on_feedback(self, client, temp_attempt_db, monkeypatch):
        """A graded answer persists an attempt row (correct flag + id + time)."""
        captured = {}

        real_record = store.record_attempt

        def spy(*args, **kwargs):
            captured.update(kwargs)
            return real_record(*args, **kwargs)

        # Patch the name as referenced by the endpoint (app.main.store).
        import app.main as main_mod

        monkeypatch.setattr(main_mod.store, "record_attempt", spy)

        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": correct_id,
                "type": "mcq",
                "timeTakenMs": 4321,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # The endpoint forwarded the correct args to the store.
        assert captured["exercise_id"] == exercise["id"]
        assert captured["correct"] is True
        assert captured["selected_id"] == correct_id
        assert captured["time_taken_ms"] == 4321

        # And a row actually landed in the temp DB.
        stats = store.overall_stats()
        assert stats["total"] == 1
        assert stats["correct"] == 1
        assert exercise["id"] in store.attempted_ids()

    def test_incorrect_attempt_recorded(self, client, temp_attempt_db):
        """An incorrect graded answer is recorded with correct=0."""
        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)
        wrong_id = next(oid for oid in displayed if oid != correct_id)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": wrong_id,
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["correct"] is False

        stats = store.overall_stats()
        assert stats["total"] == 1
        assert stats["correct"] == 0

    def test_no_attempt_recorded_on_validation_error(self, client, temp_attempt_db):
        """Validation-error paths must not write an attempt row."""
        exercise = self._first_mcq(client)
        incorrect = [o["id"] for o in exercise["options"] if not o["correct"]]
        displayed = incorrect[:3]  # wrong length -> validation error

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": displayed[0],
                "type": "mcq",
            },
        )
        assert resp.json()["success"] is False
        assert store.overall_stats()["total"] == 0

    def test_store_failure_does_not_break_feedback(self, client, temp_attempt_db, monkeypatch):
        """A store-write failure is swallowed; feedback response is unchanged."""
        import app.main as main_mod

        def boom(*args, **kwargs):
            raise RuntimeError("simulated store failure")

        monkeypatch.setattr(main_mod.store, "record_attempt", boom)

        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": correct_id,
                "type": "mcq",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["correct"] is True
        assert body["data"]["correctOptionId"] == correct_id

    def test_unsupported_type(self, client):
        exercise = self._first_mcq(client)
        displayed, correct_id = self._displayed_ids(exercise)

        resp = client.post(
            "/api/feedback",
            json={
                "exerciseId": exercise["id"],
                "displayedOptionIds": displayed,
                "selectedId": correct_id,
                "type": "code_completion",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert "Unsupported feedback type" in body["error"]


class TestFindExercise:
    """Tests for the find_exercise helper."""

    def test_found(self):
        mcq = _make_mcq("findme-1")
        assert find_exercise([mcq], "findme-1") is mcq

    def test_not_found(self):
        mcq = _make_mcq("findme-1")
        assert find_exercise([mcq], "nope") is None
