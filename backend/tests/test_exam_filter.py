"""Tests for the `exam` filter & session scoping (Story 6.7).

The corpus now contains both Associate and Professional exercises. A practice
session must NEVER mix the two. These tests assert that:

* ``GET /api/sessions``, ``GET /api/exercises/count`` and ``POST /api/sessions``
  accept an ``exam`` param and filter by it,
* ``exam=associate`` yields only Associate exercises and ``exam=professional``
  yields only Professional exercises,
* omitting ``exam`` on the GET endpoints applies the documented default
  (associate -- never a mixed corpus),
* an invalid ``exam`` is a ``success: false`` error, and
* the count endpoint stays leak-free (only ``{count}``).

Counts are asserted relationally (all returned exercises carry the expected
exam; per-exam totals partition the corpus) rather than hard-coding 72/60, so
the suite tolerates corpus growth.
"""


def _iter_keys(obj):
    """Recursively yield every dict key in a JSON payload."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_keys(item)


def _exam_of(client, exercise_id):
    """Look up the authored ``exam`` of an exercise via GET /api/exercises."""
    data = client.get("/api/exercises").json()["data"]
    for ex in data:
        if ex["id"] == exercise_id:
            return ex["exam"]
    return None


class TestSessionsExamFilter:
    """GET /api/sessions scopes by exam and never mixes corpora."""

    def test_associate_returns_only_associate(self, client):
        data = client.get("/api/sessions?exam=associate").json()
        assert data["success"] is True
        ids = [entry["exerciseId"] for entry in data["data"]]
        assert len(ids) > 0
        for exercise_id in ids:
            assert _exam_of(client, exercise_id) == "associate"

    def test_professional_returns_only_professional(self, client):
        data = client.get("/api/sessions?exam=professional").json()
        assert data["success"] is True
        ids = [entry["exerciseId"] for entry in data["data"]]
        assert len(ids) > 0
        for exercise_id in ids:
            assert _exam_of(client, exercise_id) == "professional"

    def test_exam_is_case_insensitive(self, client):
        upper = client.get("/api/sessions?exam=ASSOCIATE").json()["data"]
        lower = client.get("/api/sessions?exam=associate").json()["data"]
        assert sorted(e["exerciseId"] for e in upper) == sorted(e["exerciseId"] for e in lower)

    def test_omitting_exam_defaults_to_associate(self, client):
        """No exam param must behave as associate-only, never mixed."""
        default = client.get("/api/sessions").json()["data"]
        associate = client.get("/api/sessions?exam=associate").json()["data"]
        assert sorted(e["exerciseId"] for e in default) == sorted(
            e["exerciseId"] for e in associate
        )
        # And the default population is strictly smaller than the whole corpus
        # would be, i.e. it does not silently include Professional exercises.
        professional = client.get("/api/sessions?exam=professional").json()["data"]
        default_ids = {e["exerciseId"] for e in default}
        professional_ids = {e["exerciseId"] for e in professional}
        assert default_ids.isdisjoint(professional_ids)

    def test_associate_and_professional_are_disjoint(self, client):
        associate = {
            e["exerciseId"] for e in client.get("/api/sessions?exam=associate").json()["data"]
        }
        professional = {
            e["exerciseId"] for e in client.get("/api/sessions?exam=professional").json()["data"]
        }
        assert associate.isdisjoint(professional)

    def test_invalid_exam_returns_error(self, client):
        response = client.get("/api/sessions?exam=expert")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert "Invalid exam type" in data["error"]

    def test_no_correct_key_leaked_with_exam_filter(self, client):
        payload = client.get("/api/sessions?exam=professional").json()
        assert "correct" not in set(_iter_keys(payload["data"]))


class TestCountExamFilter:
    """GET /api/exercises/count scopes by exam and stays leak-free."""

    def test_associate_count_matches_session_population(self, client):
        count = client.get("/api/exercises/count?exam=associate").json()["data"]["count"]
        session = client.get("/api/sessions?exam=associate").json()["data"]
        # The session builder may drop non-MCQ types, so count >= session size.
        assert count >= len(session)
        assert count > 0

    def test_professional_count_is_nonzero(self, client):
        count = client.get("/api/exercises/count?exam=professional").json()["data"]["count"]
        assert count > 0

    def test_per_exam_counts_partition_full_corpus(self, client):
        from app.main import app

        associate = client.get("/api/exercises/count?exam=associate").json()["data"]["count"]
        professional = client.get("/api/exercises/count?exam=professional").json()["data"]["count"]
        # Every exercise belongs to exactly one exam, so the two counts
        # partition the whole corpus.
        assert associate + professional == len(app.state.exercises)

    def test_omitting_exam_defaults_to_associate(self, client):
        default = client.get("/api/exercises/count").json()["data"]["count"]
        associate = client.get("/api/exercises/count?exam=associate").json()["data"]["count"]
        assert default == associate

    def test_invalid_exam_returns_error(self, client):
        response = client.get("/api/exercises/count?exam=expert")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert "Invalid exam type" in data["error"]

    def test_count_payload_is_count_only_with_exam(self, client):
        keys = set(_iter_keys(client.get("/api/exercises/count?exam=associate").json()))
        assert keys == {"success", "data", "error", "count"}
        leaky = {"correct", "options", "pool", "displayedOptions", "explanation", "references"}
        assert keys & leaky == set()


class TestPostSessionExamScope:
    """POST /api/sessions scopes a replay to a single exam when asked."""

    def _ids_for(self, client, exam):
        return [e["exerciseId"] for e in client.get(f"/api/sessions?exam={exam}").json()["data"]]

    def test_exam_scope_drops_other_exam_ids(self, client):
        associate_ids = self._ids_for(client, "associate")
        professional_ids = self._ids_for(client, "professional")
        mixed = associate_ids[:2] + professional_ids[:2]

        data = client.post(
            "/api/sessions",
            json={"exerciseIds": mixed, "exam": "associate"},
        ).json()
        assert data["success"] is True
        returned = {entry["exerciseId"] for entry in data["data"]}
        # Only the Associate ids survive the exam scope.
        assert returned.issubset(set(associate_ids[:2]))
        assert returned.isdisjoint(set(professional_ids))

    def test_no_exam_replays_exactly_the_requested_ids(self, client):
        """Without an exam scope the replay is the matched id set as-is."""
        professional_ids = self._ids_for(client, "professional")[:3]
        data = client.post(
            "/api/sessions",
            json={"exerciseIds": professional_ids},
        ).json()
        assert data["success"] is True
        returned = {entry["exerciseId"] for entry in data["data"]}
        assert returned == set(professional_ids)

    def test_invalid_exam_returns_error(self, client):
        response = client.post(
            "/api/sessions",
            json={"exerciseIds": [], "exam": "expert"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert "Invalid exam type" in data["error"]
