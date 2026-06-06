---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.1: Match Count Endpoint & Start-Screen Preview

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-1-match-count-endpoint-start-screen

## Story Statement

As a **student**,
I want **to see how many questions match my filters before I start**,
So that **I can right-size a session instead of starting blind**.

## Acceptance Criteria

**AC1 — Leak-free count endpoint**
**Given** the backend is running
**When** I call `GET /api/exercises/count?domain=...&difficulty=...`
**Then** it returns the standard `{success, data, error}` wrapper where `data` is `{count: <int>}` only
**And** the response carries **no** options, pools, `displayedOptions`, explanations, references, or `correct` flags (leak-free, preserving the FR-20 non-leakage rule).

**AC2 — Filter semantics match the corpus**
**Given** loaded exercises
**When** `domain` and/or `difficulty` query params are supplied (both optional, case-insensitive, whitespace-tolerant)
**Then** `count` equals the number of exercises returned by the shared `filter_exercises` helper for those filters
**And** with no `domain`/`difficulty`, `count` equals the **Associate** corpus size (per Story 6.7, `exam` defaults to `associate` so the count never mixes exams — superseded the original "full loaded corpus" wording)
**And** an invalid `domain`/`difficulty` returns `{success: false, data: null, error: <message>}` consistent with `GET /api/sessions`.

**AC3 — Live count on the Start screen**
**Given** the Start screen (`frontend/src/pages/SessionSelect.jsx`)
**When** I change the domain or difficulty select
**Then** the count refreshes from `GET /api/exercises/count` and displays **"{n} questions match"** (singular "1 question matches")
**And** the count is shown before I click Start (no blind starts).

**AC4 — Empty state disables Start**
**Given** the current filters match zero exercises
**When** the count resolves to 0
**Then** the Start button is disabled
**And** a clear empty-state message is shown ("No questions match these filters").

**AC5 — Tests**
**Given** the implementation
**Then** backend tests cover the endpoint (shape, leak-free keys, filtered counts, full-corpus count, invalid-filter error)
**And** frontend tests cover the live-count display updating on filter change, singular/plural, and the 0 → disabled-Start empty state.

## Architecture Context

- **New endpoint:** `GET /api/exercises/count` returns a **lightweight match count** for the Start-screen "{n} questions match" preview. Filters: `domain`, `difficulty` (architecture rev 3 lists `type` as a future filter; this story wires only the two the Start screen exposes). Response `data`: `{count}`. Returns **no pools/options/flags**. [Source: architecture.md#api-design]
- **Why a dedicated endpoint (gap G1):** the practice client must never receive `correct` flags. `GET /api/exercises` returns authored exercises including pools/flags and so would violate the FR-20 non-leakage rule; the runner uses `/api/sessions` + `/api/exercises/count`, never `/api/exercises`. [Source: architecture.md#api-design]
- **Response wrapper:** all requests/responses use the standard `{success, data, error}` wrapper. [Source: architecture.md#api-design]
- **Filtering:** reuse the existing `filter_exercises(exercises, domain=..., difficulty=...)` helper — case-insensitive, whitespace-tolerant — so the count is consistent with `GET /api/sessions` and `GET /api/exercises`. [Source: backend/app/content.py]
- **Start-screen behavior (UX-DR9):** match count updates live as domain/difficulty change; **"{n} questions match"** / **"No questions match these filters"**; empty match disables Start, surfacing the existing empty guidance *before* clicking; loading/error use existing patterns. [Source: EXPERIENCE.md#start-screen-states]

## Tasks / Subtasks

- [ ] **Task 1: Add `GET /api/exercises/count` endpoint** (AC1, AC2)
  - [ ] In `backend/app/main.py`, add a route `@app.get("/api/exercises/count")` accepting optional `domain` and `difficulty` query params (mirror the `Query(None, ...)` signature used by `get_session`).
  - [ ] Read exercises from `getattr(app.state, "exercises", [])` (guard against pre-startup access, matching existing routes).
  - [ ] Validate `domain`/`difficulty` case-insensitively against `Domain`/`Difficulty` enums and return `{success: false, data: null, error: ...}` on invalid input — copy the validation loop pattern from `get_session`.
  - [ ] Apply `filter_exercises(exercises, domain=domain, difficulty=difficulty)` and return `{"success": True, "data": {"count": len(filtered)}, "error": None}`.
  - [ ] Ensure the response contains only the count — do **not** serialize any exercise objects.

- [ ] **Task 2: Add `getExerciseCount` to the frontend API client** (AC1, AC3)
  - [ ] In `frontend/src/api.js`, add `getExerciseCount({ domain, difficulty } = {})` that builds the query string (same `URLSearchParams` pattern as `getSession`), calls `apiRequest('/api/exercises/count...')`, throws `APIError` on `!result.success`, and returns `result.data.count` (default 0 if missing/non-number).

- [ ] **Task 3: Wire the live count into SessionSelect** (AC3, AC4)
  - [ ] In `frontend/src/pages/SessionSelect.jsx`, add `count` and `countLoading` state.
  - [ ] Add a `useEffect` keyed on `[domain, difficulty]` that calls `getExerciseCount`, with cleanup/ignore-stale-response handling so rapid filter changes don't render a stale count.
  - [ ] Render **"{n} questions match"** (use "1 question matches" when count === 1) below the filters; show "No questions match these filters" when count === 0.
  - [ ] Disable the Start button when `count === 0` (combine with the existing `loading` disable).
  - [ ] Preserve existing Start behavior (`getSession`, error alert, loading spinner) — do not remove it.

- [ ] **Task 4: Backend tests** (AC5)
  - [ ] Add `backend/tests/test_exercises_count.py` (co-located with the other endpoint tests, using the shared `client` fixture from `conftest.py`).
  - [ ] Test: `{success, data, error}` wrapper, 200, `data` is `{"count": <int>}`.
  - [ ] Test: leak-free — recursively assert no `correct` / `options` / `pool` / `displayedOptions` / `explanation` keys appear in the payload (reuse the `_iter_keys` recursion pattern from `test_sessions.py`).
  - [ ] Test: no-filter count equals the Associate corpus (default exam, per 6.7); a `domain` filter count equals the matching subset; a `domain`+`difficulty` filter narrows further.
  - [ ] Test: invalid `domain`/`difficulty` returns `success: false` with an error message.

- [ ] **Task 5: Frontend tests** (AC5)
  - [ ] Extend `frontend/src/pages/SessionSelect.test.jsx` (mocks `../api` via `vi.mock`).
  - [ ] Test: count renders after mount and updates when domain/difficulty change (assert `getExerciseCount` called with the new filters and "{n} questions match" shown).
  - [ ] Test: singular form "1 question matches" when count === 1.
  - [ ] Test: count 0 disables the Start button and shows the empty-state message.
  - [ ] Update existing tests if needed so `getExerciseCount` is mocked (e.g. `api.getExerciseCount.mockResolvedValue(...)`) to avoid unhandled rejections.

## Dev Notes

### Backend — `backend/app/main.py` (UPDATE)
- **Current state:** Defines `GET /api/exercises` (full exercises incl. pools/flags), `GET /api/sessions` (leak-free session), `GET /api/export/anki`, `POST /api/feedback`. All return the `{success, data, error}` wrapper and read `app.state.exercises` set by the `lifespan` loader.
- **What to add:** a `GET /api/exercises/count` route. Model it on `get_session` (lines 136-200): same `domain`/`difficulty` `Query(None, ...)` signature, same `app.state` guard, same case-insensitive enum-validation loop returning an error wrapper on bad input.
- **What to preserve:** do not touch the other routes, the `lifespan` loader, or CORS config. The count endpoint must serialize **only** `{count}` — never `e.dict()` of any exercise.

### Backend — `backend/app/content.py` (REUSE, no change)
- **Current state:** `filter_exercises(exercises, domain=None, difficulty=None, exam=None, exercise_type=None)` already filters case-insensitively and whitespace-tolerantly. Reuse it directly; the count is `len(filter_exercises(...))`. No edits expected here.

### Frontend — `frontend/src/api.js` (UPDATE)
- **Current state:** exports `apiRequest`, `isBackendAvailable`, `getSession`, `submitFeedback`. `getSession` already shows the query-string + `{success}` handling pattern to mirror.
- **What to add:** `getExerciseCount({ domain, difficulty })` returning a number. Preserve all existing exports.

### Frontend — `frontend/src/pages/SessionSelect.jsx` (UPDATE)
- **Current state:** local `domain`/`difficulty`/`loading`/`error` state; `handleStart` calls `getSession` and routes via `startSession`; empty result only surfaces as an error *after* clicking Start.
- **What to change:** add a live count driven by a `useEffect` on `[domain, difficulty]`, render it, and disable Start at 0. The empty-state guidance now appears *before* clicking (UX-DR9), but keep the post-Start error alert as a fallback.
- **What to preserve:** the existing filter selects (`DOMAINS`/`DIFFICULTIES` from `../constants`), the Start button styling/spinner, the `error` alert, and `startSession` wiring.

### Testing
- **Backend:** co-located in `backend/tests/`, run with `uv run pytest` (e.g. `uv run pytest backend/tests/test_exercises_count.py`). Use the shared `client` fixture in `backend/tests/conftest.py` (loads real exercises into `app.state` once per session). **Use uv, never pip.**
- **Frontend:** `vitest` via the project's test setup (`*.test.jsx` co-located in `frontend/src`). Tests mock `../api` with `vi.mock('../api')`; render through `SessionProvider` as the existing `SessionSelect.test.jsx` does.

### References

- [Source: epics.md#story-6.1-match-count-endpoint--start-screen-preview] — story statement, ACs, UX-DR9 coverage.
- [Source: epics.md#ux-dr-coverage-map-epic-6] — UX-DR9 → Epic 6, `GET /api/exercises/count`.
- [Source: architecture.md#api-design] — G1 decision, `{count}` response, no pools/options/flags, FR-20 non-leakage, `{success, data, error}` wrapper.
- [Source: EXPERIENCE.md#start-screen-states] — live match count, "{n} questions match" / "No questions match these filters", empty → Start disabled, loading/error patterns retained.
- [Source: backend/app/main.py] — existing `get_session` route to model the new endpoint on.
- [Source: backend/app/content.py] — `filter_exercises` reuse.
- [Source: backend/tests/test_sessions.py] — `_iter_keys` leak-free assertion pattern; `conftest.py` `client` fixture.
- [Source: frontend/src/api.js] — `getSession` pattern for `getExerciseCount`.
- [Source: frontend/src/pages/SessionSelect.test.jsx] — existing frontend test conventions.

## Dev Agent Record

### Agent Model Used

(To be filled in by the dev agent.)

### Completion Notes List

(To be filled in upon task completion.)

### File List

(Files will be listed here upon completion.)
