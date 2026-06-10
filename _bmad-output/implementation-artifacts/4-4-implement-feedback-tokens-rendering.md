---
status: review
baseline_commit: 4cce825
---

# Story 4.4: Implement FeedbackTokens Rendering

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-4-implement-feedback-tokens-rendering

## Story Statement

As a **student**,
I want **to see colored feedback on my attempt**,
So that **I understand what's right and what's wrong**.

(FR-14 display — epics.md Story 4.4.)

## Acceptance Criteria

**Given** I've submitted a code attempt
**When** feedback is computed
**Then** my code renders with tokens colored **green/yellow/grey**
**And** I can see the **remaining attempts counter**
**And** if I've exhausted attempts, the **canonical answer is revealed**
**And** vitest tests cover token coloring (incl. color-independence), the attempts counter, and the reveal-on-exhaustion display

Acceptance detail / scope boundary with Story 4.5:

- **4.4 is presentational.** It renders the feedback the engine (4.3) produced, the attempts counter the loop (4.5) tracks, and — when told the exercise has concluded — the revealed canonical answer. The **state machine** (decrementing attempts, detecting a solve, deciding *when* to reveal, showing the explanation, advancing) belongs to **Story 4.5**; 4.4 provides the components 4.5 drives.
- Concretely this story delivers: a **`FeedbackTokens`** component (colors one attempt's tokens), an **attempts counter** affordance, and a **reveal** display for the canonical answer. 4.5 wires them into the live loop.

## Architecture Context

- **`FeedbackTokens.jsx` — green/yellow/grey token coloring** is a named Phase-2 frontend component (architecture.md lines 616, 840; component boundary line 906: "renders green/yellow/grey feedback"). It consumes the output of Story 4.3's `computeFeedback` — an array of `{ token, color, position }` — and renders the attempt's tokens in order, each tinted by color.
- **Color-independence is a hard accessibility floor (app-wide).** Green/yellow/grey **must not be conveyed by color alone** — mirror the pattern already used across the app (e.g. MCQ feedback uses ✓/✗ glyphs alongside color; `ReadinessIndicator`/`Timer` pair color with text/glyph). Each token color needs a non-color cue: a glyph/marker (e.g. ✓ for green, ↔/○ for yellow/misplaced, ·/✕ for grey), an `aria-label`/`title` per token (e.g. "`SELECT` — correct"), and/or a visible legend. Provide an `aria-live`/`role="status"` summary of the attempt result so screen-reader users get the outcome without parsing per-token tints.
- **Reuse existing visual language.** Tailwind green/yellow/grey utility classes consistent with the MCQ feedback palette (`bg-green-100 text-green-800`, etc.); reduced-motion respected if any reveal animation is added (mirror `ProgressBar`/`Timer`'s `motion-reduce:`). Monospace for tokens (this is code) — reuse `CodeBlock`/`<pre>` styling conventions where it helps, but tokens need per-token spans so they can be individually colored (so this is likely bespoke spans, not `CodeBlock`).
- **Playfulness (architecture.md lines 52, 87–88):** the colored-tile reveal is the Wordle delight beat — keep it crisp and satisfying, not a sterile diff.
- **Client-side only.** Pure presentation off props; no API calls.

## Tasks / Subtasks

- [x] **Task 4.4.1 — Create `frontend/src/components/FeedbackTokens.jsx`** (NEW)
  - [x] Props: `tokens` (the `[{ token, color, position }]` from `computeFeedback`). Render each token as a colored span/tile in order, monospace.
  - [x] **Color-independence:** pair every color with a glyph/marker AND a per-token `aria-label`/`title` ("correct" / "wrong position" / "not in answer"); render a small **legend** (green=correct spot, yellow=present elsewhere, grey=not in answer). Add a `role="status"` summary line (e.g. "3 correct, 1 misplaced, 2 not in answer").
  - [x] Handle empty/edge inputs gracefully (no tokens → render nothing/placeholder, never crash).
  - [x] If multiple past attempts are shown as a stack (Wordle history), support rendering a list of attempt rows (accept an array of attempts, or render one row and let 4.5 stack them — pick one and document it; a single-row component that 4.5 maps over is simplest).
- [x] **Task 4.4.2 — Attempts counter affordance**
  - [x] A small, accessible "Attempts left: N" (or N/Max) indicator suitable for the `CodeCompletion.jsx` header/near-input area. Presentational — value supplied by props (4.5 owns the count). Announce changes politely (don't spam).
- [x] **Task 4.4.3 — Canonical-answer reveal display**
  - [x] A reveal block that shows the canonical `answer` (and is styled distinctly as "the answer"). Presentational: visible only when a `revealed`/`concluded` prop is true. 4.5 decides *when*; 4.4 only renders it. (The explanation panel is wired in 4.5, reusing the MCQ feedback explanation/references styling.)
  - [x] Use a monospace render for the revealed code answer; color-independent.
- [x] **Task 4.4.4 — Wire the components into `CodeCompletion.jsx` for display** (UPDATE — minimal)
  - [x] Mount `<FeedbackTokens>` where attempts render, the attempts counter in the header region (the placeholder from Story 4.1), and the reveal block — all driven by props/local state that Story 4.5 will fully populate. Keep this story's wiring shallow: it should render correctly when handed feedback/attempts data, even before 4.5's loop exists (tests can pass props directly to the components).
- [x] **Task 4.4.5 — Tests** (`frontend/src/components/FeedbackTokens.test.jsx`, NEW — vitest)
  - [x] Given a `tokens` array with mixed colors, each token renders with the right color class **and** its non-color cue (glyph and/or `aria-label`); assert color-independence (a grey vs green token differs by more than a class — has a distinct label/glyph).
  - [x] Legend + `role="status"` summary render and reflect the counts.
  - [x] Attempts counter renders the supplied value and updates when the prop changes.
  - [x] Reveal block is hidden until `revealed`/`concluded`, then shows the canonical answer.
  - [x] Empty tokens → no crash.

## Dev Notes

### NEW files
- `frontend/src/components/FeedbackTokens.jsx` — green/yellow/grey token renderer (+ legend, a11y summary).
- `frontend/src/components/FeedbackTokens.test.jsx` — vitest.

### UPDATE files
- `frontend/src/pages/CodeCompletion.jsx` — mount `FeedbackTokens`, the attempts counter, and the reveal block (shallow wiring; Story 4.5 makes them live). **Preserve** the Story 4.1 template display + input + Exit-confirm header.

### Preserve / do not regress
- The app-wide **color-independence floor** (✓/✗-style cues, never color alone) — consistent with MCQ feedback, `ReadinessIndicator`, `Timer`.
- Reduced-motion handling for any reveal animation (mirror `ProgressBar`/`Timer` `motion-reduce:`).

### Dependencies
- **Depends on Story 4.3** for the `{ token, color, position }` shape it renders, and **Story 4.1** for the page it mounts into. Story 4.5 drives it with live attempt/feedback/reveal state. Tests can feed props directly, so 4.4 can be verified before 4.5 lands.

### References
- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-4.4] — ACs (lines ~604–616); FR-14 (line 51).
- [Source: `_bmad-output/planning-artifacts/architecture.md`] — `FeedbackTokens.jsx` named component (lines 616, 840); green/yellow/grey (line 71); component boundary "renders green/yellow/grey feedback" (line 906); playfulness (lines 52, 87–88).
- [Source: `frontend/src/pages/MCQPractice.jsx`] — color-independence pattern (✓/✗ glyphs with color) + Tailwind feedback palette to mirror.
- [Source: `frontend/src/components/ReadinessIndicator.jsx`, `frontend/src/components/Timer.jsx`] — established "color + text/glyph, never color alone" + `motion-reduce:` conventions.
- Story 4.3 — `computeFeedback(...)` output consumed here.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story workflow, 2026-06-09).

### Completion Notes List

- `FeedbackTokens` renders one attempt's tokens with color + a non-color cue per token (glyph ✓/↔/· + per-token `aria-label` "correct"/"wrong position"/"not in answer"), a `role="status"` summary ("N correct, N misplaced, N not in answer"), and an optional legend (color-independence floor).
- Named exports `AttemptsCounter` ("Attempts left: N of M", aria-live) and `AnswerReveal` (hidden until `revealed`, then shows the canonical answer via CodeBlock). All presentational/off-props.
- Live wiring into `CodeCompletion.jsx` was completed in Story 4.5 (the loop drives these components).
- 6 vitest tests (color + cue independence, status summary, legend toggle, empty tokens, counter value, reveal gating) — green.

### File List

- frontend/src/components/FeedbackTokens.jsx (NEW)
- frontend/src/components/FeedbackTokens.test.jsx (NEW)

### Change Log

- 2026-06-09 — Implemented FeedbackTokens + AttemptsCounter + AnswerReveal (color-independent) + 6 unit tests (Story 4.4).
