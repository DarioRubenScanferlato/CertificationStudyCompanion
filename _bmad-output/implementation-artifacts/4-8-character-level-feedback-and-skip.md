---
status: done
baseline_commit: 247164b
---

# Story 4.8: Character-Level Feedback + Skip

**Epic:** 4 - Code-Completion Practice
**Story Key:** 4-8-character-level-feedback-and-skip

## Story Statement

As **a student**,
I want **per-letter (Wordle-style) feedback and a Skip button**,
So that **the code-completion drill actually narrows toward the answer and I'm never trapped exhausting attempts**.

(Added 2026-06-10 via correct-course. Reverses the token-level feedback of stories 4.3/4.4 — see decision-log #54/#55, PRD §4.3/FR-14/FR-15, architecture rev 9, Sprint Change Proposal `_bmad-output/planning-artifacts/sprint-change-proposal-2026-06-10.md`.)

## Acceptance Criteria

**Given** a code-completion exercise
**When** I submit a guess
**Then** feedback is rendered **per character**: green (right letter, right place) / yellow (letter in the answer, wrong place) / grey (not in the answer), with **two-pass duplicate-letter handling**, computed client-side < 100ms
**And** it honors `case_sensitive` (per-character compare) and `ignore_whitespace`, and scores against the **best** of `[canonical, ...accepted]` (FR-16)
**And** `solved` is true iff the attempt equals a candidate (all-green and equal length, after the case/whitespace rules)
**And** `FeedbackTokens` renders **per-character tiles**, color-independent (per-tile glyph + `aria-label`, plus the `role="status"` summary)
**When** I press **Skip**
**Then** the runner advances to the next exercise **without revealing** the answer/explanation (distinct from solve/exhaustion, which reveal)
**And** the **6-guess cap** (`CODE_COMPLETION_MAX_ATTEMPTS`) is retained, with auto-reveal on exhaustion and reveal on solve
**And** the regex `tokenizer.js` (+ `tokenizer.test.js`) is **removed**; `utils/language.js` (LANGUAGE_ALIASES) **stays** (still used by `CodeBlock` for Prism + by `codeFeedback` for the per-language case rule)
**And** `codeFeedback.test.js` / `FeedbackTokens.test.jsx` / `CodeCompletion.test.jsx` are updated for character-level + Skip; `tokenizer.test.js` is deleted; backend + frontend suites + lint are green

## Architecture Context

- **Character-level engine (replaces token two-pass).** `computeFeedback(attempt, canonical, language, { accepted, caseSensitive, ignoreWhitespace })` now compares **characters**, not tokens:
  1. Normalize attempt + each candidate per the rules: if `ignoreWhitespace`, drop whitespace chars; if not `caseSensitive`, lowercase for comparison (the *rendered* char keeps the user's casing).
  2. For each candidate, run the standard **two-pass Wordle**: pass 1 greens by position (decrementing a per-letter multiset of the candidate); pass 2 yellows from remaining counts, else grey.
  3. Score = (greens, then yellows); return the **best** candidate's coloring. `solved` = all-green AND `attempt` length == candidate length (after normalization).
  - Return shape stays `{ tokens: [{ token, color, position }], solved }` where each `token` is now a **single character** (keep the field name `tokens`/`token` so `FeedbackTokens` + the guess loop need minimal change; or rename to `cells`/`char` — dev's choice, just keep it consistent and update the renderer).
- **`FeedbackTokens.jsx`** renders one tile per character (monospace). Color-independence: keep the `role="status"` summary ("N correct, N misplaced, N not in answer") and a per-tile `aria-label`/`title` (e.g. "f — correct"); a per-character glyph is optional (tiles get noisy — the status summary carries the non-color signal). Legend unchanged.
- **`CodeCompletion.jsx`** adds a **Skip** control next to Submit (subordinate styling). Skip calls `useSession().next()` and does **not** set the concluded/reveal state (no `AnswerReveal`, no `ExplanationPanel`, no `recordCodeCompletion`). The 6-guess loop, solve/exhaustion reveal, retention-on-conclude (Story 11.1 fix), and per-`exerciseId` reset are all unchanged.
- **Skip ≠ conclude:** a skipped exercise is NOT recorded in `codeCompletionResults`, so Back-nav revisiting it starts fresh (consistent with "no reveal"). In the Summary "Code drills: X/Y solved", a skipped drill is in Y but not X (no solved record) — correct.
- **`tokenizer.js` removal:** it is imported ONLY by `codeFeedback.js`. After the rewrite, delete `tokenizer.js` + `tokenizer.test.js`. Do NOT remove `utils/language.js` — `CodeBlock.jsx` and `codeFeedback.js` (case rule) still import `LANGUAGE_ALIASES`/`normalizeLanguage`.
- **No backend change.** The session entry already carries `answer`/`accepted`/`caseSensitive`/`ignoreWhitespace`. `<100ms` NFR is trivially met (char compare on one short word).
- **Case nuance retained:** SQL items `case_sensitive: false` → case-insensitive char compare; PySpark items `case_sensitive: true` → case-sensitive. `effectiveCaseSensitive(language, caseSensitive)` logic carries over (defaults by language when the flag is absent), still using `LANGUAGE_ALIASES`.

## Tasks / Subtasks

- [x] **Task 4.8.1 — Rewrite `codeFeedback.js` to character-level** (UPDATE)
  - [x] Per-character two-pass Wordle; normalize for `ignoreWhitespace` (drop whitespace) and `caseSensitive` (lowercase compare, keep rendered casing); best-candidate scoring over `[canonical, ...accepted]`; `solved` = all-green AND equal length. Return `{ tokens|cells, solved }`. Pure, < 100ms. Stop importing `tokenize`.
  - [x] Rewrite `codeFeedback.test.js`: per-letter green/yellow/grey, duplicate-letter rule, accepted alternative (`filter`/`where`), SQL case-insensitive vs PySpark case-sensitive, whitespace-ignore, solved/length, perf.
- [x] **Task 4.8.2 — Per-character `FeedbackTokens.jsx`** (UPDATE)
  - [x] Render one tile per character (monospace), color + per-tile `aria-label`, keep the legend + `role="status"` summary. Update `FeedbackTokens.test.jsx`.
- [x] **Task 4.8.3 — Skip in `CodeCompletion.jsx`** (UPDATE)
  - [x] Add a Skip button (subordinate to Submit) → `next()`, no reveal, no record. Keep the 6-cap, solve/exhaustion reveal, retention-on-conclude, per-exercise reset. Add a Skip test to `CodeCompletion.test.jsx` (advances, no reveal, api/grading untouched).
- [x] **Task 4.8.4 — Remove the tokenizer**
  - [x] Delete `frontend/src/utils/tokenizer.js` and `frontend/src/utils/tokenizer.test.js`. Confirm nothing else imports `tokenize` (grep). Keep `utils/language.js`.
- [x] **Task 4.8.5 — Validate**
  - [x] Full frontend suite + eslint green; spot-check a real exercise (e.g. `format`, `availableNow`, `filter`/`where`) shows correct per-letter feedback and Skip advances without reveal.

### Review Findings (code review 2026-06-11)

Headline: **algorithm verified correct** (two-pass duplicates, longer-attempt guard, `solved`-length, normalization all sound); all 8 ACs MET; Skip + retention + cap preserved. Only minor polish.

Patches:
- [x] [Review][Patch] Doc-comment accuracy: `codeFeedback.js` header says "casing preserved for display" but, when `ignoreWhitespace`, whitespace is silently dropped from the rendered tiles too. Clarify the comment [frontend/src/utils/codeFeedback.js]
- [x] [Review][Patch] Test gap: the `i >= targetChars.length` longer-attempt guard is unexercised. Add a test (e.g. `formatXY` vs `format` → trailing chars grey, `solved: false`) [frontend/src/utils/codeFeedback.test.js]

Deferred (real, by-design tradeoff — see deferred-work.md):
- [x] [Review][Defer] No "right letter, wrong case" cue: under `case_sensitive: true` (camelCase answers like `availableNow`/`checkpointLocation`), a case-only miss shows grey (looks "not in answer"). This is inherent to 3-state per-letter Wordle (which is what was requested); the explanations already flag case-sensitivity. Revisit only if it proves confusing (e.g. make such answers case-insensitive, or add a subtle case cue) — deferred.

Dismissed (3): best-candidate tiebreak is order-dependent on exact greens+yellows ties (only `dbx-de-0163` has a divergent alternative; any valid word still solves — correct, not a bug); the supplied review diff understated the change set (the whole session is uncommitted — MCQPractice refactor/backend churn is prior work, not 4.8); `FeedbackTokens.test.jsx` fixture uses a multi-char token (component is char-count-agnostic — harmless).

## Dev Notes

### UPDATE / DELETE files
- `frontend/src/utils/codeFeedback.js` (M — character-level), `frontend/src/utils/codeFeedback.test.js` (M)
- `frontend/src/components/FeedbackTokens.jsx` (M — per-character tiles), `FeedbackTokens.test.jsx` (M)
- `frontend/src/pages/CodeCompletion.jsx` (M — Skip), `CodeCompletion.test.jsx` (M — Skip test)
- `frontend/src/utils/tokenizer.js` (DELETE), `frontend/src/utils/tokenizer.test.js` (DELETE)

### Preserve / do not touch
- `utils/language.js` (still used by CodeBlock + codeFeedback). Backend (no change). The guess-loop cap, reveal, retention (Story 11.1), per-exercise reset, exit-confirm.

### Dependencies / non-goals
- Builds on the shipped runner (4.1–4.5) + retention fix (11.1 review). No backend, no content change (answers already single words). MCQ feedback (`Feedback`/`ExplanationPanel`) unaffected.

### References
- decision-log #54/#55; PRD §4.3 / FR-14 / FR-15 / OQ-3; architecture rev 9; Sprint Change Proposal 2026-06-10.
- Existing `codeFeedback.js` two-pass token logic (adapt to chars); `FeedbackTokens.jsx`; `CodeCompletion.jsx` guess loop.

## Dev Agent Record

### Agent Model Used
claude-opus-4-8 (dev-story workflow, 2026-06-10).

### Completion Notes List
- **`codeFeedback.js` rewritten to character-level** two-pass Wordle: per-letter green/yellow/grey, `ignoreWhitespace` drops whitespace, `caseSensitive` governs the compare (rendered char keeps the typed casing), best-candidate scoring over `[canonical, ...accepted]`, `solved` = all-green AND equal length. No longer imports `tokenize`. Return shape kept as `{ tokens:[{token,color,position}], solved }` with `token` = one character, so `FeedbackTokens` and the guess loop needed no structural change.
- **`FeedbackTokens.jsx` unchanged** — it was already agnostic over `{token,color,position}`, so it renders one tile per character automatically (glyph + per-tile `aria-label` + `role="status"` summary intact). Its tests still pass.
- **Skip added to `CodeCompletion.jsx`**: a Skip button beside Submit → `next()` with **no reveal, no record** (skipped ≠ concluded, so Back revisits fresh). Removed the now-obsolete zero-token guard + `inputError` state (under char-level a non-empty attempt always yields chars; `canSubmit`'s trim check covers the empty case). 6-guess cap + solve/exhaustion reveal + retention-on-conclude + per-exercise reset unchanged.
- **Removed** `frontend/src/utils/tokenizer.js` + `tokenizer.test.js` (only `codeFeedback` imported `tokenize`; confirmed by grep). Kept `utils/language.js` (CodeBlock + codeFeedback case rule); refreshed its stale comment + CodeCompletion's docstring.
- Tests: `codeFeedback.test.js` rewritten for char-level (13); `CodeCompletion.test.jsx` extended with a per-character-feedback assertion + a Skip-advances-without-reveal test + a skipped-not-recorded test (11). **Frontend 176 pass** (−12 tokenizer tests removed), eslint clean; backend 294 unchanged (no backend change).

### File List
- frontend/src/utils/codeFeedback.js (M — character-level engine)
- frontend/src/utils/codeFeedback.test.js (M — char-level tests)
- frontend/src/pages/CodeCompletion.jsx (M — Skip button; removed zero-token guard; docstring)
- frontend/src/pages/CodeCompletion.test.jsx (M — per-char + Skip tests)
- frontend/src/utils/language.js (M — comment refresh)
- frontend/src/utils/tokenizer.js (DELETED)
- frontend/src/utils/tokenizer.test.js (DELETED)

### Change Log
- 2026-06-10 — Reversed code-completion feedback token→character (per-letter Wordle), removed the tokenizer, and added a Skip button (advance without reveal; 6-guess cap retained). Frontend 176 / backend 294 green, lint clean (Story 4.8).
- 2026-06-11 — Code review (bmad-code-review): algorithm verified correct, all 8 ACs MET. Applied 2 patches (doc-comment accuracy; added a longer-attempt test → frontend 177). 1 deferred (no "right letter, wrong case" cue — inherent to 3-state Wordle; deferred-work.md), 3 dismissed. Status → done.
