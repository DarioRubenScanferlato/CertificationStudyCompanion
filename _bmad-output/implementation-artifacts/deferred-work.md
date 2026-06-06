# Deferred Work

## Deferred from: code review of Epic 5 (2026-06-06)

- **Summary denominator counts unanswered/skipped** (`frontend/src/pages/Summary.jsx`) — headline `{correct}/{total}` uses `exercises.length`; skipped/unanswered understate the score. Belongs to Epic 6 (quit-to-partial-summary surfaces answered/skipped counts). Pre-existing logic from Epic 3.
- **Empty-session message when only code_completion matches** (`backend/app/session.py` + `frontend/src/pages/SessionSelect.jsx`) — `build_session` filters out non-MCQ, so a filter matching only code_completion yields `[]` and the UI says "no exercises match those filters" (misleading). Non-issue with the current all-MCQ corpus; revisit when code_completion content lands (Epic 4).
- **`request.type` not validated against the stored exercise type** (`backend/app/main.py`, `feedback.py`) — client-supplied `type` is decorative; an isinstance check catches mismatches, but the request `type` is never cross-checked against truth. Hardening only.
- **`export_anki` reads `app.state.exercises` without the `getattr` guard** (`backend/app/main.py`) — pre-existing (not Epic 5); inconsistent with the new endpoints' defensive `getattr`. Could AttributeError → 500 if hit before lifespan startup.
- **Malformed POST body returns FastAPI 422, not the `{success,data,error}` envelope** (`backend/app/main.py`) — programmer-error path; partially mitigated once the frontend surfaces submit errors (patch). Consider a 422→envelope exception handler later.
