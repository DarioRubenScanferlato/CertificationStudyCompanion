"""Tests for GET /api/stats and GET /api/readiness (Story 7.4, FR-23/FR-25).

Attempts are seeded via ``store.record_attempt(...)``; the autouse
``isolated_attempt_db`` fixture (conftest.py) points the store at a fresh temp
DB per test, so each test starts from an empty history.
"""

import pytest

from app import store

# --- helpers ----------------------------------------------------------------


def _seed(exercise_id, correct, *, exam=None, domain=None, answered_at=None):
    store.record_attempt(
        exercise_id=exercise_id,
        exam=exam,
        domain=domain,
        correct=correct,
        answered_at=answered_at,
    )


# --- GET /api/stats ---------------------------------------------------------


def test_stats_overall_and_per_domain_math(client):
    # 4 attempts, 3 correct -> 0.75 overall.
    _seed("ex-1", True, domain="ELT")
    _seed("ex-2", False, domain="ELT")
    _seed("ex-3", True, domain="Governance")
    _seed("ex-4", True, domain="Governance")

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["error"] is None

    overall = body["data"]["overall"]
    assert overall["attempts"] == 4
    assert overall["correct"] == 3
    assert overall["accuracy"] == pytest.approx(0.75)

    by_domain = body["data"]["byDomain"]
    assert by_domain["ELT"] == {
        "attempts": 2,
        "correct": 1,
        "accuracy": pytest.approx(0.5),
    }
    assert by_domain["Governance"] == {
        "attempts": 2,
        "correct": 2,
        "accuracy": pytest.approx(1.0),
    }


def test_stats_trend_present_and_grouped_by_day(client):
    _seed("ex-1", True, answered_at="2026-06-05T10:00:00+00:00")
    _seed("ex-2", False, answered_at="2026-06-05T11:00:00+00:00")
    _seed("ex-3", True, answered_at="2026-06-06T09:00:00+00:00")

    body = client.get("/api/stats").json()
    trend = body["data"]["trend"]

    assert isinstance(trend, list)
    # Two distinct days, oldest first.
    assert [d["date"] for d in trend] == ["2026-06-05", "2026-06-06"]
    assert trend[0] == {
        "date": "2026-06-05",
        "attempts": 2,
        "correct": 1,
        "accuracy": pytest.approx(0.5),
    }
    assert trend[1] == {
        "date": "2026-06-06",
        "attempts": 1,
        "correct": 1,
        "accuracy": pytest.approx(1.0),
    }


def test_stats_exam_filter_narrows(client):
    _seed("ex-a", True, exam="associate", domain="ELT")
    _seed("ex-b", False, exam="associate", domain="ELT")
    _seed("ex-c", True, exam="professional", domain="ELT")

    body = client.get("/api/stats", params={"exam": "associate"}).json()
    assert body["success"] is True
    overall = body["data"]["overall"]
    assert overall["attempts"] == 2
    assert overall["correct"] == 1
    assert overall["accuracy"] == pytest.approx(0.5)
    assert set(body["data"]["byDomain"]) == {"ELT"}
    assert body["data"]["byDomain"]["ELT"]["attempts"] == 2


def test_stats_empty_history_is_zeros_and_success(client):
    body = client.get("/api/stats").json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["overall"] == {"attempts": 0, "correct": 0, "accuracy": 0.0}
    assert body["data"]["byDomain"] == {}
    assert body["data"]["trend"] == []


def test_stats_invalid_exam_is_error(client):
    resp = client.get("/api/stats", params={"exam": "expert"})
    body = resp.json()
    assert body["success"] is False
    assert body["data"] is None
    assert "Invalid exam type" in body["error"]


def test_stats_is_leak_free(client):
    """The stats payload exposes only aggregates -- never content/flags."""
    _seed("ex-1", True, domain="ELT")
    body = client.get("/api/stats").json()
    # Only the documented keys are present.
    assert set(body["data"]) == {"overall", "byDomain", "trend"}
    assert set(body["data"]["overall"]) == {"attempts", "correct", "accuracy"}
    for block in body["data"]["byDomain"].values():
        assert set(block) == {"attempts", "correct", "accuracy"}


# --- GET /api/readiness -----------------------------------------------------


def test_readiness_overall_ready_above_threshold(client):
    # 8/10 correct -> 0.8 >= 0.70 -> ready.
    for i in range(8):
        _seed(f"ex-c{i}", True, domain="ELT")
    for i in range(2):
        _seed(f"ex-w{i}", False, domain="ELT")

    body = client.get("/api/readiness").json()
    assert body["success"] is True
    overall = body["data"]["overall"]
    assert overall["accuracy"] == pytest.approx(0.8)
    assert overall["ready"] is True
    assert overall["window"] == store.READINESS_WINDOW


def test_readiness_overall_not_ready_below_threshold(client):
    # 5/10 correct -> 0.5 < 0.70 -> not ready.
    for i in range(5):
        _seed(f"ex-c{i}", True, domain="ELT")
    for i in range(5):
        _seed(f"ex-w{i}", False, domain="ELT")

    body = client.get("/api/readiness").json()
    overall = body["data"]["overall"]
    assert overall["accuracy"] == pytest.approx(0.5)
    assert overall["ready"] is False


def test_readiness_per_domain(client):
    # ELT strong (3/3), Governance weak (1/3).
    for i in range(3):
        _seed(f"elt-{i}", True, domain="ELT")
    _seed("gov-0", True, domain="Governance")
    _seed("gov-1", False, domain="Governance")
    _seed("gov-2", False, domain="Governance")

    body = client.get("/api/readiness").json()
    by_domain = body["data"]["byDomain"]
    assert by_domain["ELT"]["ready"] is True
    assert by_domain["ELT"]["accuracy"] == pytest.approx(1.0)
    assert by_domain["Governance"]["ready"] is False
    assert by_domain["Governance"]["accuracy"] == pytest.approx(1 / 3)
    # Per-domain blocks expose only accuracy + ready (leak-free).
    assert set(by_domain["ELT"]) == {"accuracy", "ready"}


def test_readiness_rolling_window_respected(client, monkeypatch):
    """Only the last ``window`` attempts count, not lifetime average."""
    # Use a small window so the test is cheap and unambiguous.
    monkeypatch.setattr(store, "READINESS_WINDOW", 5)

    # Oldest 5 are wrong, newest 5 are right. Lifetime = 0.5 (not ready),
    # but the rolling window of 5 newest = 1.0 (ready).
    _seed("old-0", False, answered_at="2026-06-01T00:00:00+00:00")
    _seed("old-1", False, answered_at="2026-06-01T00:01:00+00:00")
    _seed("old-2", False, answered_at="2026-06-01T00:02:00+00:00")
    _seed("old-3", False, answered_at="2026-06-01T00:03:00+00:00")
    _seed("old-4", False, answered_at="2026-06-01T00:04:00+00:00")
    _seed("new-0", True, answered_at="2026-06-07T00:00:00+00:00")
    _seed("new-1", True, answered_at="2026-06-07T00:01:00+00:00")
    _seed("new-2", True, answered_at="2026-06-07T00:02:00+00:00")
    _seed("new-3", True, answered_at="2026-06-07T00:03:00+00:00")
    _seed("new-4", True, answered_at="2026-06-07T00:04:00+00:00")

    body = client.get("/api/readiness").json()
    overall = body["data"]["overall"]
    assert overall["window"] == 5
    assert overall["accuracy"] == pytest.approx(1.0)
    assert overall["ready"] is True


def test_readiness_empty_history_not_ready_success(client):
    body = client.get("/api/readiness").json()
    assert body["success"] is True
    assert body["error"] is None
    overall = body["data"]["overall"]
    assert overall["accuracy"] == 0.0
    assert overall["ready"] is False
    assert body["data"]["byDomain"] == {}


def test_readiness_exam_filter_narrows(client):
    # associate is strong, professional is weak.
    for i in range(4):
        _seed(f"a-{i}", True, exam="associate", domain="ELT")
    for i in range(4):
        _seed(f"p-{i}", False, exam="professional", domain="ELT")

    body = client.get("/api/readiness", params={"exam": "associate"}).json()
    overall = body["data"]["overall"]
    assert overall["accuracy"] == pytest.approx(1.0)
    assert overall["ready"] is True


def test_readiness_invalid_exam_is_error(client):
    resp = client.get("/api/readiness", params={"exam": "wizard"})
    body = resp.json()
    assert body["success"] is False
    assert body["data"] is None
    assert "Invalid exam type" in body["error"]


def test_readiness_surfaces_threshold_and_window(client):
    _seed("ex-1", True, domain="ELT")
    body = client.get("/api/readiness").json()
    assert body["data"]["threshold"] == pytest.approx(store.READINESS_THRESHOLD)
    assert body["data"]["window"] == store.READINESS_WINDOW
