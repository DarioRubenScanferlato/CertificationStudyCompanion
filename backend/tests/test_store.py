"""Tests for the local SQLite attempt store (Story 7.1 / AR-16).

All tests use a temp DB path via the ``tmp_path`` fixture so they never touch
the real ``backend/data/progress.db``.
"""

import sqlite3

import pytest

from app import store


@pytest.fixture
def db_path(tmp_path):
    """A temp DB path (the file does not exist yet)."""
    return tmp_path / "progress.db"


# --- init / create-if-absent ------------------------------------------------


def test_init_db_creates_table_and_parent_dir(tmp_path):
    """init_db creates the attempts table (and parent dirs) if absent."""
    path = tmp_path / "nested" / "dir" / "progress.db"
    assert not path.exists()

    store.init_db(path=path)

    assert path.exists()
    conn = sqlite3.connect(str(path))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='attempts'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None


def test_init_db_is_idempotent(db_path):
    """Calling init_db twice is safe and preserves existing rows."""
    store.init_db(path=db_path)
    store.record_attempt("ex-1", correct=True, path=db_path)
    store.init_db(path=db_path)  # must not drop/recreate

    assert store.attempted_ids(path=db_path) == {"ex-1"}


# --- record_attempt / read back ---------------------------------------------


def test_record_attempt_persists_all_fields(db_path):
    store.init_db(path=db_path)
    new_id = store.record_attempt(
        exercise_id="dbx-de-0001",
        exam="associate",
        domain="Data Governance",
        correct=True,
        selected_id="b",
        time_taken_ms=4200,
        answered_at="2026-06-07T10:00:00+00:00",
        path=db_path,
    )
    assert isinstance(new_id, int) and new_id >= 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM attempts WHERE id = ?", (new_id,)).fetchone()
    finally:
        conn.close()

    assert row["exercise_id"] == "dbx-de-0001"
    assert row["exam"] == "associate"
    assert row["domain"] == "Data Governance"
    assert row["correct"] == 1
    assert row["selected_id"] == "b"
    assert row["time_taken_ms"] == 4200
    assert row["answered_at"] == "2026-06-07T10:00:00+00:00"


def test_record_attempt_stores_correct_as_zero_one(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-wrong", correct=False, path=db_path)
    store.record_attempt("ex-right", correct=True, path=db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        values = {
            r[0]: r[1] for r in conn.execute("SELECT exercise_id, correct FROM attempts").fetchall()
        }
    finally:
        conn.close()
    assert values == {"ex-wrong": 0, "ex-right": 1}


def test_record_attempt_defaults_answered_at_to_utc_now(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-1", correct=True, path=db_path)

    seen = store.last_seen_map(path=db_path)
    # An ISO timestamp was stored; it should be a non-empty parseable string.
    ts = seen["ex-1"]
    assert isinstance(ts, str) and ts
    # Should not raise.
    from datetime import datetime

    datetime.fromisoformat(ts)


def test_record_attempt_optional_fields_nullable(db_path):
    store.init_db(path=db_path)
    new_id = store.record_attempt("ex-min", correct=False, path=db_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM attempts WHERE id = ?", (new_id,)).fetchone()
    finally:
        conn.close()
    assert row["exam"] is None
    assert row["domain"] is None
    assert row["selected_id"] is None
    assert row["time_taken_ms"] is None


# --- attempted_ids ----------------------------------------------------------


def test_attempted_ids_distinct_no_filter(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-1", correct=True, path=db_path)
    store.record_attempt("ex-1", correct=False, path=db_path)  # duplicate id
    store.record_attempt("ex-2", correct=True, path=db_path)

    assert store.attempted_ids(path=db_path) == {"ex-1", "ex-2"}


def test_attempted_ids_with_filters(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-a", exam="associate", domain="ELT", correct=True, path=db_path)
    store.record_attempt("ex-b", exam="associate", domain="Governance", correct=True, path=db_path)
    store.record_attempt("ex-c", exam="professional", domain="ELT", correct=True, path=db_path)

    assert store.attempted_ids(exam="associate", path=db_path) == {"ex-a", "ex-b"}
    assert store.attempted_ids(domain="ELT", path=db_path) == {"ex-a", "ex-c"}
    assert store.attempted_ids(exam="associate", domain="ELT", path=db_path) == {"ex-a"}


def test_attempted_ids_empty_db(db_path):
    store.init_db(path=db_path)
    assert store.attempted_ids(path=db_path) == set()


# --- last_seen_map ----------------------------------------------------------


def test_last_seen_map_returns_most_recent(db_path):
    store.init_db(path=db_path)
    store.record_attempt(
        "ex-1", correct=True, answered_at="2026-06-01T00:00:00+00:00", path=db_path
    )
    store.record_attempt(
        "ex-1", correct=False, answered_at="2026-06-05T00:00:00+00:00", path=db_path
    )
    store.record_attempt(
        "ex-2", correct=True, answered_at="2026-06-03T00:00:00+00:00", path=db_path
    )

    seen = store.last_seen_map(path=db_path)
    assert seen == {
        "ex-1": "2026-06-05T00:00:00+00:00",
        "ex-2": "2026-06-03T00:00:00+00:00",
    }


def test_last_seen_map_respects_filters(db_path):
    store.init_db(path=db_path)
    store.record_attempt(
        "ex-a",
        exam="associate",
        answered_at="2026-06-01T00:00:00+00:00",
        correct=True,
        path=db_path,
    )
    store.record_attempt(
        "ex-c",
        exam="professional",
        answered_at="2026-06-02T00:00:00+00:00",
        correct=True,
        path=db_path,
    )

    seen = store.last_seen_map(exam="associate", path=db_path)
    assert seen == {"ex-a": "2026-06-01T00:00:00+00:00"}


def test_last_seen_map_empty_db(db_path):
    store.init_db(path=db_path)
    assert store.last_seen_map(path=db_path) == {}


# --- overall_stats + domain_accuracy math -----------------------------------


def test_overall_stats_math(db_path):
    store.init_db(path=db_path)
    # 4 attempts, 3 correct -> 0.75 accuracy.
    store.record_attempt("ex-1", domain="ELT", correct=True, path=db_path)
    store.record_attempt("ex-2", domain="ELT", correct=False, path=db_path)
    store.record_attempt("ex-3", domain="Governance", correct=True, path=db_path)
    store.record_attempt("ex-4", domain="Governance", correct=True, path=db_path)

    stats = store.overall_stats(path=db_path)
    assert stats["total"] == 4
    assert stats["correct"] == 3
    assert stats["accuracy"] == pytest.approx(0.75)

    by_domain = stats["by_domain"]
    assert by_domain["ELT"] == {"attempts": 2, "correct": 1, "accuracy": pytest.approx(0.5)}
    assert by_domain["Governance"] == {
        "attempts": 2,
        "correct": 2,
        "accuracy": pytest.approx(1.0),
    }


def test_overall_stats_scoped_by_exam(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-a", exam="associate", domain="ELT", correct=True, path=db_path)
    store.record_attempt("ex-b", exam="associate", domain="ELT", correct=False, path=db_path)
    store.record_attempt("ex-c", exam="professional", domain="ELT", correct=True, path=db_path)

    stats = store.overall_stats(exam="associate", path=db_path)
    assert stats["total"] == 2
    assert stats["correct"] == 1
    assert stats["accuracy"] == pytest.approx(0.5)
    assert set(stats["by_domain"]) == {"ELT"}
    assert stats["by_domain"]["ELT"]["attempts"] == 2


def test_overall_stats_empty_db(db_path):
    store.init_db(path=db_path)
    stats = store.overall_stats(path=db_path)
    assert stats == {"total": 0, "correct": 0, "accuracy": 0.0, "by_domain": {}}


def test_domain_accuracy_math(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-1", domain="ELT", correct=True, path=db_path)
    store.record_attempt("ex-2", domain="ELT", correct=True, path=db_path)
    store.record_attempt("ex-3", domain="ELT", correct=False, path=db_path)

    acc = store.domain_accuracy(path=db_path)
    assert acc["ELT"] == {"attempts": 3, "correct": 2, "accuracy": pytest.approx(2 / 3)}


def test_domain_accuracy_groups_null_domain_under_empty_key(db_path):
    store.init_db(path=db_path)
    store.record_attempt("ex-1", correct=True, path=db_path)  # no domain

    acc = store.domain_accuracy(path=db_path)
    assert acc[""] == {"attempts": 1, "correct": 1, "accuracy": pytest.approx(1.0)}


def test_domain_accuracy_empty_db(db_path):
    store.init_db(path=db_path)
    assert store.domain_accuracy(path=db_path) == {}
