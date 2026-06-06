---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.6: Summary Review & Replay

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-6-summary-review-and-replay

## Story Statement

As a **student**,
I want **to review the questions I missed and replay sets**,
So that **I can target my weak spots and re-drill**.

## Acceptance Criteria

(from epics.md, Story 6.6 — UX-DR4/10/11)

**Given** I reach the Summary (complete or partial)
**When** the Summary renders in `frontend/src/pages/Summary.jsx`
**Then** a Review-incorrect list shows each missed question with its correct option and explanation (from the retained feedback, Story 6.3)
**And** "Practice these N again" starts a fresh session of just the missed exercises via `POST /api/sessions {exerciseIds}` (Story 6.2)
**And** "Restart this session" replays the full exercise set fresh via the same endpoint
**And** a partial Summary surfaces answered and skipped counts
**And** the existing "Start a new session" action is retained
**And** tests cover review-incorrect, practice-again, restart, and partial counts

## Architecture Context

- **Replay endpoint (architecture rev 3, gap G2):** `POST /api/sessions` builds a session from an explicit `{ exerciseIds: [...] }` set. Same response shape as `GET /api/sessions` (flag-less Displayed Options, randomized order), with **freshly sampled/shuffled options and re-randomized order** so replays keep FR-20/21 freshness; unknown ids are dropped (logged), not fatal (architecture.md lines 352, 854; Story 6.2). Both "Restart this session" and "Practice these N again" use this one endpoint — the only difference is the id set passed.
- **Retained feedback (architecture rev 3, gap G3):** with grading server-side and `correct` flags stripped from the session payload, the client persists each `POST /api/feedback` response in `feedback[exerciseId]` as `{ correct, correctOptionId, explanation, references }`. The Review-incorrect list reads this retained feedback directly — **no re-grade, no re-POST** (architecture.md line 292; Story 6.3). This story is read-only over that state.
- **Review-incorrect list (EXPERIENCE.md, Component Patterns, line 65):** an expandable list of the questions answered incorrectly, each showing the question, the correct option, and the explanation. A **"Practice these {n} again"** action starts a fresh session containing only those exercises.
- **Partial Summary / state patterns (EXPERIENCE.md lines 50, 52, 77, 86):**
  - Ended-early → Summary computed over the **answered subset**; skipped/unanswered are excluded from the score denominator shown but **surfaced as counts**.
  - Skipped state label in summary: **"Skipped"** (neutral, not "failed").
  - All-skipped edge: Summary shows 0 answered with an encouraging "Nothing graded yet — jump back in?" plus a Start action.
  - Replay labels are fixed: Restart = **"Restart this session"**; Practice-again = **"Practice these {n} again"**.
- **UX-DR coverage (epics.md lines 166, 171):** UX-DR4/UX-DR10 (Restart-same / Practice-incorrect-again via `POST /api/sessions {exerciseIds}`); UX-DR10/UX-DR11 (Review-incorrect + quit-to-partial-Summary).
- **Dependencies:** Story 6.2 (the `POST /api/sessions {exerciseIds}` endpoint) and Story 6.3 (retained feedback + per-question `unanswered | answered | skipped` accounting and the `endToSummary` / partial-summary state). This story consumes both; if either is incomplete the corresponding ACs (replay, partial counts) cannot land. Note and coordinate.

## Tasks/Subtasks

- [ ] Task 6.6.1: Extend results computation for partial Summary counts
  - [ ] In `computeResults(exercises, feedback)` (or alongside it), derive `answered`, `correct`, `skipped`, and `unanswered` counts so the Summary can surface answered + skipped totals (AC: partial counts)
  - [ ] Keep the existing `correct/total` and per-domain `byDomain` breakdown working unchanged; score denominator shown is the answered subset (EXPERIENCE.md ended-early)
  - [ ] Read skipped/unanswered per-question state from the Story 6.3 session state (do not infer "incorrect" from "unanswered")

- [ ] Task 6.6.2: Build the Review-incorrect list (read-only, from retained feedback)
  - [ ] Render a list of exercises where `feedback[ex.exerciseId].correct === false`
  - [ ] For each, show the question text, the correct option (resolve `correctOptionId` against the exercise's `displayedOptions`), and the `explanation` from retained feedback — no API call, no re-grade
  - [ ] Make the list expandable per Component Patterns (EXPERIENCE.md line 65); empty state when nothing was missed

- [ ] Task 6.6.3: Add the replay actions (Restart / Practice-again)
  - [ ] "Restart this session" → replay the full exercise-id set (all `exercises[].exerciseId`)
  - [ ] "Practice these {n} again" → replay only the missed exercise-id set; label uses the live count `n` and is hidden/disabled when `n === 0`
  - [ ] Both call the api wrapper from Task 6.6.4, then start a fresh session via `startSession(...)` from `SessionContext`
  - [ ] Retain the existing "Start a new session" button wired to `reset` (AC: existing action retained)
  - [ ] Handle the all-skipped / 0-answered partial Summary with the encouraging copy + Start action (EXPERIENCE.md line 86)

- [ ] Task 6.6.4: Wire the replay API call in `frontend/src/api.js`
  - [ ] Add `postSessionByIds(exerciseIds)` (replay) calling `apiRequest('/api/sessions', { method: 'POST', body: JSON.stringify({ exerciseIds }) })`
  - [ ] Mirror `getSession` result handling: throw `APIError` when `!result.success`; guard `Array.isArray(result.data) ? result.data : []`
  - [ ] Returns the same session-entry shape as `getSession` so `startSession` consumes it directly

- [ ] Task 6.6.5: Tests (vitest) — `frontend/src/pages/Summary.test.jsx`
  - [ ] Review-incorrect: renders only missed questions with their correct option + explanation from retained feedback (no fetch)
  - [ ] Practice-again: clicking calls `postSessionByIds` with exactly the missed ids and starts a session; label shows correct `n`; hidden/disabled when none missed
  - [ ] Restart: clicking calls `postSessionByIds` with the full id set and starts a session
  - [ ] Partial counts: a partial Summary surfaces answered + skipped counts; score denominator = answered subset; all-skipped shows the 0-answered state
  - [ ] "Start a new session" still calls `reset`

## Dev Notes

**Current behavior (baseline 10824eb).**
`frontend/src/pages/Summary.jsx` exports `computeResults(exercises, feedback)` → `{ correct, answered, total, byDomain }` (only answered exercises count toward per-domain totals; `total` is `exercises.length`). The component reads `{ exercises, feedback, reset }` from `useSession()`, shows a `correct/total` headline + percentage and a per-domain breakdown, and renders a single **"Start a new session"** button wired to `reset`. There is currently no review list and no replay.

`frontend/src/context/SessionContext.jsx` already retains feedback: `SUBMIT_SUCCESS` stores the full `{ correct, correctOptionId, explanation, references }` in `feedback[exerciseId]`, and `startSession(exercises)` dispatches `START_SESSION` to begin a fresh practice session from a session-entry list. `reset()` returns to Start. (Story 6.3 adds the per-question `unanswered | answered | skipped` accounting and `endToSummary`; this story reads that state — coordinate if 6.3 is not yet merged.)

`frontend/src/api.js` has `getSession({ domain, difficulty })` (GET) and `submitFeedback(...)`; it has **no** POST-by-ids call yet — that is added in Task 6.6.4 and depends on the Story 6.2 endpoint.

**How review-incorrect reads retained feedback.** Filter `exercises` by `feedback[ex.exerciseId]?.correct === false`. The correct option text is resolved by matching `feedback[ex.exerciseId].correctOptionId` to an entry in that exercise's `displayedOptions` (`{ id, text }`). The explanation comes straight from `feedback[ex.exerciseId].explanation`. No grading call is made — the data is already in state from Story 6.3.

**Replay calls `POST /api/sessions {exerciseIds}`.** Both replay actions go through the same endpoint (architecture rev 3, G2). Restart passes every `exerciseId` in the session; Practice-again passes only the missed ids. The backend re-samples/re-shuffles options and re-randomizes order, so replays are fresh (FR-20/21) — the client must not reuse its old flag-less options. Feed the returned list straight into `startSession(...)`.

**Preserve.** Keep `computeResults`'s existing signature/return fields and the per-domain breakdown; keep the "Start a new session" → `reset` button; keep the session payload flag-less assumption (Summary never sees answer keys except via retained feedback). Extend, do not rewrite.

**NEW files:** none.
**UPDATE files:**
- `frontend/src/pages/Summary.jsx` — partial counts, Review-incorrect list, Restart / Practice-again actions (Tasks 6.6.1–6.6.3)
- `frontend/src/api.js` — `postSessionByIds(exerciseIds)` (Task 6.6.4)
- `frontend/src/pages/Summary.test.jsx` — review/replay/partial tests (Task 6.6.5)

(`frontend/src/context/SessionContext.jsx` is consumed read-only here — `startSession`, `reset`, retained `feedback`; any reducer changes belong to Story 6.3.)

**Dependencies:** Story 6.2 (replay endpoint) and Story 6.3 (retained feedback + partial/skip accounting). Both are prerequisites for the replay and partial-count ACs respectively.

## References

- `_bmad-output/planning-artifacts/epics.md` — Story 6.6 (lines 794–809); Story 6.2 (lines 720–734); Story 6.3 (lines 738–753); UX-DR coverage map (lines 166, 171)
- `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` — Review-incorrect list (line 65); replay labels (lines 50, 52); ended-early / partial + all-skipped states (lines 77, 86); resolved replay note (line 122)
- `_bmad-output/planning-artifacts/architecture.md` — rev 3 changelog (line 10); retained feedback G3 (line 292); new actions incl. replay (line 293); `POST /api/sessions {exerciseIds}` (lines 352, 854)
- Code: `frontend/src/pages/Summary.jsx`, `frontend/src/api.js`, `frontend/src/context/SessionContext.jsx`, `frontend/src/pages/Summary.test.jsx`

## Dev Agent Record

### Implementation Plan

(To be filled in as implementation progresses)

### Subtasks Completed

(To be filled in as implementation progresses)

### Completion Notes

(To be filled in upon task completion)

## File List

(Files will be listed here upon completion)

## Change Log

- Initial story creation — 2026-06-06

## Status

ready-for-dev
