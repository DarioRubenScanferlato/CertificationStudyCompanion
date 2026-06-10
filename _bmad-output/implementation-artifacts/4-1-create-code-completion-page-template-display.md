---
status: review
baseline_commit: 4cce825
---

# Story 4.1: Create CodeCompletion Page & Template Display

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-1-create-code-completion-page-template-display

## Story Statement

As a **student**,
I want **to see a code template with a blank to fill**,
So that **I can practice syntax**.

(FR-13 — PRD §4.x Code-Completion; epics.md Story 4.1.)

## Acceptance Criteria

**Given** I open a Code-Completion exercise
**When** the page loads
**Then** I see the prompt (e.g., "Configure Auto Loader to infer schema")
**And** the code template with the blank marked clearly (e.g., `___`)
**And** the target language is shown
**And** an input field is ready for me to type
**And** vitest tests cover the prompt/template/language/input rendering, and the backend session builder now delivers code-completion entries (pytest)

Acceptance detail (derived from FR-13, architecture, and the current code state):

- This story delivers the **page shell + template display + input affordance only**. The interactive Wordle loop — tokenizing, green/yellow/grey feedback, the guess counter, and answer reveal — arrives in Stories 4.2–4.5. The page is **built to integrate** those (it renders `<FeedbackTokens>` and the attempt loop once 4.4/4.5 land), but 4.1 itself just shows the template and accepts typed input.
- A Code-Completion exercise must actually **reach the runner**. Today the session builder **skips** code-completion (see Dev Notes); this story extends it so a code-completion session entry is delivered, and routes the `practice` view to a new `CodeCompletion.jsx` based on the current exercise's `type`.

## Architecture Context

### Cross-cutting decisions for ALL of Epic 4 (read once, applies to 4.1–4.5)

- **Feedback is CLIENT-SIDE (NFR-1).** The tokenizer (4.2) and the positional-feedback algorithm (4.3) run **in the browser**. NFR-1 requires "< 100ms from keystroke to rendered feedback… client-side computation; no perceptible server round-trip" (architecture.md lines 49, 92, 142–143), and the React technology choice is justified *entirely* by this. **The `POST /api/feedback/code-completion` endpoint mentioned in architecture.md (lines 363, 900, 906) is a documented inconsistency and is NOT implemented in Epic 4** — it would reintroduce the server round-trip NFR-1 forbids. Resolution: no new backend feedback endpoint; feedback is computed client-side. (The existing MCQ `POST /api/feedback` is untouched.)
- **Answer-delivery trade-off (consequence of client-side feedback).** Because the browser computes feedback, the code-completion **session entry carries the canonical answer + accepted alternatives** (`answer`, `accepted`, `caseSensitive`, `ignoreWhitespace`) to the client. This is a **deliberate, documented trade-off**: the Wordle drill inherently narrows to the answer through feedback and has **no multiple-choice gaming surface**, so shipping the answer for the *active* exercise is acceptable. This does **NOT** relax the MCQ non-leakage rule (FR-20) — MCQ Displayed Options still never carry `correct` flags. Code-completion and MCQ have different leakage models.
- **Tokenizer choice (AR-9):** regex-based, language-specific patterns; SQL keywords case-insensitive, PySpark/Python case-sensitive; non-semantic whitespace ignored. `tokenize(code, language) → [{token, type, position}]` (architecture.md lines 325–345). Built in 4.2.
- **Playfulness is load-bearing (architecture.md lines 39, 52, 87–88):** the Wordle guess-and-narrow feel is the differentiator, not a correctness checkbox. Keep the interaction delightful.
- **Backend tooling:** `uv` only — **NEVER pip** (project-context.md). Frontend tests are **vitest**, backend tests are **pytest**.

### This story specifically

- **`CodeCompletion` model already exists** in `backend/app/models.py` (lines 178–201): `BaseExercise` fields (`id`, `type`, `exam`, `domain`, `difficulty`, `question` (the prompt), `explanation`) plus `language: str`, `template: str` (validated to contain `___`), `answer: str` (validated non-empty), `accepted: list[str]`, `case_sensitive: bool = False`, `ignore_whitespace: bool = True`. `Exercise = MCQ | CodeCompletion`. **No model change is needed.**
- **The session builder currently SKIPS code-completion.** `backend/app/session.py` `build_session` (and `build_mock_session`) filter to `isinstance(ex, MCQ) and ex.type != ExerciseType.CODE_COMPLETION` (session.py lines ~276, ~316), and `build_session_entry(mcq: MCQ)` only knows the MCQ shape (sampled, flag-less `displayedOptions`). This story adds a **code-completion session-entry shape** and stops dropping these exercises.
- **The frontend already degrades code-completion gracefully.** `MCQPractice.jsx` returns `<UnsupportedExercise message="Code-completion exercises arrive in a later update." />` when `exercise.type === EXERCISE_TYPES.CODE_COMPLETION` (lines ~211–219). This story replaces that dead-end with real routing to `CodeCompletion.jsx`.
- **`EXERCISE_TYPES.CODE_COMPLETION = 'code_completion'`** already exists in `frontend/src/constants.js`.
- **`CodeBlock.jsx` (Story 3.7)** renders Prism-highlighted code (`sql`/`python`; `pyspark`→`python`; `clike` fallback), preserving whitespace in a `<pre>`. **Reuse it** to render the template — do not hand-roll a highlighter.
- **Routing:** `App.jsx` `CurrentView` switches on `view` (`practice | summary | stats | select`); `practice` currently renders `<MCQPractice/>` unconditionally. This story makes `practice` **dispatch by the current exercise's type** (MCQ → `MCQPractice`, code-completion → `CodeCompletion`). Prefer a tiny dispatcher (a `Practice` component or an inline branch reading `currentExercise.type` from `useSession()`) so a single session can mix types and the existing MCQ path is untouched.

### Proposed code-completion session-entry shape

`build_session` should emit, for a `CodeCompletion`:

```python
{
  "exerciseId": cc.id,
  "type": "code_completion",
  "domain": cc.domain.value,
  "difficulty": cc.difficulty,           # match the MCQ entry's difficulty serialization
  "language": cc.language,
  "prompt": cc.question,                 # the BaseExercise `question` is the prompt
  "template": cc.template,               # contains the ___ blank
  "answer": cc.answer,                   # canonical (client-side feedback; see trade-off above)
  "accepted": cc.accepted,
  "caseSensitive": cc.case_sensitive,
  "ignoreWhitespace": cc.ignore_whitespace,
  "explanation": cc.explanation,         # rendered only after the exercise concludes (FR-17, story 4.5)
  "references": getattr(cc, "references", []),
}
```

(Mirror the existing MCQ `build_session_entry` field-naming conventions — camelCase keys, `domain`/`difficulty` serialized exactly as the MCQ entry does. Confirm against the live MCQ entry rather than guessing.)

## Tasks / Subtasks

- [x] **Task 4.1.1 — Stop dropping code-completion in the session builder** (`backend/app/session.py`)
  - [x] Add a `build_code_completion_entry(cc: CodeCompletion) -> SessionEntry` (or a typed dict builder) producing the shape above; keep `build_session_entry` (MCQ) untouched.
  - [x] In `build_session`, include `CodeCompletion` exercises: route MCQs through the MCQ builder and code-completions through the new builder, preserving the existing **unseen-first ordering** (FR-24) and **randomization** behavior for the combined list. Do **not** sample/shuffle options for code-completion (it has none).
  - [x] Decide and document mock-exam behavior: `build_mock_session` is **MCQ-only by design** (domain-weighted MCQ blueprint, Epic 8) — leave it excluding code-completion. Only `build_session`/replay deliver code-completion.
  - [x] Confirm `find_exercise` / `POST /api/feedback` is unaffected (MCQ-only grading stays MCQ-only; code-completion is graded client-side, so it never hits `POST /api/feedback`).
- [x] **Task 4.1.2 — `getSession` plumbing is automatic, but verify the API contract** (`backend/app/main.py`, `frontend/src/api.js`)
  - [x] `GET /api/sessions` already returns whatever `build_session` produces — once 4.1.1 emits code-completion entries they flow through. Verify no MCQ-shaped assumption in the route (e.g. it must not assume every entry has `displayedOptions`).
  - [x] `frontend/src/api.js` `getSession` returns the raw entries array unchanged — confirm it does not coerce/validate to the MCQ shape.
- [x] **Task 4.1.3 — Create `frontend/src/pages/CodeCompletion.jsx`** (NEW)
  - [x] Read `currentExercise` from `useSession()`; render: the **prompt** (`prompt`/`question`), the **template** via `<CodeBlock code={template} language={language}>` with the `___` blank visually emphasized, a **language** badge, and a **text input** (single-line `<input>` or `<textarea>` — single-line/fill-in-blank scope per architecture.md line 39) for the answer.
  - [x] Mark the blank clearly (e.g., a styled `___` or a labeled slot) so it's obvious what to fill.
  - [x] Include a disabled-until-non-empty **Submit/Guess** button and a **remaining-attempts** placeholder region — these become live in 4.4/4.5. Keep local component state for the typed attempt.
  - [x] Reuse the Practice surface conventions: the `flex items-center gap-4 mb-4` header with domain/difficulty badges + the neutral **End session** control + the `useRegisterExitConfirm` wiring, mirroring `MCQPractice.jsx`, so ending/exiting a code-completion exercise routes through the same confirm/partial-summary flow (Story 6.4). Reuse `ProgressBar`.
  - [x] Accessibility: label the input (`htmlFor`/`id`); the template `<pre>` is readable; do not rely on color alone for the blank.
- [x] **Task 4.1.4 — Route the `practice` view by exercise type** (`frontend/src/App.jsx`, `frontend/src/pages/MCQPractice.jsx`)
  - [x] In `App.jsx` `CurrentView`, when `view === 'practice'` render a dispatcher that reads `currentExercise.type` and renders `<CodeCompletion/>` for `code_completion`, else `<MCQPractice/>`. Keep `summary`/`stats`/`select` unchanged.
  - [x] Remove the code-completion `UnsupportedExercise` dead-end from `MCQPractice.jsx` (lines ~211–219) **only after** the dispatcher guarantees code-completion never reaches MCQPractice. Keep the malformed-MCQ guard (the 4-displayed-options guard) intact.
  - [x] Preserve the `ExitConfirmContext` registration / header Home flow for both runners.
- [x] **Task 4.1.5 — Author at least one real code-completion exercise** (`exercises/...`)
  - [x] There is **no code-completion content yet**. Add 2–3 grounded code-completion items (SQL + PySpark) following the `CodeCompletion` model (`type: code_completion`, `language`, `template` with `___`, `answer`, `accepted`, `case_sensitive`, `ignore_whitespace`, `explanation`, `references`). Use **current Databricks terminology** (Lakeflow Declarative Pipelines + `dp`, Lakeflow Jobs, Unity Catalog — see the `write-mcq` skill's terminology rules) and continue the existing `id` sequence. This unblocks manual + automated verification of the page and the 4.2–4.5 loop.
  - [x] Validate the new content loads (content loader / models) without errors.
- [x] **Task 4.1.6 — Tests**
  - [x] **pytest** (`backend/tests/`): `build_session` now includes code-completion entries with the documented shape (no `displayedOptions`; carries `template`/`answer`/`accepted`/`language`/`caseSensitive`/`ignoreWhitespace`); MCQ entries are unchanged; `GET /api/sessions` returns mixed-type sessions; `build_mock_session` still excludes code-completion.
  - [x] **vitest** (`frontend/src/pages/CodeCompletion.test.jsx`, NEW): given a code-completion session entry, the page renders the prompt, the template (with the blank), the language, and an input; the Submit/Guess control is disabled until input is non-empty; ending the session routes through the exit flow. Add/extend an `App` routing test that a `code_completion` current exercise renders `CodeCompletion` (not `MCQPractice`), and an MCQ still renders `MCQPractice`.

## Dev Notes

### NEW files
- `frontend/src/pages/CodeCompletion.jsx` — the code-completion runner page (display + input shell this story; full loop by 4.5).
- `frontend/src/pages/CodeCompletion.test.jsx` — page-display tests.
- `exercises/...` — first real code-completion content (SQL + PySpark).

### UPDATE files
- `backend/app/session.py` — emit code-completion session entries (new entry builder); stop filtering them out of `build_session`. **Preserve:** MCQ `build_session_entry` (sampled, flag-less `displayedOptions`), unseen-first ordering (FR-24), randomization (FR-20/21), and `build_mock_session` staying MCQ-only.
- `frontend/src/App.jsx` — type-based dispatch for the `practice` view. **Preserve:** the `select|practice|summary|stats` switch, `ExitConfirmContext`, the header Home/Stats wiring.
- `frontend/src/pages/MCQPractice.jsx` — remove the code-completion dead-end once routing handles it. **Preserve:** the radiogroup/Submit/Feedback flow, keyboard shortcuts (Story 6.5), Exit-confirm (6.4), per-question timing (8.2), and the malformed-MCQ guard.
- (Verify-only) `backend/app/main.py` `GET /api/sessions`, `frontend/src/api.js` `getSession` — must not assume the MCQ entry shape.

### Backend tooling
- Use `uv` for any backend deps/commands (e.g. `uv run pytest`). **Never pip** (project-context.md).

### Dependencies
- **Independent** of 4.2–4.5 for the display + backend-delivery scope. The interactive loop layered onto this page depends on 4.2 (tokenizer), 4.3 (feedback), 4.4 (rendering), 4.5 (guess loop). Build 4.1 so those drop in (a clear seam where `<FeedbackTokens>` and the attempt state will mount).

### References
- [Source: `_bmad-output/planning-artifacts/epics.md`#Story-4.1] — ACs (lines ~555–569); Epic 4 overview (lines ~228–235); schema BDD "Code-Completion template includes id, type, language, prompt, template, answer, accepted" (line ~372); FR-13 (line 49).
- [Source: `_bmad-output/planning-artifacts/architecture.md`] — Code-Completion novelty + single-line scope (line 39); **NFR-1 client-side <100ms** (lines 49, 92, 142–143); playfulness (lines 52, 87–88); tokenizer decision/AR-9 (lines 325–345); API contract incl. the to-be-ignored `code-completion` endpoint (lines 363, 900, 906); component boundaries (lines 903–910); FE file structure (lines 612–616, 833–854).
- [Source: `backend/app/models.py`] — `CodeCompletion` model (lines 178–201); `Exercise = MCQ | CodeCompletion` (line 205).
- [Source: `backend/app/session.py`] — code-completion currently skipped (lines ~276, ~316); MCQ `build_session_entry` (lines ~181–209).
- [Source: `frontend/src/pages/MCQPractice.jsx`] — code-completion `UnsupportedExercise` dead-end (lines ~211–219); header/Exit-confirm conventions.
- [Source: `frontend/src/components/CodeBlock.jsx`] — Prism template renderer to reuse.
- [Source: `frontend/src/App.jsx`] — `CurrentView` view switch (lines ~27–40).
- [Source: `_bmad-output/project-context.md`] — uv only, never pip.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story workflow, 2026-06-09; finalized alongside 4.2–4.5).

### Completion Notes List

- Page shell shipped earlier: `CodeCompletion.jsx` renders the prompt, the code template with its `___` blank (via `CodeBlock`), the target language, and the typed-answer input, with the shared Exit-confirm header (`useRegisterExitConfirm`).
- Backend delivery + routing in place: `session.py` `build_session` delivers code-completion entries (carrying `language/template/answer/accepted/caseSensitive/ignoreWhitespace/explanation/references`); `App.PracticeRouter` routes `code_completion` → `CodeCompletion` by `type`.
- The interactive loop (4.2–4.5) was layered onto this shell; the page is now fully playable.
- Verified via App.test.jsx (routes code_completion to the runner) and the CodeCompletion guess-loop suite.

### File List

- frontend/src/pages/CodeCompletion.jsx (shell; extended by 4.5)
- frontend/src/App.jsx (PracticeRouter routes code_completion)
- backend/app/session.py (build_session delivers code-completion entries)

### Change Log

- 2026-06-09 — Confirmed page shell + backend delivery + routing complete; closed out alongside the Epic 4 runner (Story 4.1).
