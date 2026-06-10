---
status: review
baseline_commit: 247164b
---

# Story 4.7: Exercise-Type Filter (multiselect, MCQ default)

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-7-exercise-type-filter

## Story Statement

As a **student**,
I want **to choose which exercise type(s) a session includes — multiple choice, code completion, or both — with multiple choice selected by default**,
So that **I can drill the Wordle-style code-completion exercises directly instead of hunting for them interleaved among dozens of MCQs**.

(Added 2026-06-09 during the Epic 4 dev-story run. Makes the Code-Completion content discoverable in the UI — the runner built in Stories 4.1–4.5 is useless if users can't reach a code-completion exercise.)

## Acceptance Criteria

**Given** the Start screen
**When** I view the filters
**Then** there is an **Exercise type** multiselect listing **Multiple choice** and **Code completion**, with **Multiple choice selected by DEFAULT** (the familiar experience is unchanged)
**And** I can check **Code completion** (and/or uncheck Multiple choice) to scope the session
**When** I start a session scoped to **Code completion**
**Then** the session contains **only** code-completion exercises (which route to the `CodeCompletion` runner)
**And** the live match count reflects the selected type(s)
**And** `GET /api/sessions` and `GET /api/exercises/count` accept a **repeatable** `exercise_type` query param (any-of semantics), validated against the `ExerciseType` enum
**And** vitest + pytest cover the multiselect default, type-scoped sessions/counts, multi-value any-of, and invalid-type rejection

Acceptance detail:

- **MCQ is the default selection** (not "all"), so the existing study flow is unchanged for users who never touch the filter.
- **Empty selection = all types** (never blocks): if the user unchecks everything, no `exercise_type` is sent and the backend returns all types. Documented, least-surprising fallback consistent with how an empty Domain filter means "all domains".
- The backend already had a single-value `exercise_type` on `GET /api/exercises` and `filter_exercises`; this story generalizes it to **multi-value** on the runner endpoints and wires the UI.

## Architecture Context

- **Discoverability gap (root cause).** `build_session` already DELIVERS code-completion entries (rev 5), and `App.PracticeRouter` already routes them to `CodeCompletion` by `type` — but `SessionSelect` only filtered by exam/domain/difficulty and `GET /api/sessions` silently ignored any type filter, so code-completion items (3 of ~150 Associate exercises) were effectively unreachable. This story closes that gap.
- **Backend (`filter_exercises`, `content.py`).** Generalized `exercise_type` to accept a single value OR a list (any-of membership match), preserving back-compat for the single-value `GET /api/exercises` admin endpoint.
- **Backend (`main.py`).** `GET /api/sessions` and `GET /api/exercises/count` gained a repeatable `exercise_type` query param (`Annotated[list[str] | None, Query(...)]` — modern FastAPI style, ruff-B008-clean). Each value validated against `ExerciseType` via a shared `_validate_exercise_types` helper; an invalid value returns the standard `{success:false, error}` wrapper.
- **Frontend (`constants.js`).** `EXERCISE_TYPE_OPTIONS` drives the multiselect (Multiple choice → `single_choice`, Code completion → `code_completion`).
- **Frontend (`api.js`).** `getSession` / `getExerciseCount` accept `exerciseTypes: string[]` and append a repeated `exercise_type` param per value.
- **Frontend (`SessionSelect.jsx`).** A `<fieldset>` of checkboxes (default `['single_choice']`), threaded into the live-count effect and Start.
- **Supersedes** the single-select "Exercise type" dropdown added earlier the same day (the requirement changed to a multiselect with MCQ default).

## Tasks / Subtasks

- [x] **Task 4.7.1 — Backend: multi-value `exercise_type` filter**
  - [x] `content.py` `filter_exercises`: accept `str | list[str] | None`; any-of membership match (case-insensitive).
  - [x] `main.py` `GET /api/sessions` + `GET /api/exercises/count`: repeatable `exercise_type` query param; `_validate_exercise_types` helper validates each value; pass through to `filter_exercises`.
  - [x] `pytest`: type-scoped session/count, multi-value any-of (both types present), invalid-type rejection, and one-invalid-among-several rejection.
- [x] **Task 4.7.2 — Frontend API + constants**
  - [x] `constants.js`: `EXERCISE_TYPE_OPTIONS`.
  - [x] `api.js`: `getSession`/`getExerciseCount` accept `exerciseTypes: string[]`, append repeated `exercise_type`.
- [x] **Task 4.7.3 — Frontend: SessionSelect multiselect (MCQ default)**
  - [x] Checkboxes (Multiple choice / Code completion) in a labeled `<fieldset>`; default `['single_choice']`.
  - [x] Threaded into the live match-count effect and the Start handler.
  - [x] `vitest`: MCQ checked by default; scoping to code-completion only sends `exerciseTypes: ['code_completion']` to session + count; existing exact-match call assertions updated for the default.

## Dev Notes

### UPDATE files
- `backend/app/content.py` — `filter_exercises` accepts a list of types.
- `backend/app/main.py` — repeatable `exercise_type` on `/api/sessions` + `/api/exercises/count`; `_validate_exercise_types` helper; `Annotated` Query style.
- `backend/tests/test_sessions.py`, `backend/tests/test_count.py` — type-filter tests.
- `frontend/src/constants.js` — `EXERCISE_TYPE_OPTIONS`.
- `frontend/src/api.js` — `exerciseTypes` array param.
- `frontend/src/pages/SessionSelect.jsx` — multiselect checkboxes (MCQ default).
- `frontend/src/pages/SessionSelect.test.jsx` — multiselect tests + updated call assertions.

### Decisions / non-goals
- Empty selection ⇒ all types (never blocks). MCQ default keeps the existing flow unchanged.
- A polished Provider/Certification switcher and broader type taxonomy are out of scope (Epic 9 territory).

## Dev Agent Record

### Agent Model Used
claude-opus-4-8 (dev-story workflow, 2026-06-09).

### Completion Notes List
- Closed the code-completion discoverability gap. Backend `exercise_type` generalized to multi-value (any-of); two runner endpoints + validation wired; frontend multiselect with MCQ default.
- Verified live: code-completion-only session returns exactly the 3 Associate code-completion exercises; both-types returns 147 MCQ + 3 code-completion; counts agree; invalid type rejected.
- Tests: backend `test_sessions.py`/`test_count.py` extended; frontend `SessionSelect.test.jsx` extended (multiselect default + scoping). Full suites green (backend 269, frontend 179); ruff + eslint clean.

### File List
- backend/app/content.py (M)
- backend/app/main.py (M)
- backend/tests/test_sessions.py (M)
- backend/tests/test_count.py (M)
- frontend/src/constants.js (M)
- frontend/src/api.js (M)
- frontend/src/pages/SessionSelect.jsx (M)
- frontend/src/pages/SessionSelect.test.jsx (M)

### Change Log
- 2026-06-09 — Implemented exercise-type multiselect filter (MCQ default); generalized backend `exercise_type` to multi-value; tests added; suites green.
- 2026-06-10 — Code-reviewed alongside the runner. The multiselect made mixed MCQ+code-completion sessions reachable, surfacing 4 mixed-session bugs that were fixed under Story 4.5 (back-nav retention, progress count, Summary miscount, unseen-first ordering). No change to 4.7's own filter behavior.
