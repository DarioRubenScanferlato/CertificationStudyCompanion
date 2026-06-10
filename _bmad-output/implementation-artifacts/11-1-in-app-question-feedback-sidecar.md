---
status: done
baseline_commit: 247164b
---

# Story 11.1: In-App Question Feedback → Sidecar YAML

**Epic:** 11 - Question Feedback & Content-Improvement Loop
**Story Key:** 11-1-in-app-question-feedback-sidecar

## Story Statement

As **a student**,
I want **to attach a free-text note to a question while I practice and have it saved**,
So that **bad/unclear questions get flagged for fixing without interrupting my study**.

(FR-32, AR-21 — PRD rev 6 §4.9, addendum §I.)

## Acceptance Criteria

**Given** the practice surface (the MCQ feedback panel and the Code-Completion conclusion)
**When** I open a "Flag / leave a note" affordance and submit a free-text note
**Then** the note is persisted to a sidecar `exercises/feedback.yaml`, keyed by Exercise `id`, with a server-stamped `created_at` and `resolved: false`
**And** the authored Exercise YAML file is **byte-unchanged** (only the sidecar is written)
**And** an empty/whitespace-only note is rejected (no entry written, clear error)
**And** a new `backend/app/feedback_store.py` exposes `add_note` / `notes_for` / `open_notes` / `mark_resolved` over the sidecar (create-if-absent), and a new `POST /api/exercise-feedback {exerciseId, note}` endpoint appends via it using the standard `{success, data, error}` wrapper and validates the `exerciseId` exists in the loaded corpus
**And** a feedback note survives an app restart
**And** the new endpoint does NOT touch the MCQ `POST /api/feedback` grading path or the SQLite attempt store
**And** `pytest` covers add/list/open/resolve + the endpoint (incl. unknown-id and empty-note rejection); `vitest` covers the affordance calling the API and the empty-note guard

Acceptance detail:

- **Free-text note only** (decision-log #49) — no category/severity. Entry shape: `{ note, created_at, resolved }`.
- **Sidecar, not inline** (decision-log #48): authored Exercise files are never rewritten by the app. Only `exercises/feedback.yaml` is written. This is the app's **first content-write path** — a narrow, deliberate reversal of the "no in-app authoring" non-goal (PRD §5 narrowed), distinct from the MCQ-scoped SQLite store.
- Endpoint naming avoids the existing MCQ-grading `POST /api/feedback` — use **`POST /api/exercise-feedback`**.

## Architecture Context

- **Sidecar store (addendum §I, AR-21).** A single YAML `exercises/feedback.yaml` mapping Exercise `id` → list of `{ note, created_at, resolved }`. New module `backend/app/feedback_store.py` (distinct from MCQ `feedback.py`): `add_note(exercise_id, note)`, `notes_for(exercise_id)`, `open_notes()`, `mark_resolved(exercise_id, index|predicate)`. Create-if-absent; serialize with a small lock; `created_at` is server-stamped ISO 8601.
- **Write endpoint.** `POST /api/exercise-feedback` body `{ exerciseId, note }`. Validate `exerciseId` exists in `app.state.exercises` (404-style `{success:false,...}` if not); reject empty/whitespace `note` (400-style). Standard `{success, data, error}` wrapper. Optional read path `GET /api/exercise-feedback?exerciseId=` returning that Exercise's notes (drives the UI showing existing notes).
- **Content is loaded read-only at startup today** (in-memory `app.state.exercises`); this story does NOT change that — the Exercise corpus stays read-only; only the separate sidecar is written. No reload of the corpus is required.
- **Docker implication (OQ-8/OQ-9).** Writeback requires the content location be a **writable** bind-mount (not baked read-only). Whether `feedback.yaml` is committed or local-per-instance is OQ-9 — out of scope for this story (just write the file where content lives); note it.
- **Frontend affordance.** A lightweight "Flag / leave a note" control on the practice surface — reuse the shared runner-shell conventions (rev 7: `styles/ui.js`, etc.). Keep it subordinate to Submit/Next (don't compete with the primary study actions). A small textarea + submit calling `api.submitExerciseFeedback({exerciseId, note})`.

## Tasks / Subtasks

- [x] **Task 11.1.1 — Sidecar store** (`backend/app/feedback_store.py`, NEW)
  - [x] `add_note(exercise_id, note)` (server-stamp `created_at`, `resolved: false`), `notes_for(exercise_id)`, `open_notes()`, `mark_resolved(...)`. Read/write `exercises/feedback.yaml`, create-if-absent, with a small lock. Pure-ish stdlib + PyYAML (already a dep).
  - [x] `pytest` (temp file): add/list, open-only filter, mark-resolved, create-if-absent.
- [x] **Task 11.1.2 — Write endpoint** (`backend/app/main.py`, UPDATE)
  - [x] `POST /api/exercise-feedback {exerciseId, note}` → validate id exists + non-empty note → `feedback_store.add_note` → `{success, data, error}`. Optional `GET /api/exercise-feedback?exerciseId=`.
  - [x] `pytest`: success path, unknown id, empty/whitespace note, payload shape.
- [x] **Task 11.1.3 — Frontend API + affordance** (`frontend/src/api.js` + practice surfaces, UPDATE)
  - [x] `api.submitExerciseFeedback({exerciseId, note})` (+ optional `getExerciseFeedback`).
  - [x] "Flag / leave a note" control on the MCQ feedback panel (`MCQPractice.jsx` / `Feedback`) and the Code-Completion conclusion (`CodeCompletion.jsx`): textarea + submit; disable submit on empty; show a confirmation + error states.
  - [x] `vitest`: submitting calls the API with `{exerciseId, note}`; empty note is blocked; error surfaces.

### Review Findings (code review 2026-06-10)

Patches (unchecked = to apply):
- [x] [Review][Patch] Content loader scans `exercises/feedback.yaml` → a `missing_exercises_key` startup error on every boot (and a corrupt sidecar pollutes the content error log) [backend/app/content.py:115 + feedback_store path] *(blind+edge — highest value)*
- [x] [Review][Patch] Corrupt/malformed sidecar YAML crashes the store and returns HTTP 500 — `_load` has no try/except and the endpoint only catches `ValueError` [backend/app/feedback_store.py:49; backend/app/main.py]
- [x] [Review][Patch] Malformed sidecar *values* (scalar / non-dict / null entries) crash `open_notes`/`mark_resolved` and make `notes_for` return character-garbage [backend/app/feedback_store.py:82,99,113]
- [x] [Review][Patch] `_save` is a non-atomic truncate-rewrite → an interrupted write corrupts the whole file; use temp-file + `os.replace` [backend/app/feedback_store.py:_save]
- [x] [Review][Patch] `FeedbackNote` isn't reset on `exerciseId` change (no `key`/effect) → a typed draft or the "saved" banner can carry onto the next/another question [frontend/src/components/FeedbackNote.jsx; mount sites MCQPractice.jsx + CodeCompletion.jsx]
- [x] [Review][Patch] No length cap on the note (Pydantic field + textarea) → unbounded growth on full-file rewrite [backend/app/main.py ExerciseFeedbackRequest; frontend/src/components/FeedbackNote.jsx]
- [x] [Review][Patch] Test quality: add a corrupt/malformed-YAML test for the store; the `test_does_not_touch_other_files` assertion is a tautology under its dedicated-subdir fixture [backend/tests/test_feedback_store.py]

Deferred (real, NEW — lower priority for single-user/local scope; revisit if a real second writer appears):
- [x] [Review][Defer] Cross-process lost update — `threading.Lock` doesn't serialize the API process vs the `write-mcq` `python -c` invocation; atomic write (above) mitigates corruption but not lost updates [feedback_store.py] — deferred
- [x] [Review][Defer] `mark_resolved` blanket-resolves ALL open notes for an id, so a note filed between the author reading `open_notes()` and resolving is buried unreviewed [feedback_store.py:mark_resolved] — deferred

Dismissed (3): GET `/api/exercise-feedback` not validating an unknown id (optional read path; empty result is fine); `mark_resolved` signature lacks the AC's literal `index|predicate` (cosmetic — the resolve-all-for-id form is what 11.2 needs); `getExerciseFeedback` shipped untested (thin optional wrapper, not wired into the UI).

## Dev Notes

### NEW files
- `backend/app/feedback_store.py` (+ `backend/tests/test_feedback_store.py`)
- `exercises/feedback.yaml` is created at runtime (not committed as part of this story; OQ-9 decides commit-vs-local).

### UPDATE files
- `backend/app/main.py` — `POST /api/exercise-feedback` (+ optional GET).
- `frontend/src/api.js` — `submitExerciseFeedback` / `getExerciseFeedback`.
- `frontend/src/pages/MCQPractice.jsx` and `frontend/src/pages/CodeCompletion.jsx` — the note affordance (consider a shared `<FeedbackNote exerciseId />` component to avoid duplication, consistent with the rev-7 shared-shell direction).

### Preserve / do not touch
- The MCQ-grading `POST /api/feedback` and the SQLite attempt store (`store.py`) — unrelated; do not modify.
- Authored Exercise YAML files — never written by this feature.

### Dependencies / non-goals
- **Story 11.2** (`write-mcq` feedback-driven revision) consumes `open_notes()` / `mark_resolved` — out of scope here.
- No in-app editing of questions/options/config; no feedback moderation/triage UI; no cross-instance aggregation.

### References
- [Source: PRD §4.9 FR-32; §5 narrowed non-goal; §8 OQ-9; §9 assumptions]
- [Source: addendum §I — sidecar schema, endpoint, feedback_store.py, docker implication]
- [Source: decision-log #47–53]
- [Source: `backend/app/main.py`] — existing `{success,data,error}` wrapper + filter/validation patterns to mirror; `POST /api/feedback` (MCQ grading) to NOT collide with.
- [Source: rev-7 shared shell — `styles/ui.js`, component conventions]

## Dev Agent Record

### Agent Model Used
claude-opus-4-8 (dev-story workflow, 2026-06-10).

### Completion Notes List
- New `backend/app/feedback_store.py`: `add_note` (server-stamped `created_at`, `resolved:false`; rejects empty/whitespace), `notes_for`, `open_notes` (unresolved-only), `mark_resolved` (idempotent). Read/modify/write `exercises/feedback.yaml` under a thread lock, create-if-absent. Authored Exercise files never touched.
- New `POST /api/exercise-feedback {exerciseId, note}` + `GET /api/exercise-feedback?exerciseId=` in `main.py` — validates the id exists in `app.state.exercises`, rejects empty notes, standard string-error `{success,data,error}` wrapper. Distinct from the MCQ-grading `POST /api/feedback` and the SQLite store.
- Frontend: `api.submitExerciseFeedback` / `getExerciseFeedback`; shared `FeedbackNote.jsx` ("Flag a problem with this question" → textarea → submit; disabled on empty; saved/​error states), mounted in the MCQ feedback panel and the Code-Completion conclusion.
- Test isolation: added an autouse `isolated_feedback_store` conftest fixture (mirrors the SQLite isolation) so no test writes the real sidecar.
- **OQ-9 left open:** `exercises/feedback.yaml` is written at runtime; NOT gitignored and NOT committed by this story — commit-vs-local is the user's call. Flag for Epic 11 close.
- Tests: backend 284 (incl. 10 store + 5 endpoint), frontend 186 (incl. 4 FeedbackNote), ruff + eslint clean.

### File List
- backend/app/feedback_store.py (NEW)
- backend/tests/test_feedback_store.py (NEW)
- backend/tests/test_exercise_feedback.py (NEW)
- backend/tests/conftest.py (M — autouse isolated_feedback_store fixture)
- backend/app/main.py (M — ExerciseFeedbackRequest + POST/GET /api/exercise-feedback; import feedback_store)
- frontend/src/api.js (M — submitExerciseFeedback / getExerciseFeedback)
- frontend/src/components/FeedbackNote.jsx (NEW)
- frontend/src/components/FeedbackNote.test.jsx (NEW)
- frontend/src/pages/MCQPractice.jsx (M — mount FeedbackNote after feedback)
- frontend/src/pages/CodeCompletion.jsx (M — mount FeedbackNote in the conclusion)

### Change Log
- 2026-06-10 — Implemented in-app question feedback → sidecar `exercises/feedback.yaml` (backend store + endpoint + frontend affordance) with tests; authored Exercise files untouched (Story 11.1).
- 2026-06-10 — Code review (bmad-code-review): applied 7 patches — content loader now skips `feedback.yaml`; `_load` raises a clear `FeedbackStoreError` on corrupt YAML (endpoints return a friendly failure, no 500); malformed sidecar values are tolerated; `_save` is atomic (temp + `os.replace`); `FeedbackNote` is keyed by `exerciseId` (resets per question); note length capped (`MAX_NOTE_LENGTH`/`maxLength`); added robustness tests + fixed the tautology test. 2 findings deferred (deferred-work.md), 3 dismissed. Suites green (backend 289 / frontend 187), lint clean. Status → done.
