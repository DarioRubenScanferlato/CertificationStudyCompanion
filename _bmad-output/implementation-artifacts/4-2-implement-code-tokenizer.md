---
status: review
baseline_commit: 4cce825
---

# Story 4.2: Implement Code Tokenizer

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-2-implement-code-tokenizer

## Story Statement

As **the app**,
I want **to tokenize code for feedback**,
So that **I can give per-token feedback**.

(AR-9, FR-14 prerequisite — epics.md Story 4.2.)

## Acceptance Criteria

**Given** a user types code into the input
**When** tokenization happens
**Then** the tokenizer splits the code into tokens (keywords, identifiers, operators, literals)
**And** tokenization is language-specific (SQL case-insensitive, PySpark case-sensitive)
**And** non-semantic whitespace is ignored
**And** vitest tests cover SQL + PySpark tokenization, case rules, whitespace insensitivity, and the `{token, type, position}` output shape

Acceptance detail:

- The tokenizer is a **pure, client-side function** with **no UI and no React** — it is consumed by the positional-feedback algorithm (Story 4.3) and ultimately the rendering (4.4). Building it in isolation with thorough unit tests is the point of this story.
- Output: `tokenize(code, language)` → an **ordered array of `{ token, type, position }`** (architecture.md line 336), where `position` is the token's index in the emitted sequence (0-based), `type ∈ {keyword, identifier, operator, literal, punctuation}` (extend only if a language needs it), and **non-semantic whitespace is not emitted as tokens**.
- **Language-specific behavior:** SQL keywords are matched **case-insensitively** (so `SELECT`/`select` tokenize as the same keyword), while **PySpark/Python identifiers are case-sensitive** (`df` ≠ `DF`). The function must not *destroy* the original casing (the renderer shows what the user typed) — case rules govern *classification/matching*, captured so Story 4.3 can compare correctly. Provide a stable, documented contract for how case is represented (e.g. keep `token` as-typed and expose a normalized form, or document that comparison is the consumer's job using the language rule).

## Architecture Context

- **Regex-based, language-specific tokenizer (AR-9, the chosen MVP approach).** architecture.md (lines 325–345): "No need for a full parser; tokens are sufficient (keywords, identifiers, operators, literals). Language-specific patterns (SQL vs. PySpark) can be simple regexes. If tokenization becomes a bottleneck, replace with a proper lexer later." Example SQL pattern given:
  ```javascript
  const sqlTokenPattern = /(\bSELECT\b|\bFROM\b|[a-zA-Z_]\w*|'[^']*'|\d+|[(),.;])/gi;
  const tokens = code.match(sqlTokenPattern);
  ```
  Treat this as a **starting sketch**, not the final pattern — produce typed tokens (`{token, type, position}`), not a bare string array.
- **Implementation contract (architecture.md line 336):** `tokenize(code, language) → array of {token, type, position}`. This is the seam Story 4.3's `computeFeedback(attempt, canonical, language)` builds on, so the shape and ordering must be stable and deterministic.
- **Client-side & fast (NFR-1).** Runs in-browser; must be cheap enough that 4.3's feedback (which tokenizes attempt + canonical) stays well under the 100ms budget. Plain regex/scan, no async, no heavy deps.
- **Whitespace-insensitive (FR-13/FR-14 spirit; architecture.md line 39 "Whitespace-insensitive").** Spaces/tabs/newlines between tokens are non-semantic and must not appear as tokens nor shift positions — `SELECT  *` and `SELECT *` tokenize identically. (String literals preserve their internal whitespace — `'a b'` is one literal token.)
- **Languages in scope:** `sql`, `pyspark`, `python` (map `pyspark`→Python lexical rules; `py` alias acceptable — mirror `CodeBlock.jsx`'s `LANGUAGE_ALIASES`). Unknown language → a sensible generic fallback (identifier/operator/literal/punctuation split) rather than throwing, so the runner degrades instead of crashing.

## Tasks / Subtasks

- [x] **Task 4.2.1 — Create `frontend/src/utils/tokenizer.js`** (NEW)
  - [x] Export `tokenize(code, language)` returning an ordered `[{ token, type, position }]` with `position` = 0-based index in the emitted token stream.
  - [x] Implement **language-specific** regex sets: a SQL set (keyword list matched case-insensitively; identifiers, numeric/string literals, operators, punctuation) and a Python/PySpark set (Python keywords case-sensitive; identifiers case-sensitive; literals incl. strings with quotes, numbers; operators `= == != <= >= + - * / . , ( ) [ ] :` etc.; punctuation).
  - [x] **Skip non-semantic whitespace** (do not emit whitespace tokens; do not let it affect `position`). Preserve whitespace *inside* string literals.
  - [x] Classify each token into `keyword | identifier | operator | literal | punctuation`. Keep `token` as the **original substring** (renderer shows what was typed); document how case is normalized for comparison (per-language) so Story 4.3 can match correctly.
  - [x] Unknown/unsupported language → generic fallback tokenization (no throw).
  - [x] Keep it pure (no React, no DOM, no I/O) and synchronous.
- [x] **Task 4.2.2 — Tests** (`frontend/src/utils/tokenizer.test.js`, NEW — vitest)
  - [x] SQL: `SELECT * FROM t WHERE x = 1` → expected typed token sequence; `select` and `SELECT` classify as the same keyword (case-insensitive).
  - [x] PySpark/Python: `df.select("a")` → identifiers/operators/literals as expected; `df` ≠ `DF` (case-sensitive).
  - [x] Whitespace insensitivity: `SELECT   *` and `SELECT *` (and a newline variant) yield identical token sequences/positions.
  - [x] String literals: `'a b c'` (SQL) and `"a b"` (Python) are single literal tokens preserving inner spaces.
  - [x] Output shape: every element is `{ token, type, position }` with contiguous 0-based `position`.
  - [x] Unknown language does not throw and returns a reasonable split.
  - [x] (Optional perf sanity) tokenizing a ~200-char line is sub-millisecond — keeps the 4.3 budget safe.

## Dev Notes

### NEW files
- `frontend/src/utils/tokenizer.js` — pure regex tokenizer (`tokenize(code, language)`).
- `frontend/src/utils/tokenizer.test.js` — vitest unit tests.

> **Directory note:** if the repo has no `frontend/src/utils/` yet, create it (architecture.md FE structure lists `tokenizer.js` under a utils/lib location, line ~854). Match whatever utility-module convention the repo already uses (check where `api.js`/`constants.js` live — utilities currently sit at `frontend/src/`; a `utils/` subfolder is fine and is what the architecture names). Keep it co-located with its `.test.js`.

### Preserve / do not touch
- No backend changes. No React/UI changes. This is a leaf utility — Stories 4.3/4.4/4.5 import it.

### Dependencies
- **Independent** — can be built first or in parallel with 4.1. Story 4.3 (positional feedback) **depends on this**.

### References
- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-4.2] — ACs (lines ~572–584); AR-9 (line ~109).
- [Source: `_bmad-output/planning-artifacts/architecture.md`] — tokenizer decision + sketch + `tokenize()` contract (lines 325–345, 336); whitespace-insensitive (line 39); NFR-1 client-side <100ms (lines 49, 92, 142–143); FE file location for `tokenizer.js` (line ~854).
- [Source: `frontend/src/components/CodeBlock.jsx`] — `LANGUAGE_ALIASES` (sql/python/py/pyspark) to mirror for language mapping.
- [Source: `_bmad-output/project-context.md`] — frontend tests are vitest.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story workflow, 2026-06-09).

### Completion Notes List

- Pure regex tokenizer `tokenize(code, language)` → `[{token, type, position}]`. Single master scanner; whitespace skipped (not emitted, never shifts positions); string literals preserve inner whitespace.
- SQL keywords matched case-insensitively; Python/PySpark keywords + identifiers case-sensitive; original casing preserved on `token`. Unknown language → generic split (no throw).
- 12 vitest tests (SQL + PySpark, case rules, whitespace, string literals, shape, empty/null, unknown language, sub-ms perf) — green.

### File List

- frontend/src/utils/tokenizer.js (NEW)
- frontend/src/utils/tokenizer.test.js (NEW)

### Change Log

- 2026-06-09 — Implemented pure client-side tokenizer + 12 unit tests (Story 4.2).
