---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.4: End Session, Exit Confirm & Home

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-4-end-session-exit-confirm-home

## Story Statement

As a **student**,
I want **to end or leave a session at any time, with a confirmation and the option to see partial results**,
So that **I'm never trapped in a session and don't lose progress by accident**.

## Acceptance Criteria

**Given** I'm in an active practice session
**When** I activate the persistent "End session" control (or click the header title = Home)
**Then** an Exit-confirm modal appears offering *See results*, *Discard & exit*, *Keep practicing* (unless zero questions are answered, which exits straight to Start)
**And** *See results* routes to a partial Summary via `endToSummary` (Story 6.3)
**And** *Discard & exit* returns to the Start screen (reset)
**And** the modal is focus-trapped, labeled, Esc-dismissible (= Keep practicing), and restores focus to the trigger on close
**And** tests cover each action and the zero-answered shortcut

Acceptance detail derived from EXPERIENCE.md:

- The End-session control is persistent on the Practice surface (top-right of the question header row), secondary/neutral styling so it never competes with the Submit `databricks-500` button (EXPERIENCE.md → Component Patterns: End-session control).
- The header title is a clickable Home affordance on every surface. On Practice it behaves identically to End-session (routes through Exit confirm); on Summary/Start it goes to Start directly (EXPERIENCE.md → Component Patterns: Home affordance).
- Modal copy: **"End this session? You've answered {n} of {total}."** with actions *"See results"* · *"Discard & exit"* · *"Keep practicing"* (EXPERIENCE.md → Voice / Microcopy; Component Patterns: Exit confirm).
- Zero answered → no confirm; exit straight to Start (EXPERIENCE.md → Component Patterns: End-session control; epics.md Story 6.4 AC).

## Architecture Context

- **architecture.md rev 3** (`_bmad-output/planning-artifacts/architecture.md`) introduces the new behavioral components for this epic: *"persistent End-session control, Exit-confirm modal (focus-trapped)"* and the reducer actions `endToSummary` (exit Practice early → Summary over the answered subset) and the existing `exit`/`reset` to Start (architecture.md lines ~293–296). Visual tokens inherited from DESIGN.md.
- **EXPERIENCE.md** (`_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md`):
  - Component Patterns — End-session control, Exit-confirm modal, Home affordance (lines ~59–61).
  - Accessibility Floor — Modal: traps focus, is labeled (`aria-modal`, labelled title), Esc-dismissible, restores focus on close (line ~105); Color independence (line ~106).
  - Flow 1 — "Dario bails out of a long set without losing face" (lines ~111–112): End session → Exit confirm → *See results* → partial Summary banking the answered subset.
- **State flow:** `view` ('select' | 'practice' | 'summary') lives in `SessionContext`. The modal does NOT add a new `view`; it is local UI state in the Practice surface / a wrapping component. Actions dispatched:
  - *See results* → `endToSummary()` (Story 6.3) → reducer sets `view: 'summary'` over the answered subset.
  - *Discard & exit* → `reset()` (existing) → reducer returns to `initialState` (`view: 'select'`).
  - *Keep practicing* / Esc / backdrop → close modal, stay on Practice.

## Tasks/Subtasks

- [ ] Task 6.4.1: Create `frontend/src/components/ConfirmDialog.jsx` (NEW) — reusable, accessible modal
  - [ ] Props: `open`, `title`, `description`, `actions` (array of `{ label, onClick, variant }`), `onDismiss`
  - [ ] Render nothing when `open` is false
  - [ ] Root element: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` (title id), `aria-describedby` (description id)
  - [ ] Focus trap: cycle Tab / Shift+Tab among focusable children; move focus into the dialog on open (first action or the dialog container)
  - [ ] `Esc` key calls `onDismiss` (= Keep practicing)
  - [ ] Backdrop click calls `onDismiss`; clicks inside the dialog do not
  - [ ] On close, restore focus to the element that was focused before open (capture `document.activeElement` on open, or accept a `triggerRef`)
  - [ ] Neutral styling consistent with existing Tailwind tokens; action button order matches EXPERIENCE.md (See results, Discard & exit, Keep practicing)

- [ ] Task 6.4.2: Add persistent End-session control to `frontend/src/pages/MCQPractice.jsx`
  - [ ] Place a secondary/neutral "End session" button top-right of the existing question header row (the `flex items-center justify-between` block around lines 82–98), not competing with the `databricks-500` Submit button
  - [ ] Local state `confirmOpen`; clicking End session opens the confirm UNLESS zero answered (then call `reset()` / exit straight to Start)
  - [ ] Keep a `ref` on the trigger so focus can be restored on close
  - [ ] Compute `answeredCount` for the modal copy (number of exercises with retained `feedback`, per Story 6.3 per-question state); pass `total` from context

- [ ] Task 6.4.3: Wire the header title as a Home affordance in `frontend/src/App.jsx`
  - [ ] Make the `<h1>` title interactive (clickable, keyboard-activatable — render as a button or add `role`/`tabIndex` + key handler), preserving current text/styling
  - [ ] On Practice (`view === 'practice'`): behaves like End session — open the same Exit-confirm (zero-answered → straight to Start)
  - [ ] On Summary/Start: go to Start directly via `reset()`
  - [ ] Since the modal/answered-count logic lives where session state is available, route Home through `useSession()` (lift the confirm trigger so both the header and Practice can open it, OR expose a shared handler) — keep wiring minimal and avoid duplicating the modal

- [ ] Task 6.4.4: Connect the three modal actions
  - [ ] *See results* → `endToSummary()` (Story 6.3), close modal
  - [ ] *Discard & exit* → `reset()`, close modal
  - [ ] *Keep practicing* (and Esc / backdrop) → close modal only

- [ ] Task 6.4.5: Accessibility verification
  - [ ] Confirm `aria-modal`, labelled title, focus trap, Esc-dismiss, focus-restore-to-trigger
  - [ ] Confirm correctness/feedback still never conveyed by color alone elsewhere (no regression to MCQPractice ✓/✗ glyphs)

- [ ] Task 6.4.6: Tests (Vitest + React Testing Library)
  - [ ] `frontend/src/components/ConfirmDialog.test.jsx` (NEW): renders when open / not when closed; `Esc` calls `onDismiss`; focus moves in on open and restores to trigger on close; Tab focus stays trapped; `role="dialog"` + `aria-modal` + labelled title present
  - [ ] Extend `frontend/src/pages/MCQPractice.test.jsx`: End-session button visible; with ≥1 answered → opens confirm; *See results* lands on partial Summary; *Discard & exit* returns to Start; *Keep practicing* keeps Practice; zero-answered → exits straight to Start with NO confirm shown
  - [ ] Extend `frontend/src/App.test.jsx`: header title is clickable Home — on Practice opens confirm (or zero-answered shortcut), on Summary/Start routes to Start

## Dev Notes

### Dependency

- **Requires Story 6.3** for `endToSummary` and the per-question state model (`unanswered | answered | skipped`) used to compute the answered count and the partial Summary. If 6.3 is not yet merged at implementation time, coordinate: this story's *See results* path is non-functional without `endToSummary`. The `reset` action already exists today (SessionContext.jsx line 154 / reducer `RESET` lines 93–94).

### NEW files

- `frontend/src/components/ConfirmDialog.jsx` — accessible modal (focus trap, Esc, focus restore, `aria-modal`).
- `frontend/src/components/ConfirmDialog.test.jsx` — modal a11y/behavior tests.

### UPDATE files

- `frontend/src/pages/MCQPractice.jsx` — add End-session control + confirm wiring.
- `frontend/src/App.jsx` — make header title a Home affordance.
- `frontend/src/context/SessionContext.jsx` — only if a shared confirm trigger needs lifting here; prefer NOT adding session state for the modal (it is transient UI). `endToSummary` and `reset` are consumed, not (re)defined, by this story.
- `frontend/src/pages/MCQPractice.test.jsx`, `frontend/src/App.test.jsx` — extend.

### Current behavior (baseline 10824eb)

- `frontend/src/App.jsx`: `CurrentView()` switches on `view` ('practice' → `MCQPractice`, 'summary' → `Summary`, default → `SessionSelect`). The `<h1>` title (lines 25–27) is static, non-interactive. No End-session control anywhere.
- `frontend/src/context/SessionContext.jsx`: reducer handles `START_SESSION`, `SET_SELECTION`, `SUBMIT_*`, `NEXT`, `RESET`. Context exposes `reset()` (line 154). `feedback[exerciseId]` holds graded results — basis for the answered count. (`endToSummary`/`prev`/`skip` come from Story 6.3.)
- `frontend/src/pages/MCQPractice.jsx`: question header row is the `flex items-center justify-between mb-4` block (lines 82–98) showing "Question X of Y" + domain/difficulty badges — the natural anchor for the End-session control's top-right placement. `if (!currentExercise) return null` guard at line 37.

### Preserve

- Do not change the existing `view` switch semantics or add a 'modal' view; keep the modal as transient UI state.
- Preserve header title text and styling; only add interactivity.
- Do not alter MCQPractice's existing radiogroup, Submit/Feedback, color-independence glyphs, or the `displayedOptions.length !== 4` / code-completion graceful-degradation guards.
- Submit button keeps `databricks-500`; End-session control must be visually subordinate (neutral/secondary).

### Accessibility requirements (modal)

- `role="dialog"` + `aria-modal="true"`; labelled by the title (`aria-labelledby`); described by the count copy (`aria-describedby`).
- Focus trap among the dialog's focusable elements; focus moves into the dialog on open.
- `Esc` dismisses (= Keep practicing); backdrop click dismisses.
- Focus returns to the trigger element on close.
- Color independence floor still applies app-wide — no correctness signal by color alone.

## References

- `_bmad-output/planning-artifacts/epics.md` — Story 6.4 (lines 757–771); Story 6.3 dependency (lines 738–753).
- `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` — Component Patterns: End-session control / Exit-confirm modal / Home affordance (lines ~59–61); Voice/Microcopy modal copy (line ~49); Accessibility Floor (lines ~105–106); Flow 1 (lines ~111–112).
- `_bmad-output/planning-artifacts/architecture.md` — rev 3 new behavioral components + reducer actions `endToSummary` / `reset` (lines ~293–296).
- `frontend/src/App.jsx`, `frontend/src/context/SessionContext.jsx`, `frontend/src/pages/MCQPractice.jsx`.

## Dev Agent Record

### Implementation Plan

(To be filled in by the dev agent.)

### Subtasks Completed

(To be filled in as implementation progresses.)

### Completion Notes

(To be filled in upon task completion.)

## File List

(Files will be listed here upon completion.)

## Change Log

- Initial story creation — 2026-06-06

## Status

ready-for-dev
