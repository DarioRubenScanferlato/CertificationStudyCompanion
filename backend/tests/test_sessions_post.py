"""Tests for the POST /api/sessions endpoint (Story 6.2 — replay by ids).

POST /api/sessions builds a *fresh* session over an explicit set of exercise
ids, reusing the same Story 5.3 randomizer as GET /api/sessions. Because that
randomizer samples and shuffles uniformly at random with no seed, these tests
assert on structure/counts and invariants (no answer leakage, freshness across
calls), never on exact ordering or exact option selection.
"""


def _iter_keys(obj):
    """Recursively yield every dict key in a JSON payload.

    Only keys are yielded (not string values): the non-leakage contract is that
    no ``correct`` flag *key* is serialized. Asserting against string values too
    would false-positive on question text containing the word "correct".
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_keys(item)


def _all_mcq_ids(client):
    """Return the ids of all MCQs the session builder would emit (full corpus).

    A session may now also contain Code-Completion entries (Story 4.1), which
    have a different shape (no displayedOptions). These tests cover MCQ replay
    shape/freshness, so filter to MCQ entries only.
    """
    data = client.get("/api/sessions").json()["data"]
    return [entry["exerciseId"] for entry in data if entry["type"] != "code_completion"]


class TestKnownIdSet:
    """POSTing a subset of real loaded ids returns exactly those MCQs."""

    def test_returns_200_and_success_wrapper(self, client):
        ids = _all_mcq_ids(client)
        response = client.post("/api/sessions", json={"exerciseIds": ids[:3]})
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"success", "data", "error"}
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["data"], list)

    def test_returns_requested_mcqs(self, client):
        ids = _all_mcq_ids(client)
        requested = ids[:3]
        data = client.post("/api/sessions", json={"exerciseIds": requested}).json()["data"]
        returned_ids = {entry["exerciseId"] for entry in data}
        # Each returned exerciseId must be one of the requested ids.
        assert returned_ids.issubset(set(requested))
        # All requested ids are MCQs (drawn from the session corpus), so the
        # match count equals the number requested.
        assert len(data) == len(requested)

    def test_each_entry_has_expected_shape(self, client):
        ids = _all_mcq_ids(client)
        data = client.post("/api/sessions", json={"exerciseIds": ids[:3]}).json()["data"]
        for entry in data:
            assert set(entry.keys()) == {
                "exerciseId",
                "type",
                "domain",
                "difficulty",
                "question",
                "codeContext",
                "displayedOptions",
                "seen",
            }

    def test_seen_flag_present_and_reflects_history(self, client):
        # Story 7.6: replayed entries carry `seen`. Replay is the common
        # already-seen case, so this is the path the indicator most relies on.
        from app import store

        ids = _all_mcq_ids(client)
        requested = ids[:3]
        store.record_attempt(requested[0], exam="associate")

        data = client.post("/api/sessions", json={"exerciseIds": requested}).json()["data"]
        seen_by_id = {e["exerciseId"]: e["seen"] for e in data}
        assert seen_by_id[requested[0]] is True
        assert seen_by_id[requested[1]] is False
        assert seen_by_id[requested[2]] is False

    def test_each_entry_has_exactly_four_displayed_options(self, client):
        ids = _all_mcq_ids(client)
        data = client.post("/api/sessions", json={"exerciseIds": ids[:3]}).json()["data"]
        for entry in data:
            options = entry["displayedOptions"]
            assert isinstance(options, list)
            assert len(options) == 4
            for option in options:
                assert set(option.keys()) == {"id", "text"}


class TestNoAnswerLeakage:
    """The correct flag must never be present anywhere in the payload (FR-20)."""

    def test_no_correct_key_in_displayed_options(self, client):
        ids = _all_mcq_ids(client)
        data = client.post("/api/sessions", json={"exerciseIds": ids[:3]}).json()["data"]
        for entry in data:
            for option in entry["displayedOptions"]:
                assert "correct" not in option

    def test_no_correct_key_anywhere_in_payload(self, client):
        ids = _all_mcq_ids(client)
        payload = client.post("/api/sessions", json={"exerciseIds": ids[:3]}).json()
        assert "correct" not in set(_iter_keys(payload["data"]))


class TestFreshnessAcrossCalls:
    """Replays re-sample options and re-randomize order (FR-20/21)."""

    def test_repeated_calls_are_not_always_identical(self, client):
        ids = _all_mcq_ids(client)
        requested = ids[:5]

        # Snapshot the displayed-option signature (ordered ids per exercise) plus
        # the session order across several calls. Assert *not always identical*
        # rather than *always different* to avoid flakiness, matching the
        # Story 5.3 freshness test approach.
        signatures = set()
        for _ in range(12):
            data = client.post("/api/sessions", json={"exerciseIds": requested}).json()["data"]
            order = tuple(entry["exerciseId"] for entry in data)
            options = tuple(
                (entry["exerciseId"], tuple(o["id"] for o in entry["displayedOptions"]))
                for entry in data
            )
            signatures.add((order, options))

        assert len(signatures) > 1, "expected option/order to vary across replays"


class TestUnknownIdHandling:
    """Unknown ids are dropped (logged), not fatal."""

    def test_mix_of_valid_and_bogus_ids(self, client):
        ids = _all_mcq_ids(client)
        valid = ids[:2]
        response = client.post(
            "/api/sessions",
            json={"exerciseIds": valid + ["bogus-id-1", "does-not-exist-9999"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        returned_ids = {entry["exerciseId"] for entry in data["data"]}
        # Only the matched exercises appear; bogus ids are absent.
        assert returned_ids == set(valid)
        assert "bogus-id-1" not in returned_ids
        assert "does-not-exist-9999" not in returned_ids

    def test_all_unknown_ids_returns_empty_success(self, client):
        response = client.post(
            "/api/sessions",
            json={"exerciseIds": ["nope-1", "nope-2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        assert data["data"] == []


class TestEmptyInput:
    """Empty exerciseIds is a successful empty list, not an error."""

    def test_empty_ids_returns_empty_success(self, client):
        response = client.post("/api/sessions", json={"exerciseIds": []})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        assert data["data"] == []


class TestShapeParityWithGet:
    """POST data entry shape matches GET /api/sessions exactly."""

    def test_post_entry_shape_matches_get(self, client):
        ids = _all_mcq_ids(client)
        get_entry = client.get("/api/sessions").json()["data"][0]
        post_data = client.post("/api/sessions", json={"exerciseIds": ids[:1]}).json()["data"]
        assert len(post_data) == 1
        assert set(post_data[0].keys()) == set(get_entry.keys())
