---
status: review
baseline_commit: 4cce825
---

# Story 4.3: Implement Positional Feedback Algorithm

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-3-implement-positional-feedback-algorithm

## Story Statement

As **the app**,
I want **to compute green/yellow/grey feedback**,
So that **users get Wordle-style hints**.

(FR-14, FR-16, NFR-1 — epics.md Story 4.3.)

## Acceptance Criteria

**Given** the user types code and submits
**When** the feedback algorithm runs
**Then** each token is colored: **green** (correct token, correct position), **yellow** (token is in the answer but wrong position), **grey** (token not in the answer)
**And** feedback is computed in **< 100ms** (client-side)
**And** **alternative accepted answers** are matched correctly (the attempt is scored against whichever accepted form fits best)
**And** vitest tests cover green/yellow/grey classification, Wordle duplicate-token handling, accepted-alternative matching, case rules per language, and the <100ms budget

Acceptance detail:

- Pure, client-side function: `computeFeedback(attempt, canonical, language, options) → [{ token, color, position }]`, where `color ∈ {'green','yellow','grey'}`, `options = { accepted = [], caseSensitive, ignoreWhitespace }`. No React, no network.
- **Token-level Wordle semantics** (not character-level): tokenize both the attempt and the target with Story 4.2's `tokenize`, then color the **attempt's** tokens.
- **Accepted alternatives (FR-16):** the target set is `[canonical, ...accepted]`. Score the attempt against each candidate and return the **best** result (e.g. the candidate that maximizes greens, then yellows) so a user typing a valid alternative isn't penalized.

## Architecture Context

- **`computeFeedback(attempt, canonical, language)` → token colors (green/yellow/grey)** is the named architecture contract (architecture.md lines 337, 71): "green (correct token, correct position) / yellow (correct token, wrong position) / grey (absent)." Extend the signature with an `options`/`accepted` argument to satisfy FR-16.
- **Built on Story 4.2's tokenizer.** Use `tokenize(code, language)` for both attempt and each candidate; never re-implement tokenization here. Whitespace insensitivity and language case rules come "for free" from 4.2 — but this story owns the **comparison** rule: SQL keyword comparison is case-insensitive; PySpark/Python identifier comparison is case-sensitive. Honor the `caseSensitive` flag carried on the exercise (model default `False`; from the session entry, Story 4.1) and/or the language default.
- **Wordle algorithm correctness (the subtle part):** classify in **two passes** to handle duplicate tokens exactly like Wordle:
  1. First pass — mark **green** every attempt token equal to the target token at the **same position**; decrement those from a per-token "remaining counts" multiset of the target.
  2. Second pass — for each non-green attempt token, mark **yellow** iff that token still has remaining count in the target multiset (then decrement); otherwise **grey**.
  This prevents a repeated attempt token from showing more yellows than the target actually contains.
- **< 100ms, client-side (NFR-1; architecture.md lines 49, 92, 142–143).** Two tokenizations + two linear passes per candidate; with a handful of accepted alternatives this is microseconds. No async, no server call. (Reaffirms the Epic-4 decision: **no `POST /api/feedback/code-completion`** — feedback is computed here, in the browser.)
- **Pure function, fully unit-testable** — the reason this is its own story separate from rendering (4.4).

## Tasks / Subtasks

- [x] **Task 4.3.1 — Create `frontend/src/utils/codeFeedback.js`** (NEW)
  - [x] Export `computeFeedback(attempt, canonical, language, options = {})` returning `[{ token, color, position }]` aligned to the **attempt's** token order (so 4.4 renders the user's tokens left-to-right with colors).
  - [x] Tokenize attempt + each candidate via `tokenize` (Story 4.2). Build the target token multiset honoring the comparison rule (case-insensitive for SQL keywords; case-sensitive for Python/PySpark identifiers; respect `options.caseSensitive`).
  - [x] Implement the **two-pass green/yellow/grey** classification above (correct duplicate handling).
  - [x] **Accepted alternatives:** compute feedback against `[canonical, ...(options.accepted||[])]`; return the best (max greens, tiebreak max yellows). Also expose a derived **solved** signal (all-green against some candidate ⇒ exact/accepted match) — or document that "solved" = every color is green, so Story 4.5 can detect a win without re-deriving it.
  - [x] Keep it pure/synchronous; no React/DOM.
- [x] **Task 4.3.2 — Tests** (`frontend/src/utils/codeFeedback.test.js`, NEW — vitest)
  - [x] All-correct attempt → all green (and the solved signal is true).
  - [x] Right tokens, wrong order → yellows where appropriate, greens for any already-in-position.
  - [x] Extraneous/absent tokens → grey.
  - [x] **Duplicate-token Wordle rule:** an attempt repeating a token that appears once in the target gets one green/yellow and the rest grey (assert the count, not just presence).
  - [x] **Accepted alternative:** `canonical = "cloudFiles.schemaLocation"`, `accepted = ["..."]` — typing the accepted form scores all-green / solved.
  - [x] **Case rules:** SQL `select` vs `SELECT` are equal (case-insensitive); PySpark `df` vs `DF` are not (case-sensitive); `caseSensitive` option override respected.
  - [x] **Whitespace insensitivity** flows through (inherited from 4.2): `SELECT  *` vs `SELECT *` produce identical feedback.
  - [x] **Perf:** a realistic line computes in < 100ms (assert an upper bound generously, e.g. < 50ms, to keep the NFR-1 guardrail meaningful without flakiness).

## Dev Notes

### NEW files
- `frontend/src/utils/codeFeedback.js` — `computeFeedback(...)` (green/yellow/grey + accepted-alternatives + solved signal).
- `frontend/src/utils/codeFeedback.test.js` — vitest unit tests.

### Preserve / do not touch
- No backend changes; no UI. This is the pure scoring engine consumed by 4.4 (rendering) and 4.5 (guess loop).

### Dependencies
- **Depends on Story 4.2** (`tokenize`). Story 4.4 (`FeedbackTokens` rendering) and Story 4.5 (guess loop) consume this. Independent of 4.1's page beyond sharing the session-entry fields (`answer`, `accepted`, `caseSensitive`).

### Naming note
- The file may be `codeFeedback.js` (avoids colliding with the MCQ feedback concept and the backend `feedback.py`). Keep the module name self-evidently about *code-completion* feedback; co-locate the `.test.js`.

### References
- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-4.3] — ACs (lines ~588–600); FR-14 (line 51), FR-16 (line 176).
- [Source: `_bmad-output/planning-artifacts/architecture.md`] — green/yellow/grey definition (line 71); `computeFeedback()` contract (line 337); NFR-1 client-side <100ms (lines 49, 92, 142–143); the to-be-ignored server endpoint (lines 363, 900, 906).
- [Source: `backend/app/models.py`] — `accepted`, `case_sensitive`, `ignore_whitespace` fields these inputs come from (lines 185–187).
- Story 4.2 — `tokenize(code, language)` contract (consumed here).

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story workflow, 2026-06-09).

### Completion Notes List

- `computeFeedback(attempt, canonical, language, {accepted, caseSensitive, ignoreWhitespace})` → `[{token, color, position}]` aligned to the attempt's tokens, with a derived `result.solved` boolean.
- Two-pass Wordle classification (pass 1 greens by position decrementing a target multiset; pass 2 yellows from remaining counts, else grey) — correct duplicate-token handling.
- Scores against `[canonical, ...accepted]`, returns the best candidate (most greens → most yellows; solved wins). Case rule honors `caseSensitive`, defaulting by language.
- 14 vitest tests (green/yellow/grey, duplicate rule, accepted alternatives, case rules, whitespace passthrough, perf, empty canonical) — green.

### File List

- frontend/src/utils/codeFeedback.js (NEW)
- frontend/src/utils/codeFeedback.test.js (NEW)

### Change Log

- 2026-06-09 — Implemented client-side positional-feedback engine + 14 unit tests (Story 4.3).
- 2026-06-10 — Code-review fix: `computeFeedback` now returns `{tokens, solved}` (was a monkey-patched array property that spreads/clones silently dropped). Language case rule sourced from the shared `LANGUAGE_ALIASES` (utils/language.js).
