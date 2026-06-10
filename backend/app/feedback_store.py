"""Sidecar store for in-app question feedback (Story 11.1, FR-32 / AR-21).

Free-text learner notes on an Exercise are appended to a sidecar YAML
(``exercises/feedback.yaml``), keyed by Exercise ``id``. The authored Exercise
files are NEVER modified by this store — only the sidecar — so hand-authored
comments and Option-Pool layout stay pristine. This is the app's first
content-write path; it is deliberately narrow (notes only, no editing).

Distinct from:
  * ``feedback.py`` — MCQ answer grading (read-only on content).
  * ``store.py`` — the MCQ-scoped SQLite attempt history.

Sidecar schema (``feedback.yaml``)::

    <exercise_id>:
      - note: "free text"
        created_at: "2026-06-10T14:30:00Z"   # server-stamped, ISO 8601 UTC
        resolved: false

Story 11.2's ``write-mcq`` revision flow consumes ``open_notes()`` and calls
``mark_resolved()`` after it edits an Exercise.

Robustness (code review 2026-06-10): reads tolerate a corrupt or hand-mangled
sidecar (malformed YAML raises a clear :class:`FeedbackStoreError`; malformed
*values* are skipped, never crash), and writes are atomic (temp file +
``os.replace``) so an interrupted write can't leave a half-written file.
"""

import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Serialize read-modify-write so concurrent submits in THIS process can't lose an
# entry. Cross-process coordination (the API vs the write-mcq one-liner) is not
# covered — see deferred-work.md.
_LOCK = threading.Lock()

# Generous upper bound on a single note — guards unbounded file growth / abuse.
MAX_NOTE_LENGTH = 2000


class FeedbackStoreError(Exception):
    """The sidecar feedback file exists but can't be read (e.g. corrupt YAML)."""


def _default_feedback_path() -> Path:
    """Resolve ``exercises/feedback.yaml``, mirroring content.py's project-root walk."""
    current = Path(__file__).parent
    while current != current.parent:
        candidate = current.parent / "exercises"
        if candidate.exists():
            return candidate / "feedback.yaml"
        current = current.parent
    return Path("exercises/feedback.yaml")


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        # Don't crash (500) and don't silently treat as empty (which would let a
        # write clobber a recoverable file) — surface a clear, file-named error.
        raise FeedbackStoreError(f"Feedback file is not valid YAML ({path}): {e}") from e
    return data if isinstance(data, dict) else {}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: serialize to a temp file in the same directory, then replace,
    # so an interrupted/failed write can never leave a half-written sidecar.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".feedback-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=True, allow_unicode=True, default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _clean_entries(data: dict, exercise_id: str) -> list:
    """The dict entries for an id, tolerating a malformed (non-list/non-dict) sidecar."""
    entries = data.get(exercise_id)
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict)]


def add_note(exercise_id: str, note: str, *, path: Path | None = None) -> dict:
    """Append a free-text note for ``exercise_id``; return the created entry.

    The note is server-stamped (``created_at``) and starts unresolved. Raises
    ``ValueError`` on an empty/whitespace-only note or one over ``MAX_NOTE_LENGTH``
    (nothing is written). Raises ``FeedbackStoreError`` if the existing sidecar is
    unreadable.
    """
    text = (note or "").strip()
    if not text:
        raise ValueError("Feedback note must not be empty")
    if len(text) > MAX_NOTE_LENGTH:
        raise ValueError(f"Feedback note is too long (max {MAX_NOTE_LENGTH} characters)")
    p = path or _default_feedback_path()
    entry = {
        "note": text,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved": False,
    }
    with _LOCK:
        data = _load(p)
        existing = data.get(exercise_id)
        if not isinstance(existing, list):
            existing = []
        existing.append(entry)
        data[exercise_id] = existing
        _save(p, data)
    return entry


def notes_for(exercise_id: str, *, path: Path | None = None) -> list[dict]:
    """All notes (resolved or not) recorded for ``exercise_id`` (possibly empty)."""
    p = path or _default_feedback_path()
    with _LOCK:
        return _clean_entries(_load(p), exercise_id)


def open_notes(*, path: Path | None = None) -> dict:
    """Map of ``exercise_id`` -> its unresolved notes, for exercises that have any.

    Drives Story 11.2's revision sweep (only act on exercises with open feedback).
    """
    p = path or _default_feedback_path()
    with _LOCK:
        data = _load(p)
    result = {}
    for ex_id, entries in data.items():
        if not isinstance(entries, list):
            continue
        unresolved = [e for e in entries if isinstance(e, dict) and not e.get("resolved")]
        if unresolved:
            result[ex_id] = unresolved
    return result


def mark_resolved(exercise_id: str, *, path: Path | None = None) -> int:
    """Mark all of an exercise's open notes resolved; return how many changed."""
    p = path or _default_feedback_path()
    with _LOCK:
        data = _load(p)
        entries = data.get(exercise_id)
        if not isinstance(entries, list):
            return 0
        changed = 0
        for e in entries:
            if isinstance(e, dict) and not e.get("resolved"):
                e["resolved"] = True
                changed += 1
        if changed:
            _save(p, data)
    return changed
