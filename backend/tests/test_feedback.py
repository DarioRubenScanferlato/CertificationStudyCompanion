"""Tests for POST /api/feedback single-select scoring."""

import pytest

from app.feedback import (
    FeedbackValidationError,
    find_exercise,
    score_single_select,
)
from app.models import MCQ


def _make_mcq(exercise_id: str = "test-mcq-0001") -> MCQ:
    """Build a single-select MCQ with one correct option ('a') and 3 distractors."""
    return MCQ(
        id=exercise_id,
        type="single_choice",
        exam="associate",
        domain="Databricks Lakehouse Platform",
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
        domain="Databricks Lakehouse Platform",
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
