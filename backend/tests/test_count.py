"""Tests for the GET /api/exercises/count endpoint (Story 6.1).

The endpoint returns a lightweight, leak-free match count for the Start-screen
preview. These tests assert the {success, data, error} wrapper, the {count}
shape, filter semantics consistent with filter_exercises, and that NO exercise
fields (options/pools/correct flags) are ever serialized.
"""


def _iter_keys(obj):
    """Recursively yield every dict key in a JSON payload.

    Only keys are yielded (not string values): the non-leakage contract is
    that no leaky *key* is serialized, while count payloads have no values
    that could false-positive anyway.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_keys(item)


class TestCountResponseFormat:
    """Standard {success, data, error} wrapper with a {count} data payload."""

    def test_returns_200_and_success_wrapper(self, client):
        response = client.get("/api/exercises/count")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"success", "data", "error"}
        assert data["success"] is True
        assert data["error"] is None

    def test_data_is_count_only(self, client):
        response = client.get("/api/exercises/count")
        data = response.json()["data"]
        assert set(data.keys()) == {"count"}
        assert isinstance(data["count"], int)
        assert data["count"] > 0

    def test_returns_json_content_type(self, client):
        response = client.get("/api/exercises/count")
        assert response.headers["content-type"].startswith("application/json")


class TestNoAnswerLeakage:
    """The payload must contain only the count -- no exercise fields at all."""

    def test_no_leaky_keys_anywhere_in_payload(self, client):
        response = client.get("/api/exercises/count")
        keys = set(_iter_keys(response.json()))
        leaky = {"correct", "options", "pool", "displayedOptions", "explanation", "references"}
        assert keys & leaky == set()

    def test_only_wrapper_and_count_keys_present(self, client):
        response = client.get("/api/exercises/count")
        keys = set(_iter_keys(response.json()))
        assert keys == {"success", "data", "error", "count"}


class TestCountFiltering:
    """Counts mirror filter_exercises: domain narrows, +difficulty narrows.

    Note: as of Story 6.7 the no-``exam`` count is NOT the full corpus -- the
    default-exam policy scopes an unspecified request to Associate so the
    preview never reflects a mixed Associate+Professional corpus.
    """

    def test_no_filter_equals_associate_corpus(self, client):
        """No exam param defaults to associate (Story 6.7), not the full corpus."""
        default = client.get("/api/exercises/count").json()["data"]["count"]
        associate = client.get("/api/exercises/count?exam=associate").json()["data"]["count"]
        assert default == associate

    def test_domain_filter_narrows(self, client):
        full = client.get("/api/exercises/count").json()["data"]["count"]
        narrowed = client.get("/api/exercises/count?domain=Governance%20and%20Security").json()[
            "data"
        ]["count"]
        assert 0 < narrowed < full

    def test_domain_plus_difficulty_narrows_further(self, client):
        domain_only = client.get("/api/exercises/count?domain=Governance%20and%20Security").json()[
            "data"
        ]["count"]
        both = client.get(
            "/api/exercises/count?domain=Governance%20and%20Security&difficulty=easy"
        ).json()["data"]["count"]
        assert both <= domain_only

    def test_filter_is_case_insensitive(self, client):
        upper = client.get("/api/exercises/count?domain=Governance%20and%20Security").json()[
            "data"
        ]["count"]
        lower = client.get("/api/exercises/count?domain=governance%20and%20security").json()[
            "data"
        ]["count"]
        assert upper == lower

    def test_count_matches_sessions_population(self, client):
        """Count for a domain equals the session population for that domain."""
        count = client.get("/api/exercises/count?domain=Governance%20and%20Security").json()[
            "data"
        ]["count"]
        session = client.get("/api/sessions?domain=Governance%20and%20Security").json()["data"]
        assert count == len(session)

    def test_count_by_exercise_type_matches_sessions_population(self, client):
        """Count scoped to a type equals the type-scoped session population.

        Keeps the Start-screen preview honest for the new Exercise-type filter:
        the "{n} questions match" count must agree with what the session yields.
        """
        count = client.get(
            "/api/exercises/count?exam=associate&exercise_type=code_completion"
        ).json()["data"]["count"]
        session = client.get("/api/sessions?exam=associate&exercise_type=code_completion").json()[
            "data"
        ]
        assert count == len(session)
        assert count > 0


class TestInvalidFilters:
    """Invalid enum values are errors with data == null, like GET /api/sessions."""

    def test_invalid_domain_returns_error(self, client):
        response = client.get("/api/exercises/count?domain=NotARealDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert "Invalid domain" in data["error"]

    def test_invalid_difficulty_returns_error(self, client):
        response = client.get("/api/exercises/count?difficulty=impossible")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert "Invalid difficulty" in data["error"]

    def test_invalid_exercise_type_returns_error(self, client):
        response = client.get("/api/exercises/count?exercise_type=not_a_type")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert "Invalid exercise type" in data["error"]
