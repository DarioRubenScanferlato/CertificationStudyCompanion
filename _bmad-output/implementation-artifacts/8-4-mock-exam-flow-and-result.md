---
status: ready-for-dev
baseline_commit: 4cce825
---

# Story 8.4: Mock-Exam Flow & Result (Frontend)

**Epic:** 8 - Timed Practice / Mock Exam
**Story Key:** 8-4-mock-exam-flow-and-result

## Story Statement

As a **student**,
I want **to take a timed mock exam end-to-end and see an exam-style score**,
So that **I get a realistic readiness check**.

(FR-27 — PRD §4.6.)

## Acceptance Criteria

(from epics.md, Story 8.4)

**Given** the mock-exam builder (8.3) and timer (8.1)
**When** I choose "Mock Exam" for an Exam on the Start screen
**Then** `frontend/src/pages/MockExam.jsx` (or a SessionSelect mode) starts the domain-weighted set under the exam's countdown, auto-submitting at zero
**And** at the end an exam-style result shows overall score vs the ~70% bar plus the per-Domain breakdown (reusing Story 6.6 / Story 7 stats)
**And** the mock run records attempts like any session (Story 7.2)
**And** vitest tests cover starting a mock, the countdown/auto-submit, and the result screen

## Architecture Context

- **Mock-Exam builder is backend, this story is the frontend consumer (architecture rev 4, AR-18 / Decision lines 505–509; epics.md Story 8.3 lines 1004–1019):** `GET /api/sessions?mode=mock&exam=...` assembles a **domain-weighted, full-length** set scoped to one Exam (Associate ≈45Q/90min, Professional ≈59Q/120min per addendum §C weights), **ignores unseen-first** (a mock must be representative, may repeat seen), never mixes exams, and **stamps the exam `durationMinutes`** in the response. The response otherwise matches the standard session shape — flag-less Displayed Options (`{ id, text }×4`), `{success, data, error}` wrapper. This story calls that endpoint, runs the returned set under a countdown for `durationMinutes`, and renders an exam-style result at the end.
- **Timer is frontend (architecture rev 4, lines 509, 932; FR-26/FR-28):** the countdown, auto-submit-at-zero, and per-question elapsed timing live in React — no server-side clock. The mock countdown uses the exam's real duration (`durationMinutes` from the builder) and **auto-submits at zero** by ending the session to the (partial) Summary via `endToSummary`. The same `Timer`/`Countdown` component built in Story 8.1 backs both the optional session timer and Mock-Exam mode.
- **SessionSelect affordance (architecture rev 4, line 509):** "SessionSelect gains a 'timed?' / 'mock exam' affordance." Per the AC this story adds a **"Mock Exam" affordance per Exam** on the Start screen (`frontend/src/pages/SessionSelect.jsx`) — a control that, for the selected Exam, starts a mock run instead of a filtered practice session.
- **Exam-style result reuses §4.5 per-Domain breakdown (PRD §4.6 / FR-27, prd.md lines 319, 323; architecture.md line 507):** "the result is an exam-style overall score (with the §4.5 per-Domain breakdown)." The result screen shows the overall score **vs the ~70% pass bar** (a planning heuristic surfaced as guidance, not a guarantee — prd.md lines 297, 300, 409–410) plus the per-Domain breakdown, reusing the Story 6.6 `Summary` per-Domain breakdown and/or the Story 7 readiness/stats framing.
- **Attempts are recorded like any session (epics.md Story 8.4 line 1033; Story 7.2 lines 900–913):** a mock run grades through the same `POST /api/feedback` path, which records each attempt (`exercise_id, exam, domain, correct, selected_id, time_taken_ms, answered_at`) to the SQLite store (Story 7.2 / AR-16/17). No new recording code — the existing `submitAnswer` flow in `SessionContext` already drives this. Per-question timing (Story 8.2, FR-28) sends `timeTakenMs`; reuse it if landed.
- **Dependencies (prerequisites):**
  - **Story 8.1 — Session Countdown Timer (Frontend)** (epics.md lines 971–984): provides the `Timer`/`Countdown` component that shows remaining time, decrements, and at zero auto-ends to the (partial) Summary via `endToSummary`; respects `prefers-reduced-motion` and is announced accessibly. The mock countdown reuses this component, seeded with `durationMinutes`. **If 8.1 is not yet merged, this story is blocked on the countdown/auto-submit AC** — coordinate or land 8.1 first.
  - **Story 8.3 — Mock-Exam Builder (Backend)** (epics.md lines 1004–1019): provides `GET /api/sessions?mode=mock&exam=` returning the domain-weighted full-length set **and** `durationMinutes`. **If 8.3 is not yet merged, `getMockSession` has no endpoint to call** — coordinate or land 8.3 first.
  - (Soft) **Story 8.2 — Per-Question Timing**: if landed, the mock run already sends `timeTakenMs` with feedback; if not, attempts still record with null timing.

## Tasks/Subtasks

- [ ] Task 8.4.1: Add `getMockSession({ exam })` to `frontend/src/api.js`
  - [ ] Call `GET /api/sessions?mode=mock&exam=<exam>` via the existing `apiRequest` helper (URLSearchParams with `mode=mock` + `exam`)
  - [ ] Throw `APIError` when `!result.success`, mirroring `getSession`
  - [ ] Return both the session entries **and** the `durationMinutes` the builder stamps (e.g. `{ entries, durationMinutes }`), since the runner needs the duration to seed the countdown — note the mock response carries `durationMinutes` where the practice `getSession` does not (AC: countdown uses the exam's real duration; architecture lines 505–509)
  - [ ] Guard the entries with `Array.isArray(result.data...) ? ... : []` as `getSession`/`getSessionByIds` do
- [ ] Task 8.4.2: Add the "Mock Exam" affordance to `frontend/src/pages/SessionSelect.jsx`
  - [ ] For the currently selected Exam, render a **"Mock Exam"** control alongside the existing "Start Session" (e.g. a secondary button: "Mock Exam ({Associate ≈45Q/90min | Professional ≈59Q/120min})"), per architecture line 509
  - [ ] On activate, call `getMockSession({ exam })` and start the mock run (Task 8.4.3) — do **not** apply the Domain/difficulty filters (a mock ignores them; it is exam-scoped + domain-weighted server-side)
  - [ ] Preserve all existing SessionSelect behavior: exam/domain/difficulty selects, the live match-count (UX-DR9), "Start Session" → filtered practice, the count===0 disable, error handling
- [ ] Task 8.4.3: Start the mock set under the countdown (`frontend/src/context/SessionContext.jsx`)
  - [ ] Start the mock entries via the existing `startSession(entries)` so the practice runner + per-question grading + attempt recording all work unchanged (Story 7.2)
  - [ ] Carry the mock context (a `mode: 'mock'` flag + `durationMinutes`) through session state so the runner knows to show the countdown and the result screen knows to render exam-style. Add this as a small, additive extension to `START_SESSION` (e.g. an options arg) — do **not** break the existing `startSession(exercises)` callers (SessionSelect practice, Summary replay)
  - [ ] At countdown zero, auto-submit by dispatching the existing `endToSummary` (no new end path) so the partial Summary is computed over whatever was answered (epics.md 8.4 line 1031; 8.1 line 981)
- [ ] Task 8.4.4: Mock-Exam flow page / runner (`frontend/src/pages/MockExam.jsx` OR a SessionSelect/practice mode)
  - [ ] Render the active mock set with the same MCQ single-select practice UI, mounting the Story 8.1 `Timer`/`Countdown` seeded with `durationMinutes`
  - [ ] Wire the countdown's zero-callback to `endToSummary` (auto-submit)
  - [ ] If implementing as a mode rather than a new page, gate the timer/result behavior on the `mode === 'mock'` flag from session state and reuse `MCQPractice` for the question UI (prefer reuse over a parallel runner)
- [ ] Task 8.4.5: Exam-style result screen (reuse `frontend/src/pages/Summary.jsx`)
  - [ ] When the session `mode === 'mock'`, render the result exam-style: overall score **vs the ~70% bar** (pass/fail-style readiness framing, labeled as guidance not a guarantee — prd.md lines 300, 409) plus the existing per-Domain breakdown from `computeResults` (reuse Story 6.6)
  - [ ] Reuse the Story 7 readiness/stats framing for the ~70% comparison where natural (e.g. the `ReadinessIndicator` visual or the threshold constant)
  - [ ] Keep the non-mock Summary (practice) rendering unchanged — branch additively on the mock flag; do not regress the partial-summary / review-incorrect / replay behavior
- [ ] Task 8.4.6: View wiring in `frontend/src/App.jsx` (do not break existing views)
  - [ ] Integrate the mock runner/result without disturbing the existing `select | practice | summary | stats` view switch, the `ExitConfirmContext` registration, or the `goHome`/`goStats` affordances
  - [ ] If MockExam is a distinct view, add a case to `CurrentView`'s switch; if it is a practice/summary mode, no new view is needed — the existing `practice`/`summary` views render mock behavior off the session `mode` flag (prefer this to minimize App.jsx churn)
  - [ ] Verify the header Home / Exit-confirm flow still works during a mock run (ending a mock early should route through the same confirm / partial-summary path)
- [ ] Task 8.4.7: Tests (vitest)
  - [ ] `api.test.js` (or extend): `getMockSession` calls `GET /api/sessions?mode=mock&exam=...` and returns entries + `durationMinutes`; throws `APIError` on `!success`
  - [ ] `SessionSelect.test.jsx`: the "Mock Exam" affordance is present per Exam; activating it calls `getMockSession({ exam })` and starts a mock session (mocking the api)
  - [ ] Mock flow: starting a mock mounts the countdown seeded with `durationMinutes`; at zero the runner auto-submits via `endToSummary` to the result screen (fake timers)
  - [ ] `Summary.test.jsx`: in mock mode the result shows the overall score vs the ~70% bar + the per-Domain breakdown; non-mock Summary rendering is unchanged
  - [ ] Attempt recording: submitting an answer during a mock calls `submitFeedback` (the Story 7.2 record hook) like any session

## Dev Notes

**Current behavior (baseline 4cce825).**

- `frontend/src/api.js` has `getSession({ exam, domain, difficulty })` (GET `/api/sessions`), `getSessionByIds(exerciseIds)` (POST replay), `getExerciseCount(...)`, `submitFeedback({ exerciseId, displayedOptionIds, selectedId })` (POSTs with `type: 'mcq'`), `getStats({ exam })`, and `getReadiness({ exam })`. There is **no** `getMockSession` and no `mode=mock` caller yet — Task 8.4.1 adds it. `getSession` does **not** surface `durationMinutes` (the practice endpoint doesn't stamp one); the mock helper must.
- `frontend/src/pages/SessionSelect.jsx` already has exam (defaults to Associate via `DEFAULT_EXAM`, always sent), domain (scoped to `DOMAINS_BY_EXAM[exam]`), difficulty, the live `getExerciseCount` match-count (UX-DR9), and a single "Start Session" button → `getSession` → `startSession`. The "Mock Exam" affordance is additive here.
- `frontend/src/context/SessionContext.jsx` is a reducer-based store. `startSession(exercises)` dispatches `START_SESSION` (resets to `initialState` + sets `exercises` and `view: 'practice'`). It already has `endToSummary()` (dispatches `END_TO_SUMMARY` → `view: 'summary'`, `sessionState: 'ended-early'`, preserving feedback/questionState so `computeResults` scores the answered subset) — **this is exactly the auto-submit-at-zero target.** `submitAnswer(exerciseId)` POSTs to `/api/feedback` (driving the Story 7.2 attempt record) and retains the response in `feedback[exerciseId]`. There is **no** `mode`/`durationMinutes` in state yet — Task 8.4.3 adds them additively to `START_SESSION` (do not change the existing single-arg callers' behavior).
- `frontend/src/App.jsx` has `CurrentView` switching on `view` (`practice | summary | stats | select`), an `ExitConfirmContext` (Practice registers `requestExit`; the header title routes Home through it during practice), and a `goStats` nav link hidden during `practice`/`stats`. Integrate without breaking any of these.
- `frontend/src/pages/Summary.jsx` exports `computeResults(exercises, feedback, questionState)` → `{ correct, answered, total, byDomain, skipped, unanswered }` and renders the headline score, per-Domain breakdown, Review-incorrect list, and replay actions. The exam-style result reuses `computeResults` + the per-Domain breakdown; the ~70% comparison is the new bit.
- `frontend/src/pages/StatsDashboard.jsx` (Story 7.5) and the `ReadinessIndicator` it uses already render readiness vs ~70%; reuse the threshold/visual for the mock result where natural.
- `frontend/src/constants.js` has `EXAMS` (`associate`/`professional`), `DEFAULT_EXAM`, and `DOMAINS_BY_EXAM`. The mock sizing/timing (45Q/90min, 59Q/120min) is **owned by the backend builder** and arrives as `durationMinutes` — the frontend should not hardcode per-exam Q/min beyond display copy.

**Preserve (do not regress):**
- The existing `select` / `practice` / `summary` / `stats` views and their wiring in `App.jsx`.
- The `ExitConfirmContext` registration + header Home / End-session flow (mock runs must remain exitable via the same confirm/partial-summary path).
- The Stats view + nav link from Story 7.5.
- The non-mock Summary (practice) behavior: partial counts, Review-incorrect, Restart / Practice-these-again replay.
- The flag-less session payload assumption (the client never receives `correct` flags except via retained feedback from `/api/feedback`).
- All existing `startSession(...)` call sites — extend `START_SESSION` additively (optional options arg), never change the meaning of the current single-arg form.

**Approach guidance.** Prefer implementing the mock as a **mode flag on the existing practice/summary views** (a `mode: 'mock'` + `durationMinutes` carried in session state) over a wholly separate `MockExam.jsx` runner, to maximize reuse of `MCQPractice`, `Summary`, the attempt-record hook, and the Exit-confirm flow. The AC explicitly allows "`MockExam.jsx` (or a SessionSelect mode)". A thin `MockExam.jsx` that composes `MCQPractice` + the Story 8.1 `Timer` is acceptable if cleaner.

**Dependencies:** Story 8.1 (Timer/Countdown component — countdown + auto-end-to-Summary) and Story 8.3 (`GET /api/sessions?mode=mock&exam=` returning the set + `durationMinutes`). Both are hard prerequisites for the countdown/auto-submit and the mock-set ACs respectively. Story 8.2 (per-question timing) is a soft dependency — if landed, the mock already sends `timeTakenMs`.

**Testing:** **vitest** (frontend; tests co-located as `.test.jsx` / `.test.js`, per AR-11). Mock the api module; use fake timers for the countdown/auto-submit assertions.

**NEW files:**
- `frontend/src/pages/MockExam.jsx` — only if implementing as a dedicated page/runner (optional per AC; a SessionSelect/practice mode is the alternative)
- `frontend/src/pages/MockExam.test.jsx` — if `MockExam.jsx` is created (else cover the flow in `SessionSelect.test.jsx` / `Summary.test.jsx`)

**UPDATE files:**
- `frontend/src/api.js` — add `getMockSession({ exam })` (Task 8.4.1)
- `frontend/src/pages/SessionSelect.jsx` — "Mock Exam" affordance per Exam (Task 8.4.2)
- `frontend/src/context/SessionContext.jsx` — carry `mode: 'mock'` + `durationMinutes`; auto-submit at zero via existing `endToSummary` (Task 8.4.3)
- `frontend/src/App.jsx` — view wiring for the mock runner/result without breaking the existing switch / ExitConfirm / Stats (Task 8.4.6)
- `frontend/src/pages/Summary.jsx` — exam-style result branch (vs ~70% bar + per-Domain breakdown) gated on the mock flag (Task 8.4.5)
- `frontend/src/api.test.js`, `frontend/src/pages/SessionSelect.test.jsx`, `frontend/src/pages/Summary.test.jsx` — tests (Task 8.4.7)

## References

- `_bmad-output/planning-artifacts/epics.md` — Story 8.4 (lines 1021–1035); Story 8.1 Timer/Countdown (lines 971–984); Story 8.3 mock builder + `durationMinutes` (lines 1004–1019); Story 8.2 per-question timing (lines 988–1001); Story 7.2 record-on-feedback (lines 900–913); Story 6.6 Summary review/replay (lines 841–857); Epic 8 overview (lines 264–271); FR-27 (line 77), AR-18 (line 127)
- `_bmad-output/planning-artifacts/architecture.md` — rev 4 changelog (line 12); Timed Practice / Mock Exam summary (line 45); unseen-first vs mock ordering (line 464); **Mock-Exam session builder decision** (lines 505–509: `mode=mock`, domain-weighted full-length, exam-scoped, ignores unseen-first, stamps duration; timer/timing frontend; SessionSelect mock affordance); `GET /api/sessions` mock contract (line 893); FR-26–28 component map (line 932)
- `_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md` — §4.6 Timed Practice / Mock Exam (lines 305–323); FR-27 (lines 318–323: domain-weighted full-length, exam-scoped, real clock auto-submit, exam-style score + §4.5 per-Domain breakdown); ~70% pass bar as guidance (lines 297, 300, 409–410); SM-6 (line 385)
- `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` — mock-exam flow / result-screen / ~70% framing context (timed/countdown + ~70% pass bar, lines 207, 297, 300)
- Code: `frontend/src/pages/SessionSelect.jsx`, `frontend/src/api.js`, `frontend/src/context/SessionContext.jsx`, `frontend/src/App.jsx`, `frontend/src/pages/Summary.jsx`, `frontend/src/pages/StatsDashboard.jsx`, `frontend/src/constants.js`; NEW `frontend/src/pages/MockExam.jsx` (optional)

## Dev Agent Record

### Implementation Plan

Implemented as a **mode flag on the existing practice/summary views** (the preferred approach) rather than a separate `MockExam.jsx` — maximizes reuse of `MCQPractice`, `Summary`, the Story 7.2 attempt-record hook, the Story 8.1 `Timer`, and the Exit-confirm flow. App.jsx is untouched (mock runs render through the existing `practice`/`summary` views off the session `mode` flag).

### Subtasks Completed

- 8.4.1 — `getMockSession({ exam })` added to `api.js`: GETs `/api/sessions?mode=mock&exam=`, returns `{ entries, durationMinutes }` (the mock response stamps `durationMinutes` at the top level; practice `getSession` does not), throws `APIError` on `!success`, guards entries to `[]` and duration to `null`.
- 8.4.2 — "Mock Exam" affordance on `SessionSelect.jsx`: a secondary button per exam ("Mock Exam (≈45Q / 90 min | ≈59Q / 120 min)"). On activate calls `getMockSession({ exam })` (ignores Domain/difficulty — exam-scoped + weighted server-side) and starts the mock run. All existing SessionSelect behavior preserved.
- 8.4.3 — `SessionContext`: `START_SESSION` extended additively with `mode` ('practice' default | 'mock') and `durationMinutes`; `startSession(exercises, { mode, durationMinutes, timerDurationSeconds })`. Auto-submit at zero reuses the existing `endToSummary` (no new end path). Existing single-arg callers unchanged.
- 8.4.4 — Mock runner = `MCQPractice` (already renders the Story 8.1 `Timer` when `timerDurationSeconds` is set; the mock seeds it with `durationMinutes*60`). Countdown→zero auto-submits via `endToSummary`. No parallel runner.
- 8.4.5 — Exam-style result branch in `Summary.jsx` gated on `mode === 'mock'`: a readiness banner showing the **full-set** score (correct/total — unanswered/skipped count against, exam-style) vs the ~70% pass-bar heuristic (labeled study guidance, not a guarantee), with a threshold marker mirroring `ReadinessIndicator`. Per-Domain breakdown + Review-incorrect + replay reused unchanged. Non-mock Summary untouched.
- 8.4.6 — No `App.jsx` change needed: mock reuses `practice`/`summary` views; ExitConfirm/Home/Stats wiring intact.
- 8.4.7 — Tests below.

### Completion Notes

- `~70%` pass bar centralized as `PASS_THRESHOLD = 0.7` in `constants.js` (mirrors backend `READINESS_THRESHOLD` and the `ReadinessIndicator` fallback).
- Attempt recording during a mock is automatic — the mock run grades through the same `submitAnswer → POST /api/feedback` path (Story 7.2), with per-question `timeTakenMs` (Story 8.2). No new recording code.
- Tests: `api.test.jsx` (getMockSession URL/return/error/malformed — 3 new); `SessionSelect.test.jsx` (Mock Exam button per-exam copy, mock start seeds `mode='mock'` + 5400s countdown via state probe, empty-mock error — 3 new); `Summary.test.jsx` (exam-style banner below/at the ~70% bar, unanswered counts against, no banner for practice — 4 new). The Story 8.1 MCQPractice timer tests already cover countdown/auto-submit at zero.
- Verified: frontend `vitest run` **137 passed** (11 files), `npm run lint` clean. Backend untouched (Story 8.3 builder + endpoint already green).

## File List

- UPDATE: `frontend/src/constants.js`, `frontend/src/api.js`, `frontend/src/pages/SessionSelect.jsx`, `frontend/src/context/SessionContext.jsx`, `frontend/src/pages/Summary.jsx`
- UPDATE (tests): `frontend/src/api.test.jsx`, `frontend/src/pages/SessionSelect.test.jsx`, `frontend/src/pages/Summary.test.jsx`
- No new source pages (`MockExam.jsx` not needed — implemented as a mode flag); `App.jsx` untouched.

## Change Log

- Initial story creation — 2026-06-07
- Implemented as a mode flag on practice/summary; frontend 137 tests green — 2026-06-08

## Status

done
