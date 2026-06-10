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
        # A session may mix MCQ and Code-Completion entries (Story 4.1); the two
        # types have different shapes — assert per type.
        response = client.get("/api/sessions")
        data = response.json()["data"]
        mcq_keys = {
            "exerciseId",
            "type",
            "domain",
            "difficulty",
            "question",
            "codeContext",
            "displayedOptions",
        }
        cc_keys = {
            "exerciseId",
            "type",
            "domain",
            "difficulty",
            "language",
            "prompt",
            "template",
            "answer",
            "accepted",
            "caseSensitive",
            "ignoreWhitespace",
            "explanation",
            "references",
        }
        for entry in data:
            if entry["type"] == "code_completion":
                assert set(entry.keys()) == cc_keys
            else:
                assert set(entry.keys()) == mcq_keys

    def test_each_mcq_entry_has_exactly_four_displayed_options(self, client):
        # Scoped to MCQ entries — Code-Completion entries carry no displayedOptions.
        response = client.get("/api/sessions")
        data = response.json()["data"]
        mcq_entries = [e for e in data if e["type"] != "code_completion"]
        assert len(mcq_entries) > 0
        for entry in mcq_entries:
            options = entry["displayedOptions"]
            assert isinstance(options, list)
            assert len(options) == 4
            for option in options:
                assert set(option.keys()) == {"id", "text"}

    def test_code_completion_entry_has_no_displayed_options(self, client):
        # Code-Completion entries (Story 4.1) carry template/answer/accepted but
        # never an MCQ-style displayedOptions list.
        response = client.get("/api/sessions")
        data = response.json()["data"]
        for entry in data:
            if entry["type"] == "code_completion":
                assert "displayedOptions" not in entry
                assert entry["template"].count("___") == 1
                assert isinstance(entry["answer"], str) and entry["answer"]


class TestNoAnswerLeakage:
    """The correct flag must never be present anywhere in the payload."""

    def test_no_correct_key_in_displayed_options(self, client):
        # MCQ Displayed Options never carry the `correct` flag. Code-Completion
        # entries have no displayedOptions (their answer is delivered separately
        # for client-side feedback — a different, documented leakage model).
        response = client.get("/api/sessions")
        data = response.json()["data"]
        for entry in data:
            for option in entry.get("displayedOptions", []):
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

    def test_filter_by_exercise_type_code_completion(self, client):
        # Scoping a session to code_completion returns ONLY code-completion
        # entries (so the Wordle drill is reachable without hunting through
        # interleaved MCQs). Each entry routes by ``type`` on the client.
        response = client.get("/api/sessions?exam=associate&exercise_type=code_completion")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0
        for entry in data["data"]:
            assert entry["type"] == "code_completion"
            # Code-completion entries carry the template/answer, never displayedOptions.
            assert "displayedOptions" not in entry

    def test_filter_by_exercise_type_single_choice_excludes_code_completion(self, client):
        response = client.get("/api/sessions?exam=associate&exercise_type=single_choice")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0
        assert all(entry["type"] != "code_completion" for entry in data["data"])

    def test_exercise_type_is_case_insensitive(self, client):
        upper = client.get("/api/sessions?exam=associate&exercise_type=CODE_COMPLETION").json()
        assert upper["success"] is True
        assert len(upper["data"]) > 0
        for entry in upper["data"]:
            assert entry["type"] == "code_completion"

    def test_invalid_exercise_type_returns_error(self, client):
        response = client.get("/api/sessions?exercise_type=not_a_type")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert "Invalid exercise type" in data["error"]

    def test_multiple_exercise_types_include_both(self, client):
        # The Start-screen multiselect (Story 4.7) can request several types;
        # repeating the param includes any of them.
        both = client.get(
            "/api/sessions?exam=associate&exercise_type=single_choice&exercise_type=code_completion"
        ).json()
        assert both["success"] is True
        types = {e["type"] for e in both["data"]}
        assert "single_choice" in types
        assert "code_completion" in types

    def test_one_invalid_type_among_several_is_rejected(self, client):
        response = client.get("/api/sessions?exercise_type=single_choice&exercise_type=bogus")
        data = response.json()
        assert data["success"] is False
        assert "Invalid exercise type 'bogus'" in data["error"]


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
