---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.3: Session State — Feedback Retention, Back, Skip, End-to-Summary

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-3-session-state-feedback-retention-back-skip

## Story Statement

As a **the app**,
I want **the session store to retain each feedback response and support back/skip/early-end**,
So that **revisit, review, and partial results work without re-grading**.

This story closes gap **G3** (frontend feedback-retention + new reducer actions/states) and is a
**dependency for Stories 6.4, 6.5, and 6.6** — they wire UI controls (Exit-confirm/End, progress bar,
Back/Skip controls, keyboard shortcuts, Review-incorrect/Replay) to the reducer surface added here.
This story is **state/reducer only** — it does not add or change any UI controls in `MCQPractice.jsx`
(that work belongs to 6.4/6.5/6.6).

## Acceptance Criteria

**Given** the session reducer in `frontend/src/context/SessionContext.jsx`
**When** an answer is submitted
**Then** `feedback[exerciseId]` stores the full `{correct, correctOptionId, explanation, references}` response (already true in Epic 5 — preserved and asserted)
**And** a `prev` action moves back to an earlier question shown read-only (no re-submit, no re-POST — submitted answers are final)
**And** a `skip` action advances without grading and records the question as *unanswered* (not incorrect)
**And** an `endToSummary` action ends the session early and computes the Summary over the answered subset
**And** per-question state is tracked as `unanswered | answered | skipped` and session state as `active | ended-early | completed`
**And** a furthest-reached pointer prevents Back/Next from overrunning the visited range
**And** tests cover retention, back read-only, skip accounting, and partial summary

## Architecture Context

From `architecture.md` (rev 3) **Decision: State Management → QoL additions (UX rev — EXPERIENCE.md)**:

- **Feedback retention (G3):** With grading server-side and `correct` flags stripped from option payloads, the
  client must persist each `POST /api/feedback` response in `feedback[exerciseId]` as
  `{ correct, correctOptionId, explanation, references }`. This powers **Back/Previous read-only revisit** and the
  **Review-incorrect** list (Story 6.6) with no re-grade. Revisiting a submitted question must **not** re-POST —
  answers are final. (The existing Epic-5 `submitAnswer` already stores the full response and already guards against
  re-submit; this story preserves that and adds the navigation/lifecycle around it.)
- **New actions:** `prev` (decrement index; revisit read-only), `skip` (advance without grading; records the
  question as *unanswered*, not incorrect), `endToSummary` (exit Practice early → Summary over the answered subset).
  An `exit`/`reset` to Start already exists (`reset`). Replay actions (`restartSession` / `practiceIncorrect(ids)`)
  are **out of scope here** — they land in Story 6.6.
- **Per-question state:** `unanswered | answered | skipped`, plus a **furthest-reached pointer** so Back/Next can't
  overrun. Session-level: `active | ended-early | completed`.

From `EXPERIENCE.md` **State Patterns** (UX-DR6/8/11):

- **Back / Previous** revisits already-visited questions. An **answered** question shown via Back is **read-only**:
  selection, correctness, and explanation are displayed; options are disabled. Forward returns to the furthest-reached
  question. Back is hidden/disabled on the first question.
- **Skip** advances without grading; the question is recorded as **unanswered** (not incorrect) and remains reachable
  via Back. Available only before submit. `[ASSUMPTION accepted]` Skip leaves a question answerable on revisit *within
  the active session*; once the session ends it's frozen as unanswered.
- **Session states:** *Active* → Practice. *Ended-early* → user chose *See results* → Summary computed over the
  **answered subset** (skipped/unanswered excluded from the scored denominator, but surfaced as a count). *Completed*
  → advanced past the last question → full Summary.
- **Empty/edge:** All questions skipped then End → Summary shows 0 answered (Story 6.6 renders the encouraging
  empty state; this story must make `computeResults` over the answered subset coherent — it already is).

## Tasks/Subtasks

- [ ] **Task 6.3.1 — Extend reducer state shape** (`frontend/src/context/SessionContext.jsx`)
  - [ ] Add `sessionState: 'active'` to `initialState` (values: `active | ended-early | completed`).
  - [ ] Add `questionState: {}` keyed by `exerciseId` (values: `unanswered | answered | skipped`); treat absent as `unanswered`.
  - [ ] Add `furthestIndex: 0` to track the furthest-reached question; never decrement it.
  - [ ] Update the state-shape JSDoc header comment to document the new fields.

- [ ] **Task 6.3.2 — Set `questionState: 'answered'` on grading**
  - [ ] In `SUBMIT_SUCCESS`, set `questionState[exerciseId] = 'answered'` alongside the existing `feedback` write.
  - [ ] Do **not** touch `questionState` on `SUBMIT_ERROR` (stays `unanswered`, retry still allowed).

- [ ] **Task 6.3.3 — Add `PREV` action (read-only back)**
  - [ ] `PREV` decrements `currentIndex` (floor 0); no-op at index 0.
  - [ ] Does **not** change `feedback`, `selectedAnswers`, `submitting`, or `furthestIndex`.
  - [ ] Read-only enforcement (no re-submit / no re-POST) is preserved by the existing `submitAnswer` guard
        (`if (s.feedback[exerciseId] || s.submitting[exerciseId]) return`) — no change needed; assert it in tests.

- [ ] **Task 6.3.4 — Add `SKIP` action**
  - [ ] Only records a skip when the current question is not already answered (no `feedback[exerciseId]`).
  - [ ] Sets `questionState[exerciseId] = 'skipped'`; does **not** write `feedback` and does **not** call the API.
  - [ ] Advances like `NEXT`: if last question → `sessionState: 'completed'`, `view: 'summary'`; else `currentIndex + 1` and bump `furthestIndex`.

- [ ] **Task 6.3.5 — Update `NEXT` for furthest-reached + completed**
  - [ ] On advancing, set `furthestIndex = max(furthestIndex, currentIndex + 1)`.
  - [ ] On last question, set `sessionState: 'completed'` (in addition to `view: 'summary'`).

- [ ] **Task 6.3.6 — Add `END_TO_SUMMARY` action**
  - [ ] Sets `sessionState: 'ended-early'` and `view: 'summary'`; preserves `feedback`/`questionState` so Summary scores the answered subset.

- [ ] **Task 6.3.7 — Expose new actions from the provider** (`useMemo` value)
  - [ ] `prev: () => dispatch({ type: 'PREV' })`
  - [ ] `skip: () => dispatch({ type: 'SKIP', exerciseId: currentExercise?.exerciseId })`
  - [ ] `endToSummary: () => dispatch({ type: 'END_TO_SUMMARY' })`
  - [ ] Continue to spread `...state` so `sessionState`, `questionState`, `furthestIndex` are readable by consumers (6.4/6.5/6.6).

- [ ] **Task 6.3.8 — Confirm `RESET` and `START_SESSION` reset the new fields**
  - [ ] Both derive from `initialState`, so `sessionState`/`questionState`/`furthestIndex` reset automatically — add a regression test rather than new code.

- [ ] **Task 6.3.9 — Tests (co-located vitest)** — extend `frontend/src/context/SessionContext.test.jsx`
  - [ ] **Retention:** after a successful submit, `feedback[id]` equals the full `{correct, correctOptionId, explanation, references}` and survives `prev`/`next` navigation.
  - [ ] **Back read-only / no re-POST:** after submit, `prev` then calling `submitAnswer` again does **not** call `api.submitFeedback` a second time and does not change `feedback`.
  - [ ] **Skip accounting:** `skip` advances, sets `questionState[id] === 'skipped'`, writes no `feedback`, and calls no API; skipped count is excluded from the scored total.
  - [ ] **Partial summary:** with a mix of answered + skipped, `END_TO_SUMMARY` sets `sessionState: 'ended-early'`, `view: 'summary'`, and `computeResults` (Summary) totals only the answered subset.
  - [ ] **Furthest-reached:** `prev` does not lower `furthestIndex`; `next`/`skip` raise it.
  - [ ] **Lifecycle:** advancing past the last question sets `sessionState: 'completed'`; `reset` returns all fields to `initialState`.

## Dev Notes

**Files to UPDATE (do not create new source files):**

- `frontend/src/context/SessionContext.jsx` — the only source file with real changes (reducer + provider actions).
- `frontend/src/context/SessionContext.test.jsx` — extend the existing co-located vitest suite (already mocks `../api`).
- `frontend/src/pages/Summary.jsx` — **read-only reference, likely no change.** `computeResults` already scores only
  answered exercises (`if (!result) continue`), so partial Summary already works. Only touch it if a test reveals a gap.
- `frontend/src/pages/MCQPractice.jsx` — **no change in this story.** UI wiring of Back/Skip/End is Stories 6.4/6.5/6.6.

**Current reducer shape (Epic 5, baseline) — preserve all of it:**

- State: `{ view, exercises, currentIndex, selectedAnswers, submitting, submitErrors, feedback }`
  with `view: 'select' | 'practice' | 'summary'`.
- Actions: `START_SESSION`, `SET_SELECTION`, `SUBMIT_START`, `SUBMIT_SUCCESS`, `SUBMIT_ERROR`, `NEXT`, `RESET`.
- Async `submitAnswer(exerciseId)` already: (a) guards against re-submit and in-flight submits
  (`if (s.feedback[exerciseId] || s.submitting[exerciseId]) return`), and (b) on success stores the **full**
  feedback response in `feedback[exerciseId]` via `SUBMIT_SUCCESS`. **This is the no-re-POST / answers-are-final
  guarantee** — Back revisit relies on it; do not weaken it.
- Provider uses `useReducer` + a `stateRef` (so `submitAnswer` reads fresh state without stale closures) and exposes
  derived `currentExercise` / `total` plus actions through a `useMemo`. Add new actions inside that same `useMemo`.

**What this story adds (exactly):**

- State fields: `sessionState` (`active|ended-early|completed`), `questionState` (`{id: unanswered|answered|skipped}`), `furthestIndex`.
- Actions: `PREV`, `SKIP`, `END_TO_SUMMARY`; plus `NEXT`/`SUBMIT_SUCCESS` augmented with `furthestIndex`/`sessionState`/`questionState`.
- Provider methods: `prev`, `skip`, `endToSummary`.

**Preserve / do not regress:** existing `view` transitions, the re-submit guard, full-feedback retention, error/retry flow,
and `RESET`/`START_SESSION` resetting from `initialState`.

**Testing:** Vitest is configured (Story 1.5). Tests are **co-located** with the source (`SessionContext.test.jsx` already
exists next to `SessionContext.jsx`); use `renderHook` + `act` from `@testing-library/react` and `vi.mock('../api')`,
matching the established pattern in that file. Run with the frontend test runner (e.g. `npm run test` in `frontend/`).

## References

- `_bmad-output/planning-artifacts/epics.md` — Epic 6 (Session Control & Study QoL), **Story 6.3** (lines ~738–753);
  UX-DR Coverage Map UX-DR6/8/11 (lines ~165–172); dependents Stories 6.4 (line ~768), 6.5 (line ~786), 6.6 (line ~804).
- `_bmad-output/planning-artifacts/architecture.md` (rev 3) — **Decision: State Management** (line ~274) and the
  **QoL additions (UX rev)** block (lines ~291–294: feedback retention G3, new actions, per-question/session states).
- `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` —
  Back/Skip primitives (lines ~63–64), **State Patterns** per-question/session states (lines ~67–87), Skip label/assumption
  (lines ~50, ~123), keyboard Back/Next/Skip semantics (line ~94).
- `frontend/src/context/SessionContext.jsx` — current reducer being extended.
- `frontend/src/context/SessionContext.test.jsx` — co-located test suite to extend.
- `frontend/src/pages/Summary.jsx` — `computeResults` (already partial-aware).
- `frontend/src/pages/MCQPractice.jsx` — consumer (not changed here).

## Dev Agent Record

_(empty — to be filled by the implementing agent)_
