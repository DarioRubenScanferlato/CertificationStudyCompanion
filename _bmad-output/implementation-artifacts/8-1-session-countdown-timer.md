---
status: ready-for-dev
baseline_commit: 4cce825
---

# Story 8.1: Session Countdown Timer

**Epic:** 8 - Timed Practice / Mock Exam
**Story Key:** 8-1-session-countdown-timer

## Story Statement

As a **student**,
I want **an optional countdown on a practice session**,
So that **I can train under time pressure**.

## Acceptance Criteria

**Given** the Start screen
**When** I enable a timer and start a session
**Then** a `Timer`/`Countdown` component shows remaining time and decrements; at zero the session auto-ends to the (partial) Summary via `endToSummary`
**And** with the timer off, behavior is unchanged from the untimed runner
**And** the timer respects `prefers-reduced-motion` and is announced accessibly
**And** vitest tests cover countdown display, auto-end at zero, and timer-off parity

Acceptance detail derived from FR-26, architecture rev 4, and EXPERIENCE.md:

- The timer is **opt-in** on the Start screen: the user enables it and sets (or accepts a default) duration in minutes. With it off, no Timer renders and `startSession` is called exactly as today (PRD §4.6 FR-26: "With the timer off, behavior is unchanged from the untimed runner").
- With the timer **on**, remaining time is visible on the Practice surface and decrements once per second; at zero the session **auto-ends to the (partial) Summary** via the existing `endToSummary()` action (which banks the answered subset — Story 6.3). It does NOT discard or reset (PRD §4.6 FR-26: "reaching zero ends the session and shows the summary over what was answered (partial summary)").
- Timer/countdown is **client-side only** — there is no server-side timer/clock (architecture rev 4 §"Timer is frontend (FR-26/FR-28)"; AR-18). No backend changes in this story.
- **Accessibility:** remaining time is announced via an `aria-live` region (politely, not on every tick — e.g. at coarse intervals and near expiry) and the countdown's visual transitions respect `prefers-reduced-motion` (EXPERIENCE.md → Accessibility Floor: Live regions; Targets & motion).
- **Scope:** this story delivers the *optional session countdown* (FR-26) and the reusable `Timer`/`Countdown` component. Mock-Exam wiring (FR-27) and per-question timing (FR-28) are **separate stories** (8.3 / 8.2) and out of scope here, though the component is built to be reused by Mock Exam (architecture rev 4: "a `Timer`/`Countdown` component (used by both the optional session timer and Mock-Exam mode)").

## Architecture Context

- **architecture.md rev 4** (`_bmad-output/planning-artifacts/architecture.md`):
  - §"Decision: Mock-Exam session builder" → **"Timer is frontend (FR-26/FR-28): the countdown, auto-submit-at-zero, and per-question elapsed timing live in React … No server-side timer/clock. New frontend: a `Timer`/`Countdown` component (used by both the optional session timer and Mock-Exam mode) … SessionSelect gains a 'timed?' / 'mock exam' affordance."** (line ~509)
  - Epic 6 summary line: "Optional per-session countdown with auto-end (FR-26) … Timer/timing are client-side." (line ~45)
  - FR→component map: **FR-26–28 → `Timer.jsx`/`Countdown.jsx`, `MockExam.jsx`, `SessionSelect.jsx` (timed/mock affordance)** — backend column is "—" for the timer (line ~932); confirms this story is frontend-only.
  - **AR-18** (epics.md): "timer/countdown + per-question timing are client-side … new FE components StatsDashboard, ReadinessIndicator, Timer/Countdown, MockExam."
- **State flow:** the timer is a **client-side concern layered on the existing runner**. The session `view` ('select' | 'practice' | 'summary' | 'stats') and the `endToSummary` action already live in `SessionContext`. Auto-end at zero dispatches the existing `endToSummary()` (which sets `view: 'summary'`, `sessionState: 'ended-early'` over the answered subset). The timer adds **no new reducer view**; the duration / enabled flag is transient session-scoped UI state (passed at start and held in the Practice surface / a small timer hook), not graded state.
- **No server-side timer:** the duration is never sent to the backend for the optional countdown; the client owns the clock. (Mock Exam, story 8.3/8.4, will read the exam `durationMinutes` stamped by the backend builder — not in scope here.)

## Tasks / Subtasks

- [ ] Task 8.1.1: Create `frontend/src/components/Timer.jsx` (NEW) — reusable countdown
  - [ ] Props: `durationMs` (or `durationSeconds`), `running` (bool), `onExpire` (called once when remaining hits 0), optional `onTick`
  - [ ] Internal `remaining` state; decrement via a single `setInterval` (1s cadence) started/stopped by `running`; clear the interval on unmount and when it expires (no double-fire of `onExpire`)
  - [ ] Drive elapsed time off a wall-clock reference (capture a start timestamp and compute `remaining = duration - (now - start)`) so a backgrounded tab / throttled interval doesn't drift; clamp at 0
  - [ ] Render remaining time as `MM:SS` (and `HH:MM:SS` if ≥ 60 min, for the 90/120-min exam reuse later)
  - [ ] `aria-live="polite"` region announcing the time at coarse intervals (not every second) and at/near expiry; visual ticking text marked `aria-hidden` so the live region isn't spammed each second
  - [ ] Visual transitions (e.g. a progress ring/bar or low-time pulse) respect `prefers-reduced-motion` — gate any animation behind the existing reduced-motion convention used by `ProgressBar` (mirror that approach for consistency)
  - [ ] No timer/business logic about *sessions* inside the component — it only counts down and reports expiry, so Mock Exam (8.4) can reuse it

- [ ] Task 8.1.2: Add the timer opt-in to `frontend/src/pages/SessionSelect.jsx` (UPDATE)
  - [ ] Add a "Timed session?" toggle (checkbox) and, when enabled, a duration input (minutes) with a sensible default (e.g. 1 min/question or a fixed default — document the chosen default); off by default
  - [ ] Pass the chosen duration into the session when starting. Preferred: extend `startSession(exercises, options?)` so the timer config rides with the session start without inventing a new global; OR hold the duration in a small piece of state the Practice surface can read. Keep it minimal and avoid adding graded reducer state for a transient clock
  - [ ] **Timer-off must equal today's behavior:** when the toggle is off, `handleStart` calls `startSession(sessionEntries)` exactly as it does now (no timer config), and the Practice surface renders no Timer
  - [ ] Reuse existing Tailwind form-control styling and the `databricks-500` focus ring already used by the exam/domain/difficulty controls; label the inputs (`htmlFor`/`id`) like the existing fields

- [ ] Task 8.1.3: Wire the Timer + auto-end into `frontend/src/pages/MCQPractice.jsx` (UPDATE)
  - [ ] When a session was started timed, render `<Timer>` in the question header row (the `flex items-center gap-4 mb-4` block, near the domain/difficulty badges and the End-session button) — visually subordinate, not competing with Submit
  - [ ] `onExpire` calls the existing `endToSummary()` from `useSession()` (already destructured at lines ~50–66) to land on the partial Summary; expiry must fire **once** and not re-fire if the component re-renders
  - [ ] Stop/freeze the timer once `view` leaves 'practice' (the Practice surface unmounts on Summary, so the interval is cleared on unmount — verify no leak)
  - [ ] When the session is untimed, render nothing extra and leave the existing header/markup byte-for-byte equivalent (the only diff is the conditional Timer)

- [ ] Task 8.1.4: Accessibility & reduced-motion verification
  - [ ] Confirm the `aria-live` region announces remaining time without flooding (coarse cadence) and announces at expiry; visual ticker is `aria-hidden`
  - [ ] Confirm any countdown animation is suppressed under `prefers-reduced-motion` (consistent with the `ProgressBar` treatment)
  - [ ] Confirm Esc / End-session / keyboard shortcuts on Practice are unaffected (the timer adds no keydown handlers; no regression to the Story 6.5 shortcut handler)
  - [ ] Color independence floor still applies — time-low state must not be conveyed by color alone (add text/glyph if a low-time visual cue is introduced)

- [ ] Task 8.1.5: Tests (Vitest + React Testing Library)
  - [ ] `frontend/src/components/Timer.test.jsx` (NEW): with fake timers, renders the formatted start time; decrements over advanced time; calls `onExpire` exactly once at zero (and not again after further ticks); does not tick while `running=false`; clears its interval on unmount; exposes an `aria-live` region
  - [ ] Extend `frontend/src/pages/SessionSelect.test.jsx`: timer toggle renders; enabling it reveals a duration input; starting timed passes the duration through to `startSession`; **timer off → `startSession` called with no timer config (parity)**
  - [ ] Extend `frontend/src/pages/MCQPractice.test.jsx`: with a timed session, the Timer is visible and counting; advancing fake timers to zero triggers `endToSummary` (lands on Summary, partial); **with an untimed session, no Timer renders and the runner behaves exactly as the existing untimed tests assert**

## Dev Notes

- **Frontend-only story.** No backend / API / store changes. The countdown, its display, and auto-end are entirely client-side (architecture rev 4 §"Timer is frontend (FR-26/FR-28)"; AR-18). Do not add a `durationMinutes` to `GET /api/sessions` for the optional countdown — that field is the Mock-Exam builder's concern (story 8.3).
- **Frontend tests = vitest** (AR-11; the repo uses Vitest + React Testing Library, `*.test.jsx` co-located with source). Use Vitest fake timers (`vi.useFakeTimers()` / `vi.advanceTimersByTime`) for the countdown.
- **Timer-off must equal current behavior** — this is an explicit FR-26 consequence and an AC. The untimed path must call `startSession(sessionEntries)` unchanged and render zero extra DOM on Practice; the existing SessionSelect/MCQPractice tests must keep passing with no edits to their untimed assertions.

### NEW files

- `frontend/src/components/Timer.jsx` — reusable, accessible countdown (display, decrement, `onExpire`, reduced-motion-aware). Built to be reused by Mock Exam (story 8.4); keep it free of session-specific logic.
- `frontend/src/components/Timer.test.jsx` — component countdown/expiry/a11y tests.

### UPDATE files

- `frontend/src/pages/SessionSelect.jsx` — add the timer opt-in (toggle + duration) and thread the duration into session start. **Current behavior (baseline 4cce825):** picks `exam` (default Associate), `domain`, `difficulty`; shows a live match count via `getExerciseCount`; `handleStart` (lines ~56–75) calls `getSession({exam, domain, difficulty})` then `startSession(sessionEntries)`. There is **no timer affordance today**. **Preserve:** the exam-scoped domain dropdown (`DOMAINS_BY_EXAM`), the live match-count effect and its ignore-flag stale-drop, the empty-result error path, the `count === 0` disabled Start button, and the exact untimed `startSession` call.
- `frontend/src/pages/MCQPractice.jsx` — conditionally render `<Timer>` and wire `onExpire → endToSummary`. **Current behavior (baseline 4cce825):** consumes `useSession()` including `endToSummary` and `reset` (lines ~50–66); renders the progress bar + domain/difficulty badges + the neutral **End session** button in the `flex items-center gap-4 mb-4` header (lines ~249–277); owns the Exit-confirm modal (Story 6.4) and the document-level keyboard-shortcut handler (Story 6.5); guards `if (!currentExercise) return null` and degrades code-completion / non-4-option exercises gracefully. **Preserve:** the radiogroup + Submit/Feedback flow, the `endToSummary`/Exit-confirm wiring, the keyboard-shortcut handler (the timer must not add competing keydown handlers), the graceful-degradation guards, and the color-independence ✓/✗ glyphs.
- `frontend/src/context/SessionContext.jsx` — touch **only if** threading the timer duration through `startSession` is the chosen approach (extend the action/signature to carry an optional timer config). `endToSummary` (`END_TO_SUMMARY`, lines ~152–155 / action at line ~220) is **consumed, not redefined**, by this story. Prefer NOT adding reducer state for the live clock — the countdown is transient UI, mirroring how Story 6.4 kept the modal out of the reducer. The `view` switch semantics must not change.
- `frontend/src/pages/SessionSelect.test.jsx`, `frontend/src/pages/MCQPractice.test.jsx` — extend (do not weaken the existing untimed assertions).

### Dependency

- **Requires Story 6.3 (done)** for `endToSummary` and the per-question / partial-Summary model. `endToSummary()` already exists in `SessionContext` (action `END_TO_SUMMARY`, reducer lines ~152–155; exposed at line ~220) and is already destructured/used by `MCQPractice.jsx` — the auto-end-at-zero path reuses it directly. No changes to the reducer's `END_TO_SUMMARY` behavior are needed.
- Independent of Stories 8.2 (per-question timing) and 8.3/8.4 (Mock Exam); those reuse the same `Timer` component but are separate.

### Accessibility requirements (timer)

- `aria-live="polite"` region announcing remaining time at coarse intervals (avoid per-second spam) and at/near expiry; the per-second visual ticker is `aria-hidden="true"`.
- Any countdown animation (ring/bar/pulse) is suppressed under `prefers-reduced-motion`, consistent with the `ProgressBar` reduced-motion treatment (EXPERIENCE.md → Accessibility Floor: Targets & motion).
- Color-independence floor still applies app-wide — a low-time cue must include text/glyph, not color alone.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-8.1] — Story 8.1 ACs (lines ~971–984); Epic 8 goal (lines ~264–271); AR-18 (line ~127).
- [Source: `_bmad-output/planning-artifacts/architecture.md`#Timer-is-frontend] — "Timer is frontend (FR-26/FR-28)" decision (line ~509); Epic 6 timed-practice summary (line ~45); FR-26–28 component map (line ~932); rev 4 changelog (line ~12).
- [Source: `_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md`#FR-26] — §4.6 FR-26 optional session countdown + testable consequences (lines ~307–316).
- [Source: `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md`#Accessibility-Floor] — Live regions / `aria-live="polite"` (line ~104); Targets & motion / `prefers-reduced-motion` (line ~107).
- [Source: `frontend/src/pages/SessionSelect.jsx`] — current filters + `handleStart` → `startSession` (lines ~56–75).
- [Source: `frontend/src/pages/MCQPractice.jsx`] — header row + End-session control (lines ~249–277); `endToSummary` consumption (lines ~50–66).
- [Source: `frontend/src/context/SessionContext.jsx`] — `END_TO_SUMMARY` reducer + `endToSummary` action (lines ~152–155, ~220); `startSession` action (line ~213).

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (main loop; original parallel agent died with a socket error mid-task and was completed here).

### Completion Notes List

- `Timer.jsx` (created by the original agent) reused as-is: wall-clock-anchored, drift-resistant countdown; `MM:SS` / `HH:MM:SS`; coarse-cadence `aria-live="polite"` announcer; per-second ticker `aria-hidden`; low-time cue carries glyph+text (not color alone); transitions gated behind `motion-reduce:`. `onExpire` fires exactly once via an `expiredRef` guard.
- Threaded the optional duration through `SessionContext`: added transient `timerDurationSeconds` to state, set on `START_SESSION` from `action.timerDurationSeconds`; extended `startSession(exercises, options?)` so the duration rides with the start. Untimed start (no options) leaves `timerDurationSeconds: null` — byte-for-byte parity with the pre-8.1 path. No new reducer view; `END_TO_SUMMARY` consumed unchanged.
- `SessionSelect.jsx`: added an off-by-default "Timed session" checkbox; when on, a "Duration (minutes)" number input (default 20). `handleStart` passes `{ timerDurationSeconds: minutes*60 }` only when timed; otherwise calls `startSession(entries)` exactly as before. Live match-count effect, empty-result error path, and `count === 0` disabled Start all preserved.
- `MCQPractice.jsx`: conditionally renders `<Timer durationSeconds={timerDurationSeconds} onExpire={endToSummary} />` in the existing header row (subordinate to Submit). Untimed sessions render no Timer. Timer interval is cleared on unmount (Practice unmounts on Summary), so auto-end at zero is leak-free. No new keydown handlers — the Story 6.5 shortcut handler is untouched.
- Tests: `Timer.test.jsx` (8 tests, fake timers — format MM:SS/HH:MM:SS, decrement, expire-once, no-tick-while-paused, unmount cleanup, timer role); extended `SessionSelect.test.jsx` (toggle reveals duration, duration threads through as seconds, timer-off parity via a state probe) and `MCQPractice.test.jsx` (no Timer untimed, counting Timer timed, auto-end-to-Summary at zero).
- Verified: frontend `vitest run` 122 passed (10 files), `npm run lint` clean. Backend untouched.

### File List

- NEW: `frontend/src/components/Timer.jsx`, `frontend/src/components/Timer.test.jsx`
- UPDATE: `frontend/src/context/SessionContext.jsx`, `frontend/src/pages/SessionSelect.jsx`, `frontend/src/pages/MCQPractice.jsx`, `frontend/src/pages/SessionSelect.test.jsx`, `frontend/src/pages/MCQPractice.test.jsx`
