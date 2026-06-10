---
status: review
baseline_commit: 4cce825
---

# Story 4.5: Implement Guess Limit & Answer Reveal

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-5-implement-guess-limit-answer-reveal

## Story Statement

As a **student**,
I want **a bounded number of attempts**,
So that **I'm motivated to think before typing**.

(FR-15, FR-17 — epics.md Story 4.5. This is the capstone that assembles the full Wordle loop.)

## Acceptance Criteria

**Given** I start a code-completion exercise
**When** I make an attempt
**Then** the **remaining attempts counter decreases**
**And** when attempts reach zero, the **canonical answer is revealed**
**And** the **explanation is shown**
**And** I can **move to the next exercise**
**And** vitest tests cover the attempt-decrement, solve-before-exhaustion, reveal-on-exhaustion, explanation display, and advance-to-next paths

Acceptance detail:

- This story owns the **state machine** that the prior stories' pieces plug into: bounded attempts, decrement-per-submit, solve detection, conclude-and-reveal (on solve **or** exhaustion), explanation/references display, and advancing to the next exercise. It completes Epic 4 — after this, a code-completion exercise is fully playable end-to-end.
- A **correct guess before exhaustion** also concludes the exercise (reveal + explanation + Next) — a win shouldn't force the user to burn remaining attempts.

## Architecture Context

- **FR-15 Limited guesses with reveal:** "User has bounded number of attempts; on solving or exhausting attempts, canonical answer is revealed" (epics.md line 53). **FR-17 Show Explanation:** "Explanation and references shown once exercise concludes" (epics.md line 57).
- **Wordle-style bound (playfulness, architecture.md lines 52, 87–88).** Choose a sensible attempt budget and **document it** (Wordle's 6 is a natural default; pick a constant and put it in `frontend/src/constants.js` so it's tunable, e.g. `CODE_COMPLETION_MAX_ATTEMPTS`). The guess-and-narrow loop is the differentiator — keep it delightful, not a pass/fail gate.
- **Reuses 4.2/4.3/4.4 + 4.1's page.** Each submit: `computeFeedback(attempt, answer, language, {accepted, caseSensitive, ignoreWhitespace})` (4.3) → push a `FeedbackTokens` row (4.4) → decrement the counter → if the result is **solved** (all-green per 4.3's solved signal) **or** counter hits 0, **conclude**: reveal canonical `answer`, show `explanation` + `references`, surface **Next**.
- **Advancing reuses the existing session machinery (no new end path).** "Next" calls `useSession()`'s `next()` (which advances or, on the last exercise, transitions to Summary). Ending early / Home still routes through the Story 6.4 Exit-confirm via `useRegisterExitConfirm` (already wired by Story 4.1). Code-completion outcomes are **client-side only** — they do **not** POST to `/api/feedback` and are **not** recorded in the SQLite attempt store (that store is MCQ-scoped, Epic 7). Do not invent a recording path here. (If code-completion stats are ever wanted, that's a future story; flag it, don't build it.)
- **Explanation/references display mirrors MCQ feedback.** Reuse the `MCQPractice.jsx` `Feedback` component's explanation + references markup/styling (whitespace-preserved explanation; `target="_blank" rel="noopener noreferrer"` reference links) so code-completion conclusion looks consistent with MCQ feedback.
- **Per-question timing (Story 8.2):** code-completion does not currently feed timing (no `submitFeedback` call). Leave timing out of scope — the attempt store doesn't track code-completion. (Note it as a known gap, consistent with the no-recording decision above.)

## Tasks / Subtasks

- [x] **Task 4.5.1 — Attempt budget constant** (`frontend/src/constants.js`, UPDATE)
  - [x] Add `export const CODE_COMPLETION_MAX_ATTEMPTS = 6` (or the chosen value) with a comment explaining the Wordle-style bound. Single source of truth for the counter.
- [x] **Task 4.5.2 — Guess-loop state machine in `CodeCompletion.jsx`** (UPDATE)
  - [x] Local state: the current typed attempt, the list of past attempts (each with its `FeedbackTokens` row), `attemptsLeft` (init = max), and a `concluded` flag (+ `solved` flag).
  - [x] On **Submit/Guess** (button + Enter): ignore empty/whitespace-only; run `computeFeedback` (4.3); append the attempt row; decrement `attemptsLeft`; set `solved` if the result is all-green; set `concluded` if `solved` or `attemptsLeft === 0`. Disable the input/submit once `concluded`.
  - [x] On **conclude**: reveal the canonical `answer` (4.4 reveal block), render the **explanation + references** (reuse MCQ `Feedback` styling), and show a **Next** button.
  - [x] **Next** → `useSession().next()` (advances or routes to Summary on the last exercise). On a solve, optionally surface a brief success beat (color-independent, reduced-motion-safe).
  - [x] Reset all per-exercise state when `currentExercise.exerciseId` changes (so navigating to the next code-completion exercise starts fresh) — mirror the per-question reset pattern used in `MCQPractice.jsx` (the `useEffect` keyed on `exerciseId`).
- [x] **Task 4.5.3 — Counter + reveal wiring** (UPDATE, builds on 4.4)
  - [x] Drive the 4.4 attempts counter from `attemptsLeft`; drive the reveal block from `concluded`; stack the `FeedbackTokens` rows for the attempt history (most recent visible).
  - [x] Keyboard: Enter submits a guess (when not concluded); Enter on a focused button defers to native activation (avoid double-fire) — mirror the `MCQPractice` keyboard discipline. Do **not** add competing document-level handlers that clash with the existing Practice shortcuts.
- [x] **Task 4.5.4 — Accessibility & parity**
  - [x] Announce conclusion via `role="status"`/`aria-live` ("Solved in N attempts" / "Out of attempts — answer revealed"). Counter changes announced politely (not per-keystroke).
  - [x] Color-independence maintained (delegated to 4.4). Reduced-motion respected for any success/reveal animation.
  - [x] Ending early / Home still works mid-exercise via the existing Exit-confirm (partial Summary excludes code-completion from MCQ scoring — verify the Summary doesn't miscount code-completion entries; if `computeResults` only counts entries with MCQ feedback, code-completion simply isn't scored, which is correct — confirm with a test).
- [x] **Task 4.5.5 — Tests** (`frontend/src/pages/CodeCompletion.test.jsx`, EXTEND — vitest)
  - [x] Submitting a guess decrements "attempts left" by one and renders a `FeedbackTokens` row.
  - [x] **Solve before exhaustion:** a correct (or accepted-alternative) guess concludes immediately — reveal + explanation + Next appear without burning remaining attempts.
  - [x] **Exhaustion:** after `MAX_ATTEMPTS` wrong guesses, the canonical answer is revealed, the explanation/references show, and Next appears; the input is disabled.
  - [x] **Next advances:** clicking Next calls the session `next()` (advance to the next exercise, or Summary if last) — assert via a harness like the MCQ tests' `Harness`/probe.
  - [x] **Per-exercise reset:** advancing to another code-completion exercise resets attempts/history/concluded.
  - [x] **No recording / no API:** submitting a code-completion guess does **not** call `submitFeedback`/any API (assert the mocked api is untouched).

## Dev Notes

### UPDATE files
- `frontend/src/constants.js` — add `CODE_COMPLETION_MAX_ATTEMPTS`.
- `frontend/src/pages/CodeCompletion.jsx` — the full guess loop / state machine (decrement, solve, conclude, reveal, explanation, Next). **Preserve** the Story 4.1 template/input/header + the 4.4 components it mounts.
- `frontend/src/pages/CodeCompletion.test.jsx` — extend with the loop tests.

### Reuse (don't reinvent)
- `computeFeedback` (4.3), `tokenize` (4.2), `FeedbackTokens` + counter + reveal (4.4).
- `useSession().next()` and the Exit-confirm flow (Stories 3.6 / 6.4) — **do not** add a new end/advance path.
- `MCQPractice.jsx` `Feedback` explanation/references markup — mirror for the code-completion conclusion.
- The per-`exerciseId` reset `useEffect` pattern from `MCQPractice.jsx` (also used for Story 8.2 timing).

### Explicit non-goals (do not build)
- **No `POST /api/feedback/code-completion`** and **no SQLite recording** of code-completion attempts — feedback is client-side (Epic 4 decision; NFR-1) and the attempt store is MCQ-scoped (Epic 7). Note the "code-completion not in stats" gap; don't close it here.
- No per-question timing for code-completion (Story 8.2 is MCQ-scoped).

### Dependencies
- **Depends on Stories 4.1 (page), 4.2 (tokenizer), 4.3 (feedback), 4.4 (rendering).** This is the last story in Epic 4 — it makes code-completion fully playable end-to-end.

### References
- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-4.5] — ACs (lines ~620–633); FR-15 (line 53), FR-17 (line 57).
- [Source: `_bmad-output/planning-artifacts/architecture.md`] — playfulness/Wordle loop (lines 39, 52, 87–88); NFR-1 client-side (lines 49, 92, 142–143); CodeCompletion holds "attempt, feedback, attempt count" (line 294).
- [Source: `frontend/src/pages/MCQPractice.jsx`] — `Feedback` explanation/references markup; per-`exerciseId` reset `useEffect`; keyboard discipline; Exit-confirm wiring to mirror.
- [Source: `frontend/src/context/SessionContext.jsx`] — `next()` advance/Summary semantics reused (no new end path).
- [Source: `frontend/src/pages/Summary.jsx`] — `computeResults` only scores entries with feedback; confirm code-completion entries are simply unscored (not miscounted).
- Stories 4.1–4.4 — page, `tokenize`, `computeFeedback`, `FeedbackTokens` consumed here.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story workflow, 2026-06-09).

### Completion Notes List

- Capstone: wired the full guess loop into `CodeCompletion.jsx`. Each submit runs `computeFeedback` (4.3) client-side, appends a `FeedbackTokens` row (4.4), decrements `attemptsLeft`, and concludes on solve (all-green) OR exhaustion.
- On conclusion: status banner ("Solved in N tries" / "Out of attempts"), `AnswerReveal`, explanation + references (mirrors MCQ `Feedback` markup), and a Next button → `useSession().next()` (advances or routes to Summary). Input disabled once concluded. Per-`exerciseId` reset effect.
- Added `CODE_COMPLETION_MAX_ATTEMPTS = 6` to `constants.js`. Enter submits a guess.
- No `POST /api/feedback` and no SQLite recording for code-completion (client-side only; known stats/timing gap by design). Verified the grading API is never called.
- Also fixed a stale MCQ test (`MCQPractice.test.jsx`) that expected the removed 4.1 placeholder — code_completion is routed away by App's PracticeRouter (covered in App.test.jsx); MCQPractice's option-less fallback is now asserted as graceful (no crash).
- 7 vitest tests (decrement+row, solve-before-exhaustion, accepted alternative, exhaustion+reveal+disable, Next advances, per-exercise reset, Next→Summary, no-API). Full suite green (frontend 179).

### File List

- frontend/src/constants.js (M — CODE_COMPLETION_MAX_ATTEMPTS, EXERCISE_TYPE_OPTIONS)
- frontend/src/pages/CodeCompletion.jsx (M — full guess loop; review fixes: retention, progress, outcome enum, zero-token guard)
- frontend/src/pages/CodeCompletion.test.jsx (NEW)
- frontend/src/pages/MCQPractice.test.jsx (M — stale code_completion degradation test updated)
- frontend/src/context/SessionContext.jsx (M — `codeCompletionResults` retention + RECORD_CODE_COMPLETION action)
- frontend/src/pages/Summary.jsx (M — exclude code-completion from MCQ tallies; "Code drills: X/Y solved")
- frontend/src/pages/MCQPractice.jsx (M — adopt shared shell: styles/ui, ExplanationPanel, useSessionExit)
- frontend/src/styles/ui.js (NEW — shared FOCUS_RING/FOCUS_RING_NEUTRAL/DIFFICULTY_STYLES)
- frontend/src/components/ExplanationPanel.jsx (NEW — shared explanation + references)
- frontend/src/hooks/useSessionExit.js (NEW — shared Exit-confirm wiring)
- frontend/src/utils/language.js (NEW — single LANGUAGE_ALIASES; imported by CodeBlock/tokenizer/codeFeedback)
- backend/app/session.py (M — `_order_unseen_first` excludes code-completion from unseen-first; sprinkles randomly)

### Change Log

- 2026-06-09 — Implemented the bounded guess loop / reveal / explanation / advance; Epic 4 runner now fully playable end-to-end (Story 4.5).
- 2026-06-10 — Code-review fixes (decision-log #43-46): concluded drills retained via SessionContext `codeCompletionResults` so Back/Next shows them final (was wiping + re-arming); ProgressBar `correct` now reflects real MCQ count in a mixed session (was hardcoded 0); single `outcome` enum replaces the `solved`+`concluded` booleans; zero-token attempts rejected without consuming a guess; shared shell adopted (styles/ui.js, ExplanationPanel, useSessionExit). +2 tests (retention, zero-token).
