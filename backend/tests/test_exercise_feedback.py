"""Tests for the POST/GET /api/exercise-feedback endpoint (Story 11.1, FR-32)."""


def _a_real_exercise_id(client):
    """Grab a real loaded exercise id (any type) from the admin listing."""
    data = client.get("/api/exercises").json()["data"]
    assert data, "expected loaded exercises"
    return data[0]["id"]


class TestPostExerciseFeedback:
    def test_records_a_note_and_returns_entry(self, client):
        ex_id = _a_real_exercise_id(client)
        resp = client.post(
            "/api/exercise-feedback",
            json={"exerciseId": ex_id, "note": "The explanation looks outdated."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["note"] == "The explanation looks outdated."
        assert body["data"]["resolved"] is False
        assert body["data"]["created_at"].endswith("Z")

    def test_note_is_retrievable_after_submit(self, client):
        ex_id = _a_real_exercise_id(client)
        client.post("/api/exercise-feedback", json={"exerciseId": ex_id, "note": "first"})
        client.post("/api/exercise-feedback", json={"exerciseId": ex_id, "note": "second"})
        got = client.get("/api/exercise-feedback", params={"exerciseId": ex_id}).json()
        assert got["success"] is True
        notes = [n["note"] for n in got["data"]["notes"]]
        assert notes == ["first", "second"]

    def test_unknown_exercise_id_is_rejected(self, client):
        resp = client.post(
            "/api/exercise-feedback",
            json={"exerciseId": "does-not-exist", "note": "hi"},
        )
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert "not found" in body["error"].lower()

    def test_empty_note_is_rejected(self, client):
        ex_id = _a_real_exercise_id(client)
        resp = client.post(
            "/api/exercise-feedback",
            json={"exerciseId": ex_id, "note": "   "},
        )
        body = resp.json()
        assert body["success"] is False
        assert "empty" in body["error"].lower()
        # And nothing was recorded for that exercise.
        got = client.get("/api/exercise-feedback", params={"exerciseId": ex_id}).json()
        assert got["data"]["notes"] == []

    def test_get_for_exercise_with_no_feedback_is_empty(self, client):
        ex_id = _a_real_exercise_id(client)
        got = client.get("/api/exercise-feedback", params={"exerciseId": ex_id}).json()
        assert got["success"] is True
        assert got["data"]["notes"] == []

    def test_corrupt_sidecar_returns_friendly_error_not_500(self, client, tmp_path):
        # The autouse isolated_feedback_store fixture points the store at
        # tmp_path/feedback.yaml; corrupt it and confirm neither endpoint 500s.
        (tmp_path / "feedback.yaml").write_text("{ not: valid: yaml: [")
        ex_id = _a_real_exercise_id(client)

        post = client.post("/api/exercise-feedback", json={"exerciseId": ex_id, "note": "hi"})
        assert post.status_code == 200
        assert post.json()["success"] is False
        assert "yaml" in post.json()["error"].lower()

        get = client.get("/api/exercise-feedback", params={"exerciseId": ex_id})
        assert get.status_code == 200
        assert get.json()["success"] is False
