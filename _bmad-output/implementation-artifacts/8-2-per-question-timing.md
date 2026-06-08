---
status: ready-for-dev
baseline_commit: 4cce825
---

# Story 8.2: Per-Question Timing

**Epic:** 8 - Timed Practice / Mock Exam
**Story Key:** 8-2-per-question-timing

## Story Statement

As a **the app**,
I want **to measure how long each answer takes**,
So that **timing feeds the stats and the timed experience**.

This is the **frontend** half of FR-28. The backend hook already exists: **Story 7.2** made
`POST /api/feedback` accept an optional `timeTakenMs` and persist it to the SQLite attempt store. The
confirmed gap from the Epic 7 review is that the frontend **never sends `timeTakenMs`** — it currently
posts only `{exerciseId, displayedOptionIds, selectedId, type:'mcq'}`. This story measures per-question
elapsed time on the client and threads it through `submitAnswer` → `submitFeedback` as `timeTakenMs`. No
backend change is in scope.

## Acceptance Criteria

**Given** an MCQ is presented
**When** the user submits
**Then** the client measures elapsed time for that question and sends `timeTakenMs` with `POST /api/feedback` (recorded by Story 7.2)
**And** timing is per-question (reset on advance), not whole-session
**And** vitest tests assert `submitFeedback` is called with a numeric `timeTakenMs`

## Architecture Context

From `architecture.md` (rev 4):

- **Timer/timing lives on the frontend.** The client owns the clock; the backend is a passive consumer.
  Per-question elapsed time is computed in the browser and POSTed alongside the answer.
- **Contract:** `POST /api/feedback {exerciseId, displayedOptionIds, selectedId, type, timeTakenMs?}`.
  `timeTakenMs` is **optional** (nullable) — grading must still work when it is omitted, so this story is
  purely additive and the field is appended to the existing request body.

From **PRD §4.6 FR-28** and **addendum §E**: the app measures how long each answer takes so timing can
feed practice stats and the timed/mock experience. Timing is **per-question** (the clock starts when a
question is presented and stops when that question is submitted), **not** a single whole-session stopwatch.

**Backend consumer — already done (do NOT change):** `backend/app/main.py`
- `FeedbackRequest.timeTakenMs: int | None = Field(default=None, ge=0, ...)` (lines ~452–456) — accepts a
  non-negative integer or null.
- `post_feedback` passes it through as `store.record_attempt(..., time_taken_ms=request.timeTakenMs)`
  (lines ~506–513), best-effort. This story's job is simply to start *supplying* a value.

## Tasks/Subtasks

- [ ] **Task 8.2.1 — Send `timeTakenMs` from the API client** (`frontend/src/api.js`)
  - [ ] Extend `submitFeedback` to accept an optional `timeTakenMs` arg: `submitFeedback({ exerciseId, displayedOptionIds, selectedId, timeTakenMs })`.
  - [ ] Include it in the POST body alongside the existing `{exerciseId, displayedOptionIds, selectedId, type:'mcq'}`.
        Only send it when it is a finite number (omit/null otherwise) so the optional/nullable contract holds and untracked submits stay unchanged.
  - [ ] Update the JSDoc to document the new `timeTakenMs` (milliseconds, optional, FR-28).

- [ ] **Task 8.2.2 — Measure per-question elapsed time and reset on advance** (`frontend/src/pages/MCQPractice.jsx`)
  - [ ] Record a start timestamp when a question is **presented** (i.e. when `currentExercise.exerciseId` changes) using a high-resolution monotonic clock (`performance.now()`), stored in a ref.
  - [ ] On **submit**, compute `elapsedMs = Math.round(now - start)` (floor at 0) and pass it into `submitAnswer`.
  - [ ] **Reset on advance:** when the displayed question changes (Next/Skip/Back), the start timestamp re-arms for the new question, so timing is strictly per-question, never cumulative across the session.
  - [ ] Do not change correctness/feedback rendering or any keyboard/submit gating — timing is orthogonal.

- [ ] **Task 8.2.3 — Thread `timeTakenMs` through `submitAnswer`** (`frontend/src/context/SessionContext.jsx`)
  - [ ] Let `submitAnswer(exerciseId, timeTakenMs)` accept the optional elapsed-ms value from the page.
  - [ ] Pass it into the `submitFeedback({ exerciseId, displayedOptionIds, selectedId, timeTakenMs })` call.
  - [ ] Preserve the existing re-submit / in-flight guard (`if (s.feedback[exerciseId] || s.submitting[exerciseId]) return`) and the no-selection early return — answers stay final and timing never re-grades.

- [ ] **Task 8.2.4 — Tests (co-located vitest)**
  - [ ] In the API client / context suite, assert `submitFeedback` (mocked) is called with a **numeric** `timeTakenMs` (`expect.any(Number)`, value `>= 0`) when an answer is submitted.
  - [ ] Assert that timing is **per-question**: after advancing, a fresh question's submit reports its own elapsed time (the value re-arms / is not the accumulated session total).
  - [ ] Assert untracked/edge behavior still grades: when no `timeTakenMs` is supplied, `submitFeedback` is still called and the body omits/nulls the field (back-compat with the optional contract).

## Dev Notes

**Files to UPDATE (do not create new source files):**

- `frontend/src/api.js` — add optional `timeTakenMs` to `submitFeedback`'s args + POST body.
- `frontend/src/context/SessionContext.jsx` — let `submitAnswer` accept and forward `timeTakenMs`.
- `frontend/src/pages/MCQPractice.jsx` — start timing when a question is presented, stop on submit, reset on advance.
- Co-located vitest suites (already exist next to the source): `frontend/src/api.test.*` (or the context suite
  `frontend/src/context/SessionContext.test.jsx` / `frontend/src/pages/MCQPractice.test.jsx`) — add the assertions in Task 8.2.4 to whichever already mocks `submitFeedback`.

**Current behavior (baseline) — preserve all of it:**

- `submitFeedback` currently posts exactly `{exerciseId, displayedOptionIds, selectedId, type:'mcq'}` — **no `timeTakenMs`** (the gap this story closes). Append the field; do not reshape the existing keys.
- `SessionContext.submitAnswer(exerciseId)` is async, reads fresh state via `stateRef`, guards re-submit/in-flight and no-selection, then dispatches `SUBMIT_START` → `submitFeedback` → `SUBMIT_SUCCESS`/`SUBMIT_ERROR`. Keep this flow intact; only add the extra arg.
- `MCQPractice.jsx` calls `submitAnswer(exercise.exerciseId)` from both the Submit button and the Enter-key shortcut — **both call sites** must pass the elapsed ms.

**Backend hook already exists — Story 7.2 (done):** `FeedbackRequest.timeTakenMs` (`ge=0`, nullable) and
`store.record_attempt(time_taken_ms=...)` in `backend/app/main.py` already accept and persist the value.
Cite as the consumer; **do not change the backend.**

**Per-question, not whole-session:** the start clock re-arms on every question change. Do not introduce a
single session-level stopwatch (that is Story 8.1's countdown, a separate concern). Use `performance.now()`
(monotonic) rather than `Date.now()` so clock adjustments can't produce a negative/garbage duration; floor at 0.

**Testing:** **vitest** is configured (Story 1.5) and tests are **co-located** with the source. Mock
`../api` (`vi.mock`) and assert the `submitFeedback` call shape with `expect.objectContaining({ timeTakenMs: expect.any(Number) })`. Run with the frontend test runner (`npm run test` in `frontend/`).

## References

- `_bmad-output/planning-artifacts/epics.md` — Epic 8 (Timed Practice / Mock Exam), **Story 8.2: Per-Question Timing** (lines ~988–1000).
- `_bmad-output/planning-artifacts/architecture.md` (rev 4) — timer/timing is frontend; `POST /api/feedback {..., timeTakenMs?}` contract.
- `_bmad-output/planning-artifacts/PRD.md` — **§4.6 FR-28** (measure per-answer time to feed stats / timed experience); addendum **§E**.
- `frontend/src/api.js` — `submitFeedback` (lines ~162–176); currently sends no `timeTakenMs` (the gap to close).
- `frontend/src/context/SessionContext.jsx` — async `submitAnswer` (lines ~178–206) calling `submitFeedback`; where to thread the elapsed ms.
- `frontend/src/pages/MCQPractice.jsx` — `submitAnswer(exercise.exerciseId)` call sites: Submit button (line ~376) and Enter shortcut (line ~166); where to start/stop/reset the per-question clock.
- `backend/app/main.py` — **consumer, already done (Story 7.2):** `FeedbackRequest.timeTakenMs` (lines ~452–456) and `store.record_attempt(time_taken_ms=...)` (lines ~506–513).

**Dependency:** backend record hook — **Story 7.2 (done)**. No further backend work required.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (main loop).

### Completion Notes List

- `api.js`: `submitFeedback` now accepts an optional `timeTakenMs` and appends it to the POST body **only when `Number.isFinite(timeTakenMs)`** — untracked submits stay byte-for-byte unchanged and the backend's nullable contract holds. Existing keys (`exerciseId`, `displayedOptionIds`, `selectedId`, `type:'mcq'`) unchanged.
- `SessionContext.jsx`: `submitAnswer(exerciseId, timeTakenMs?)` forwards the elapsed ms into `submitFeedback`. Re-submit/in-flight guard and no-selection early return preserved.
- `MCQPractice.jsx`: per-question clock via `performance.now()` stored in `questionStartRef`, re-armed by a `useEffect` keyed on `currentExercise.exerciseId` (strictly per-question, never cumulative). New `submitWithTiming(exerciseId)` helper computes `Math.max(0, Math.round(now - start))` and is used at **both** submit call sites (Submit button + Enter shortcut). Correctness/feedback rendering and keyboard gating untouched.
- Backend untouched (Story 7.2 already accepts & persists `timeTakenMs`, `ge=0`, nullable).
- Tests: new `api.test.jsx` (3 — sends when finite, omits when absent, omits when NaN); extended `MCQPractice.test.jsx` (numeric `timeTakenMs >= 0` on submit; per-question re-arm on advance; updated the existing grade assertion to `objectContaining` + `timeTakenMs: expect.any(Number)` to reflect the new contract).
- Verified: frontend `vitest run` green; `npm run lint` clean.

### File List

- NEW: `frontend/src/api.test.jsx`
- UPDATE: `frontend/src/api.js`, `frontend/src/context/SessionContext.jsx`, `frontend/src/pages/MCQPractice.jsx`, `frontend/src/pages/MCQPractice.test.jsx`
