"""Local SQLite attempt store (AR-16 / FR-22).

A single-user, local-only persistence layer for the learner's answer history,
built on the Python stdlib ``sqlite3`` (no pip dependency). Every graded answer
is recorded as a row in the ``attempts`` table; stats, readiness, and
unseen-first ordering are aggregations/queries over that table.

The DB is a gitignored local file at ``backend/data/progress.db``. The path can
be overridden via the ``ATTEMPT_DB_PATH`` env var or by passing ``path=`` to any
helper, so tests can point at a temp DB.

Schema::

    attempts(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id   TEXT NOT NULL,
        exam          TEXT,
        domain        TEXT,
        correct       INTEGER NOT NULL,   -- 0/1
        selected_id   TEXT,
        time_taken_ms INTEGER,
        answered_at   TEXT NOT NULL       -- UTC ISO-8601
    )

This story (7.1) provides only the store + helpers. Wiring the record hook into
``POST /api/feedback`` (7.2), unseen-first ordering (7.3), and the stats /
readiness endpoints (7.4/7.5) are owned by later stories.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Default DB location: backend/data/progress.db (gitignored). This file lives at
# backend/app/store.py, so the data dir is a sibling of app/.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "progress.db"


def _resolve_path(path: str | os.PathLike | None) -> Path:
    """Resolve the DB path, honoring the ATTEMPT_DB_PATH override.

    Precedence: explicit ``path`` arg > ``ATTEMPT_DB_PATH`` env var > default.
    """
    if path is not None:
        return Path(path)
    env_path = os.getenv("ATTEMPT_DB_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_DB_PATH


def _connect(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Open a connection to the attempt DB, creating parent dirs as needed.

    Rows are returned as ``sqlite3.Row`` so callers can index by column name.
    """
    db_path = _resolve_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: str | os.PathLike | None = None) -> None:
    """Create the ``attempts`` table if it does not already exist.

    Idempotent: safe to call on every startup. Wired into the FastAPI lifespan.
    """
    conn = _connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id   TEXT NOT NULL,
                exam          TEXT,
                domain        TEXT,
                correct       INTEGER NOT NULL,
                selected_id   TEXT,
                time_taken_ms INTEGER,
                answered_at   TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def record_attempt(
    exercise_id: str,
    exam: str | None = None,
    domain: str | None = None,
    correct: bool = False,
    selected_id: str | None = None,
    time_taken_ms: int | None = None,
    answered_at: str | None = None,
    path: str | os.PathLike | None = None,
) -> int:
    """Record a single graded attempt and return its new row id.

    Args:
        exercise_id: The original authored exercise id (required).
        exam: Exam scope (e.g. "associate", "professional"); optional.
        domain: The exercise's domain; optional.
        correct: Whether the answer was correct. Stored as 0/1.
        selected_id: The original option id the user selected; optional.
        time_taken_ms: Per-question time in ms (FR-28); null if absent.
        answered_at: UTC ISO-8601 timestamp; defaults to "now" in UTC.
        path: Optional DB path override (tests).

    Returns:
        The autoincrement ``id`` of the inserted row.
    """
    if answered_at is None:
        answered_at = datetime.now(timezone.utc).isoformat()

    conn = _connect(path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO attempts (
                exercise_id, exam, domain, correct, selected_id,
                time_taken_ms, answered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exercise_id,
                exam,
                domain,
                1 if correct else 0,
                selected_id,
                time_taken_ms,
                answered_at,
            ),
        )
        conn.commit()
        # lastrowid is typed Optional but is always set after a successful
        # single-row INSERT; coalesce to satisfy the type checker.
        return int(cursor.lastrowid or 0)
    finally:
        conn.close()


def _filter_clause(
    exam: str | None,
    domain: str | None,
) -> tuple[str, list]:
    """Build a ``WHERE`` clause + params for the optional exam/domain filters.

    ``difficulty`` is accepted by the public helpers for forward-compatibility
    but is not a column on ``attempts`` (the store records the domain/exam of an
    attempt, not its difficulty), so it does not contribute to the clause here.
    """
    clauses: list[str] = []
    params: list = []
    if exam is not None:
        clauses.append("exam = ?")
        params.append(exam)
    if domain is not None:
        # Match on COALESCE so the empty-string bucket (the key used for rows
        # with domain IS NULL, e.g. from domain_accuracy/_domains_for) matches
        # those NULL rows — keeps per-domain readiness consistent with stats.
        clauses.append("COALESCE(domain, '') = ?")
        params.append(domain)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def attempted_ids(
    exam: str | None = None,
    domain: str | None = None,
    difficulty: str | None = None,
    path: str | os.PathLike | None = None,
) -> set[str]:
    """Return the set of distinct exercise ids with at least one attempt.

    Filters (exam/domain) are optional. ``difficulty`` is accepted for a stable
    signature but is not stored on attempts, so it does not filter rows.
    """
    where, params = _filter_clause(exam, domain)
    conn = _connect(path)
    try:
        rows = conn.execute(f"SELECT DISTINCT exercise_id FROM attempts{where}", params).fetchall()
        return {row["exercise_id"] for row in rows}
    finally:
        conn.close()


def last_seen_map(
    exam: str | None = None,
    domain: str | None = None,
    difficulty: str | None = None,
    path: str | os.PathLike | None = None,
) -> dict[str, str]:
    """Map each attempted exercise id to its most recent ``answered_at``.

    Used by unseen-first ordering (Story 7.3) to break ties by least-recently
    seen. Filters are optional; ``difficulty`` is accepted but not stored.
    """
    where, params = _filter_clause(exam, domain)
    conn = _connect(path)
    try:
        rows = conn.execute(
            f"""
            SELECT exercise_id, MAX(answered_at) AS last_seen
            FROM attempts{where}
            GROUP BY exercise_id
            """,
            params,
        ).fetchall()
        return {row["exercise_id"]: row["last_seen"] for row in rows}
    finally:
        conn.close()


def domain_accuracy(
    exam: str | None = None,
    path: str | os.PathLike | None = None,
) -> dict[str, dict]:
    """Per-domain accuracy: ``{domain: {attempts, correct, accuracy}}``.

    ``accuracy`` is ``correct / attempts`` (0.0 when a domain has no attempts,
    which can't happen here since only domains with rows appear). Attempts whose
    ``domain`` is NULL are grouped under the empty-string key. Returns an empty
    dict when there are no attempts.
    """
    where, params = _filter_clause(exam, None)
    conn = _connect(path)
    try:
        rows = conn.execute(
            f"""
            SELECT
                COALESCE(domain, '') AS domain,
                COUNT(*)             AS attempts,
                SUM(correct)         AS correct
            FROM attempts{where}
            GROUP BY COALESCE(domain, '')
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    result: dict[str, dict] = {}
    for row in rows:
        attempts = int(row["attempts"])
        correct = int(row["correct"] or 0)
        result[row["domain"]] = {
            "attempts": attempts,
            "correct": correct,
            "accuracy": (correct / attempts) if attempts else 0.0,
        }
    return result


def overall_stats(
    exam: str | None = None,
    path: str | os.PathLike | None = None,
) -> dict:
    """Aggregate stats over all attempts (optionally scoped to one exam).

    Returns::

        {
            "total": int,            # total attempts
            "correct": int,          # correct attempts
            "accuracy": float,       # correct / total (0.0 when empty)
            "by_domain": {domain: {attempts, correct, accuracy}},
        }

    Safe on an empty DB: total/correct = 0, accuracy = 0.0, by_domain = {}.
    """
    where, params = _filter_clause(exam, None)
    conn = _connect(path)
    try:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*)     AS total,
                SUM(correct) AS correct
            FROM attempts{where}
            """,
            params,
        ).fetchone()
    finally:
        conn.close()

    total = int(row["total"] or 0)
    correct = int(row["correct"] or 0)
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "by_domain": domain_accuracy(exam=exam, path=path),
    }


def daily_stats(
    exam: str | None = None,
    path: str | os.PathLike | None = None,
) -> list[dict]:
    """Per-day trend series over the attempt history (FR-23).

    Groups attempts by the calendar date of ``answered_at`` (UTC, the date part
    of the stored ISO-8601 timestamp) and returns one entry per day, oldest
    first::

        [
            {"date": "2026-06-05", "attempts": 3, "correct": 2, "accuracy": 0.6667},
            {"date": "2026-06-06", "attempts": 5, "correct": 5, "accuracy": 1.0},
            ...
        ]

    Optionally scoped to one exam. Returns an empty list when there are no
    attempts. Used by ``GET /api/stats`` as the ``trend`` series. Leak-free:
    only aggregate counts over attempts, never content or per-option flags.
    """
    where, params = _filter_clause(exam, None)
    conn = _connect(path)
    try:
        rows = conn.execute(
            f"""
            SELECT
                date(answered_at) AS day,
                COUNT(*)          AS attempts,
                SUM(correct)      AS correct
            FROM attempts{where}
            GROUP BY date(answered_at)
            ORDER BY date(answered_at) ASC
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    series: list[dict] = []
    for row in rows:
        attempts = int(row["attempts"])
        correct = int(row["correct"] or 0)
        series.append(
            {
                "date": row["day"],
                "attempts": attempts,
                "correct": correct,
                "accuracy": (correct / attempts) if attempts else 0.0,
            }
        )
    return series


# Rolling-window readiness defaults (FR-25). The ~70% bar is a *planning
# heuristic* surfaced as guidance, not an official per-domain cut (addendum §C).
# Readiness reflects *recent* performance, so accuracy is computed over the last
# ``READINESS_WINDOW`` attempts rather than the lifetime average.
READINESS_WINDOW = 20
READINESS_THRESHOLD = 0.70


def rolling_accuracy(
    window: int = READINESS_WINDOW,
    exam: str | None = None,
    domain: str | None = None,
    path: str | os.PathLike | None = None,
) -> dict:
    """Accuracy over the most recent ``window`` attempts (FR-25, readiness).

    Selects the latest ``window`` attempts (ordered by ``answered_at`` then
    ``id`` so ties on timestamp are stable) — optionally scoped to one exam
    and/or domain — and returns::

        {"attempts": int, "correct": int, "accuracy": float, "window": int}

    ``attempts`` is the number of attempts actually considered (<= ``window``,
    and < ``window`` when fewer attempts exist). ``accuracy`` is 0.0 when there
    are no attempts. Leak-free: aggregates over attempts only.
    """
    where, params = _filter_clause(exam, domain)
    conn = _connect(path)
    try:
        rows = conn.execute(
            f"""
            SELECT correct FROM attempts{where}
            ORDER BY answered_at DESC, id DESC
            LIMIT ?
            """,
            [*params, int(window)],
        ).fetchall()
    finally:
        conn.close()

    attempts = len(rows)
    correct = sum(int(r["correct"] or 0) for r in rows)
    return {
        "attempts": attempts,
        "correct": correct,
        "accuracy": (correct / attempts) if attempts else 0.0,
        "window": int(window),
    }


def _domains_for(
    exam: str | None,
    path: str | os.PathLike | None,
) -> list[str]:
    """Distinct domain keys present in the attempt history (NULL -> '')."""
    where, params = _filter_clause(exam, None)
    conn = _connect(path)
    try:
        rows = conn.execute(
            f"SELECT DISTINCT COALESCE(domain, '') AS domain FROM attempts{where}",
            params,
        ).fetchall()
    finally:
        conn.close()
    return [row["domain"] for row in rows]


def readiness(
    window: int | None = None,
    threshold: float | None = None,
    exam: str | None = None,
    path: str | os.PathLike | None = None,
) -> dict:
    """Rolling-window readiness, overall + per-domain (FR-25).

    ``ready`` is ``rolling-window accuracy >= threshold`` (the ~70% planning
    heuristic, addendum §C — guidance, not a guarantee). Per-domain readiness
    uses each domain's own rolling window. Returns::

        {
            "overall": {"accuracy": float, "ready": bool, "window": int,
                        "attempts": int, "threshold": float},
            "byDomain": {<domain>: {"accuracy": float, "ready": bool,
                                    "window": int, "attempts": int}},
            "threshold": float,
            "window": int,
        }

    Empty history -> overall accuracy 0.0, ready False, byDomain empty.

    ``window`` / ``threshold`` default to the module-level ``READINESS_WINDOW``
    / ``READINESS_THRESHOLD`` *at call time* (resolved here, not as bound
    argument defaults) so tests can monkeypatch them on the module.
    """
    if window is None:
        window = READINESS_WINDOW
    if threshold is None:
        threshold = READINESS_THRESHOLD
    overall = rolling_accuracy(window=window, exam=exam, path=path)
    overall_block = {
        "accuracy": overall["accuracy"],
        "ready": overall["accuracy"] >= threshold,
        "window": overall["window"],
        "attempts": overall["attempts"],
        "threshold": threshold,
    }

    by_domain: dict[str, dict] = {}
    for domain in _domains_for(exam, path):
        dom = rolling_accuracy(window=window, exam=exam, domain=domain, path=path)
        by_domain[domain] = {
            "accuracy": dom["accuracy"],
            "ready": dom["accuracy"] >= threshold,
            "window": dom["window"],
            "attempts": dom["attempts"],
        }

    return {
        "overall": overall_block,
        "byDomain": by_domain,
        "threshold": threshold,
        "window": int(window),
    }
