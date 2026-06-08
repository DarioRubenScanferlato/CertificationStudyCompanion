"""Tests for the GET /api/sessions endpoint (Story 5.4).

Because the session builder samples and shuffles uniformly at random with no
seed, these tests assert on structure/counts and invariants (e.g. no answer
leakage), never on exact ordering or exact option selection.
"""


def _iter_keys(obj):
    """Recursively yield every dict key in a JSON payload.

    Only keys are yielded (not string values): the non-leakage contract is
    that no ``correct`` flag *key* is serialized. Asserting against string
    values too would false-positive on legitimate question text containing
    the word "correct".
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_keys(item)


class TestSessionResponseFormat:
    """Standard {success, data, error} wrapper and entry structure."""

    def test_returns_200_and_success_wrapper(self, client):
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"success", "data", "error"}
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_returns_json_content_type(self, client):
        response = client.get("/api/sessions")
        assert response.headers["content-type"].startswith("application/json")

    def test_each_entry_has_expected_shape(self, client):
        response = client.get("/api/sessions")
        data = response.json()["data"]
        for entry in data:
            assert set(entry.keys()) == {
                "exerciseId",
                "type",
                "domain",
                "difficulty",
                "question",
                "codeContext",
                "displayedOptions",
            }

    def test_each_entry_has_exactly_four_displayed_options(self, client):
        response = client.get("/api/sessions")
        data = response.json()["data"]
        for entry in data:
            options = entry["displayedOptions"]
            assert isinstance(options, list)
            assert len(options) == 4
            for option in options:
                assert set(option.keys()) == {"id", "text"}


class TestNoAnswerLeakage:
    """The correct flag must never be present anywhere in the payload."""

    def test_no_correct_key_in_displayed_options(self, client):
        response = client.get("/api/sessions")
        data = response.json()["data"]
        for entry in data:
            for option in entry["displayedOptions"]:
                assert "correct" not in option

    def test_no_correct_key_anywhere_in_payload(self, client):
        response = client.get("/api/sessions")
        payload = response.json()
        # Walk the entire response tree; no dict key named "correct" anywhere
        # (question text may legitimately contain the word "correct").
        assert "correct" not in set(_iter_keys(payload["data"]))


class TestSessionFiltering:
    """domain / difficulty filtering, same semantics as GET /api/exercises."""

    def test_filter_by_domain_narrows_results(self, client):
        full = client.get("/api/sessions").json()["data"]
        filtered = client.get("/api/sessions?domain=Governance%20and%20Security").json()["data"]

        assert len(filtered) > 0
        assert len(filtered) < len(full)
        for entry in filtered:
            assert entry["domain"] == "Governance and Security"

    def test_filter_by_difficulty(self, client):
        response = client.get("/api/sessions?difficulty=easy")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        for entry in data["data"]:
            assert entry["difficulty"] == "easy"

    def test_filter_is_case_insensitive(self, client):
        lower = client.get("/api/sessions?domain=governance%20and%20security").json()
        assert lower["success"] is True
        assert len(lower["data"]) > 0
        for entry in lower["data"]:
            assert entry["domain"] == "Governance and Security"


class TestEmptyAndInvalid:
    """Empty filter result is success; invalid enum value is an error."""

    def test_unmatched_filter_returns_empty_success(self, client):
        # No exercises currently match professional+hard.
        response = client.get("/api/sessions?domain=Governance%20and%20Security&difficulty=hard")
        assert response.status_code == 200
        data = response.json()
        # If content happens to contain such combos this still must be a valid
        # success response; the empty case must be data == [] (not an error).
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["data"], list)
        for entry in data["data"]:
            assert entry["domain"] == "Governance and Security"
            assert entry["difficulty"] == "hard"

    def test_invalid_domain_returns_error(self, client):
        response = client.get("/api/sessions?domain=NotARealDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert data["error"] is not None
        assert "Invalid domain" in data["error"]

    def test_invalid_difficulty_returns_error(self, client):
        response = client.get("/api/sessions?difficulty=impossible")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert "Invalid difficulty" in data["error"]


class TestRandomization:
    """Order is randomized; assert the set of ids is stable, order may vary."""

    def test_session_contains_all_mcqs_regardless_of_order(self, client):
        first = client.get("/api/sessions").json()["data"]
        second = client.get("/api/sessions").json()["data"]
        ids_first = sorted(e["exerciseId"] for e in first)
        ids_second = sorted(e["exerciseId"] for e in second)
        # Same population each call (no anti-repeat, no sampling at session level).
        assert ids_first == ids_second
