# Deferred Work

## Deferred from: code review of Epic 7 (2026-06-07)

- **Timestamp format is brittle if write paths diverge** (`backend/app/store.py`) — `daily_stats`/`rolling_accuracy` rely on lexicographic ISO-string ordering + SQLite `date()`. All current writes use `datetime.now(timezone.utc).isoformat()` (uniform `+00:00`), so it's correct today; a future write path with a `Z` suffix or local offset would mis-sort/mis-bucket. Normalize to a canonical UTC form if/when another writer appears. Also: `date()` buckets by UTC day, not the user's local day (fine for a solo local user).

## Deferred from: code review of Epic 6 (2026-06-06)

- **Replay exam-scope is convention-only (defense-in-depth)** — `frontend/src/api.js` `getSessionByIds` never sends `exam`, so the backend `POST /api/sessions` `exam` scoping is unused by the UI. Harmless today (session id sets are single-exam), but the "never mix corpora" guarantee on the replay path rests on the id set being homogeneous. Proper fix needs tracking the active session's `exam` in context. Low practical risk now.
- **aria-live announcer re-announces full progress on every option selection** (`frontend/src/pages/MCQPractice.jsx`) — the polite live region recomputes "Progress: …" on each render incl. selection; noisy for AT users. Minor polish; only the submit transition meaningfully changes.

## Deferred from: code review of Epic 5 (2026-06-06)

- **Summary denominator counts unanswered/skipped** (`frontend/src/pages/Summary.jsx`) — headline `{correct}/{total}` uses `exercises.length`; skipped/unanswered understate the score. Belongs to Epic 6 (quit-to-partial-summary surfaces answered/skipped counts). Pre-existing logic from Epic 3.
- **Empty-session message when only code_completion matches** (`backend/app/session.py` + `frontend/src/pages/SessionSelect.jsx`) — `build_session` filters out non-MCQ, so a filter matching only code_completion yields `[]` and the UI says "no exercises match those filters" (misleading). Non-issue with the current all-MCQ corpus; revisit when code_completion content lands (Epic 4).
- **`request.type` not validated against the stored exercise type** (`backend/app/main.py`, `feedback.py`) — client-supplied `type` is decorative; an isinstance check catches mismatches, but the request `type` is never cross-checked against truth. Hardening only.
- **`export_anki` reads `app.state.exercises` without the `getattr` guard** (`backend/app/main.py`) — pre-existing (not Epic 5); inconsistent with the new endpoints' defensive `getattr`. Could AttributeError → 500 if hit before lifespan startup.
- **Malformed POST body returns FastAPI 422, not the `{success,data,error}` envelope** (`backend/app/main.py`) — programmer-error path; partially mitigated once the frontend surfaces submit errors (patch). Consider a 422→envelope exception handler later.
