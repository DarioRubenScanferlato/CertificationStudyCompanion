---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.5: Progress Bar, Navigation Controls & Keyboard Shortcuts

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-5-progress-bar-navigation-keyboard

## Story Statement

As a **student**,
I want **a progress bar with running score, back/skip controls, and keyboard shortcuts**,
So that **I can drill quickly and stay oriented**.

## Acceptance Criteria

**Given** an active session in `frontend/src/pages/MCQPractice.jsx`
**When** I practice
**Then** a visual progress bar shows my position and a running correct count (e.g. "12/20 · 9 correct"), updating on submit and on navigation
**And** Back (read-only revisit) and Skip controls are available and wired to the Story 6.3 `prev` / `skip` actions
**And** keyboard shortcuts work: `1`–`4` (and `a`–`d`) select the corresponding option, `Enter` submits when an option is selected and not yet submitted then acts as Next/See-results after submit, `←` / `→` go Back / Next (and `→` on an unanswered question acts as Skip with the same unanswered recording), `Esc` opens the Exit-confirm and dismisses it (= Keep practicing) — all with pointer parity (no shortcut is the only way to do anything)
**And** focus is visible on every interactive control, and the correctness result and progress changes are announced via `aria-live="polite"`
**And** progress-bar motion respects `prefers-reduced-motion`
**And** a small "keyboard hints" affordance makes the shortcuts discoverable
**And** tests cover progress display, keyboard selection/submit/nav, and accessibility attributes

## Architecture Context

- **Surface:** Practice (`MCQPractice.jsx`). The progress bar replaces the text-only "Question X of Y" header that exists today (`architecture.md` rev 3, Component Patterns — behavioral; `EXPERIENCE.md` Component Patterns).
- **Progress bar (behavioral component):** shows position across the session and a running **correct count**, e.g. "12/20 · 9 correct". Updates on submit and on navigation. Exposes `aria-valuenow` / `aria-valuemax` (or equivalent text) and respects `prefers-reduced-motion` for its transition (`EXPERIENCE.md` Component Patterns + Accessibility Floor). Visual tokens inherited from DESIGN.md.
- **Navigation controls:** Back (read-only revisit) wired to reducer `prev`; Skip wired to reducer `skip`. These reducer actions are introduced by **Story 6.3** (`architecture.md` rev 3: "New actions: `prev` (decrement index; revisit read-only), `skip` (advance without grading; records the question as *unanswered*, not incorrect)"). A furthest-reached pointer prevents Back/Next from overrunning.
- **Keyboard map (`EXPERIENCE.md` Interaction Primitives):**
  - `1`–`4` and `a`–`d` → select the corresponding option (no-op once submitted).
  - `Enter` → Submit when an option is selected and not yet submitted; after submit, `Enter` → Next / See results.
  - `←` → Back; `→` → Next (Next only enabled after submit; `→` on an unanswered question acts as Skip with the unanswered recording).
  - `Esc` → open End-session/Exit-confirm (and dismiss it = Keep practicing). The Exit-confirm modal itself is owned by **Story 6.4**; this story dispatches the open/close intent.
- **Accessibility floor (`EXPERIENCE.md`):** full keyboard operability with a visible focus ring on every interactive element; single-select options remain a radio group (`role="radiogroup"`, native roving arrow-key behavior); correctness result and progress announced via `aria-live="polite"` (the result banner already uses `role="status"`); correctness never conveyed by color alone (keep the ✓/✗ glyph + text label).
- **Flow 2 (Fast keyboard drilling):** the target experience is clearing a 20-question set in one unbroken keyboard rhythm — `2`, `Enter` (submit), read, `Enter` (next) — with `←`/`→` to revisit a prior question read-only and return.
- **Running score source:** computed from the `feedback` map in `SessionContext` (`feedback[exerciseId].correct`), which Story 6.3 retains. No backend change; no re-grading on Back.

## Tasks/Subtasks

- [ ] Task 6.5.1: Create `frontend/src/components/ProgressBar.jsx` (NEW)
  - [ ] Props: `current` (1-based position), `total`, `correct` (running correct count)
  - [ ] Render a visual bar (filled proportion = `current / total`) plus text "{current}/{total} · {correct} correct"
  - [ ] Expose `role="progressbar"` with `aria-valuenow={current}`, `aria-valuemin={1}`, `aria-valuemax={total}`, and an `aria-label`/`aria-valuetext` conveying the running score
  - [ ] Gate the fill transition behind `prefers-reduced-motion` (e.g. `motion-reduce:transition-none`, or no transition when reduced motion is preferred)
  - [ ] Use DESIGN.md / Tailwind brand tokens (`databricks-*`) for the fill

- [ ] Task 6.5.2: Wire the progress bar into `MCQPractice.jsx`
  - [ ] Replace the text-only "Question {currentIndex + 1} of {total}" span with `<ProgressBar>`
  - [ ] Derive `correct` from the session `feedback` map (count of `feedback[id].correct === true`)
  - [ ] Confirm it updates on submit (feedback added) and on navigation (index change)

- [ ] Task 6.5.3: Add Back / Skip navigation controls
  - [ ] Consume `prev` and `skip` from `useSession()` (provided by Story 6.3)
  - [ ] Render a Back control, disabled when at the first question (`currentIndex === 0`)
  - [ ] Render a Skip control, available pre-submit (advances and records the question as unanswered, not incorrect)
  - [ ] Ensure pointer parity: every keyboard action has a visible, clickable control equivalent

- [ ] Task 6.5.4: Implement the keyboard handler
  - [ ] Add a single `keydown` listener scoped to the Practice surface (e.g. a `useEffect` on document within `MCQPractice`, cleaned up on unmount) so it doesn't leak to other views
  - [ ] `1`–`4` / `a`–`d` → map to `displayedOptions[index]` and select (no-op if submitted/submitting)
  - [ ] `Enter` → submit when an option is selected and not yet submitted; after submit → `next` (See results when last)
  - [ ] `ArrowLeft` → `prev` (no-op at first); `ArrowRight` → `next` if submitted, else `skip`
  - [ ] `Escape` → dispatch the Exit-confirm open/close intent (open hook from Story 6.4; close = Keep practicing)
  - [ ] Ignore shortcuts when focus is in a text input / when a modal is open (defer to the modal's own Esc); don't intercept browser/AT keys beyond the mapped set
  - [ ] Add a small "keyboard hints" affordance so shortcuts are discoverable

- [ ] Task 6.5.5: Accessibility polish
  - [ ] Ensure a visible focus ring on Back, Skip, Submit, Next, options, and the keyboard-hints toggle (Tailwind `focus-visible:` ring)
  - [ ] Wrap the correctness result and progress announcements in `aria-live="polite"` regions (result banner keeps `role="status"`)
  - [ ] Keep the radio group semantics (`role="radiogroup"`) and the ✓/✗ glyph + text label intact (color-independent correctness)

- [ ] Task 6.5.6: Vitest coverage (`frontend/src/pages/MCQPractice.test.jsx`, new `frontend/src/components/ProgressBar.test.jsx`)
  - [ ] ProgressBar: renders position + running correct count; exposes `aria-valuenow`/`aria-valuemax`; reduced-motion class applied
  - [ ] Keyboard select: `1`/`a` selects option 1; selecting is a no-op after submit
  - [ ] Keyboard submit-then-advance: `Enter` submits a selected answer, then `Enter` advances (and reaches Summary on the last question)
  - [ ] Keyboard nav: `ArrowLeft` goes Back (read-only, no re-POST), `ArrowRight` advances after submit and Skips (records unanswered) before submit
  - [ ] `Escape` triggers the Exit-confirm open intent
  - [ ] Pointer parity: Back/Skip buttons perform the same actions as their shortcuts
  - [ ] A11y attrs: focus-visible classes present; `aria-live` region present; radiogroup role retained
  - [ ] Progress updates on submit and on navigation

## Dev Notes

### Files
- **NEW** `frontend/src/components/ProgressBar.jsx` — presentational progress bar (position + running correct count, `role="progressbar"`, reduced-motion aware).
- **NEW** `frontend/src/components/ProgressBar.test.jsx` — component tests.
- **UPDATE** `frontend/src/pages/MCQPractice.jsx` — swap the text header for `<ProgressBar>`, add Back/Skip controls + keyboard-hints affordance, install the keydown handler, add focus-visible/aria-live polish.
- **UPDATE** `frontend/src/pages/MCQPractice.test.jsx` — add keyboard/nav/a11y/progress tests.

### Current behavior (baseline `10824eb`)
- `MCQPractice.jsx` reads `currentExercise, currentIndex, total, selectedAnswers, submitting, submitErrors, feedback, setSelection, submitAnswer, next` from `useSession()`.
- It renders a text-only header `Question {currentIndex + 1} of {total}`, the question via `QuestionContent`, the 4 `displayedOptions` as a native radio group (`role="radiogroup"`), a Submit button (disabled until an option is selected), and on submit a `Feedback` block (`role="status"` banner with ✓/✗ + text, explanation, references, and a Next/"See Results" button calling `next`).
- Grading is single-select via the backend (`submitAnswer` → `submitFeedback` API). `feedback[exerciseId] = {correct, correctOptionId, explanation, references}`.
- Defensive paths: `CODE_COMPLETION` type and any exercise without exactly 4 `displayedOptions` render an `UnsupportedExercise` fallback (which already exposes a Skip/Next via `onNext`).

### Preserve
- **Single-select grading via the API** — do not re-grade locally; Back/revisit must not re-POST. Keep `submitAnswer`'s "once submitted, ignore re-submits" guard.
- The radio-group semantics, the ✓/✗ glyph + text label (color-independent correctness), and the `role="status"` result banner.
- The `UnsupportedExercise` fallback behavior.

### Keyboard handler placement & pointer parity
- Install one `keydown` listener via `useEffect` inside `MCQPractice` (document-level, removed on unmount) rather than per-element handlers, so the map is centralized and view-scoped.
- Read current state through the handler closure / refs to avoid stale values; mirror `submitAnswer`'s pattern in `SessionContext` if a ref is needed.
- Every shortcut must have a visible, clickable equivalent (options, Submit, Next, Back, Skip, End-session) — shortcuts are an accelerator, never the only path.
- Don't fire shortcuts while focus is in a text field or while the Exit-confirm modal is open (the modal owns its own Esc / focus trap).

### Reduced motion
- The progress-bar fill animation must be disabled (or made instant) when `prefers-reduced-motion: reduce` — use Tailwind `motion-reduce:` variants or a media-query check. No other essential information may depend on motion.

### Dependencies
- **Story 6.3** (prerequisite): provides reducer actions `prev` and `skip`, per-question `unanswered | answered | skipped` state, the furthest-reached pointer, and the retained `feedback` map this story reads for the running score and read-only Back. If 6.3 is not yet merged, coordinate so Back/Skip wiring lands against the real action names (`prev`, `skip`).
- **Story 6.4** (pairs with): owns the Exit-confirm modal (focus-trapped, labeled, Esc-dismissible, restores focus). This story only dispatches the open/close intent on `Esc`; the modal's internal Esc handling and focus restoration belong to 6.4.

## References

- `_bmad-output/planning-artifacts/epics.md` — Story 6.5 (lines 775–790); UX-DR Coverage Map (lines 161–172); Epic 6 framing (line 217+).
- `_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` — Interaction Primitives (Keyboard map, lines 89–98); Component Patterns — Progress bar (line 62); Accessibility Floor (lines 100–107); Flow 2 — Fast keyboard drilling (line 114).
- `_bmad-output/planning-artifacts/architecture.md` (rev 3) — QoL reducer actions `prev`/`skip`/`endToSummary` and per-question/session states (lines 291–296); new behavioral components incl. progress bar (line 296).
- `frontend/src/pages/MCQPractice.jsx` — current Practice surface (text header, radio group, Submit, Feedback/Next).
- `frontend/src/context/SessionContext.jsx` — session reducer + `feedback` map (extended by Story 6.3 with `prev`/`skip`).

## Dev Agent Record

### Implementation Plan

(To be filled in by the dev agent)

### Subtasks Completed

(To be filled in as implementation progresses)

### Completion Notes

(To be filled in upon task completion)

### File List

(Files will be listed here upon completion)

### Change Log

- Initial story creation — 2026-06-06
