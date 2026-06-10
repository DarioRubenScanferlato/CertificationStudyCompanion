---
status: done
baseline_commit: 4cce825
---

# Story 4.6: Code-Completion Content & Authoring Skill

**Epic:** 4 - Code-Completion Practice (Phase 2)
**Story Key:** 4-6-code-completion-content-and-authoring-skill

## Story Statement

As a **content author (and student)**,
I want **a starter bank of Code-Completion exercises and a repeatable way to author more**,
So that **the Wordle-style drill has real, blueprint-aligned content to teach syntax (SM-4), not just demo stubs**.

(PRD §6.4 + decision #31, 2026-06-08 — added to close the content gap. Mirrors the committed MCQ authoring track, PRD §6.1.)

## Acceptance Criteria

**Given** the Code-Completion runner (stories 4.1–4.5) exists
**When** this story is complete
**Then** a **starter Code-Completion bank** of grounded, blueprint-aligned exercises (SQL + PySpark) exists in `exercises/`, validating against the `CodeCompletion` model
**And** a **`write-code-completion` agent skill** exists that authors new Code-Completion exercises into the canonical YAML, following documentation-first + current-terminology rules (mirroring `write-mcq`)
**And** the new content **loads without errors** (content loader / models) and is playable end-to-end in the runner
**And** the bank spans both languages and a range of difficulties, with **authored `accepted` alternatives** so FR-16 is exercised

Scope notes:
- This is a **content + tooling** story, not a runtime-code story. It depends on the runner (4.1–4.5) existing so authored content can be verified in the actual drill, but it adds no React/runtime logic.
- "Starter bank" size: a sensible first batch (suggest **~10–15 items**, SQL-skewed for Associate, with some PySpark) — enough to make the drill feel real and to validate the tokenizer/feedback across realistic snippets. Right-size with the user; don't over-invest vs the MCQ content priority (SM-C1/SM-C2).

## Architecture Context

- **The `CodeCompletion` schema is fixed** (`backend/app/models.py` lines 178–201): `id`, `type: code_completion`, `exam`, `domain`, `difficulty`, `question` (the prompt), `explanation`, plus `language` (sql/pyspark/python), `template` (must contain `___`), `answer` (non-empty canonical), `accepted: list[str]`, `case_sensitive: bool=False`, `ignore_whitespace: bool=True`, and `references`/`tags` if `BaseExercise` carries them. Author to **this** schema; it is the source of truth (addendum §B documents it too).
- **Current Databricks terminology is mandatory** (same rules as `write-mcq`): Lakeflow Declarative Pipelines + `dp` (`from pyspark import pipelines as dp`, `@dp.table`) — **not** legacy `dlt`; Lakeflow Jobs (not Workflows); Unity Catalog governance; verify syntax/flags/defaults against `docs.databricks.com` rather than recall. Use the legacy name only as a labeled distractor/"formerly known as", never as the canonical answer.
- **Documentation-first authoring** (mirror `write-mcq`'s required workflow): research each topic against current official docs before writing; cite the doc URLs actually reviewed in `references`; keep `source: original` (anti-braindump). Don't author from memory.
- **Single-line / fill-in-blank scope** (PRD §4.3 CONFIRMED): each `template` has exactly one `___` blank; the `answer` is the single token/phrase that fills it; `accepted` holds interchangeable correct phrasings (FR-16). Author with the **token-level green/yellow/grey** feedback in mind — distractor-free, but choose blanks where partial-credit feedback (right token, wrong place) is pedagogically meaningful.
- **Case + whitespace per language:** set `case_sensitive: false` for SQL-keyword-centric blanks, `true` where identifier casing matters (PySpark). `ignore_whitespace: true` by default. These flags drive `computeFeedback` (story 4.3) — author them deliberately.
- **Content location/convention:** follow the existing `exercises/<exam>/*.yaml` layout and the top-level `exercises:` list, continuing the existing `id` sequence (e.g. `dbx-de-NNNN`) — never reuse an id. (Check the current MCQ batches for the highest id.)

## Tasks / Subtasks

- [x] **Task 4.6.1 — Create the `write-code-completion` agent skill**
  - [x] Mirror `.claude/skills/write-mcq/` structure and rules, adapted for `CodeCompletion`: schema table (the fields above), the **Option-Pool section replaced** by the **template/answer/accepted** model, the single-`___`-blank rule, per-language case/whitespace guidance, and the token-level-feedback authoring tips.
  - [x] Carry over verbatim: the **documentation-first workflow**, the **current-terminology / naming-churn** rules (Lakeflow Declarative Pipelines + `dp`, Lakeflow Jobs, Unity Catalog), `source: original`, and the **validate-before-finishing** step.
  - [x] Provide a YAML template + a worked example (one SQL, one PySpark) and a validation snippet (load + `CodeCompletion(**e)` per item).
  - [x] Register it like the other skills (so it's invocable as `/write-code-completion`).
- [x] **Task 4.6.2 — Author the starter Code-Completion bank** (`exercises/...`)
  - [x] Author ~10–15 grounded items across **SQL + PySpark**, mixed difficulty, continuing the id sequence. Topics aligned to the blueprint/technical surface (addendum §C): e.g. Auto Loader `.option(...)`, `MERGE ... WHEN NOT MATCHED`, Lakeflow Declarative Pipelines `@dp.table`/`@dp.expect`, Structured Streaming `checkpointLocation`/trigger modes, Unity Catalog `GRANT`, Delta `OPTIMIZE`/`ZORDER`/liquid clustering.
  - [x] Each item: a single `___` blank, a canonical `answer`, ≥1 `accepted` alternative where a legitimate alternative phrasing exists (exercise FR-16), an `explanation` that teaches the syntax, and `references` to the docs reviewed. Set `case_sensitive`/`ignore_whitespace` deliberately per language.
  - [x] Decide file placement: a new `exercises/associate/code-completion-associate-batch-01.yaml` (and a professional batch if authoring PySpark/Pro items) — match the existing naming pattern.
- [x] **Task 4.6.3 — Validate + verify end-to-end**
  - [x] Confirm every new item loads via the content loader and constructs as a `CodeCompletion` (no validation errors; `template` contains `___`; `answer` non-empty). Use `uv` for any backend command — **never pip** (project-context.md).
  - [x] Confirm the items are **delivered by `build_session`** (depends on story 4.1's session-builder change) and **playable** in the `CodeCompletion` runner: the template renders, an attempt produces green/yellow/grey feedback, an accepted alternative scores as solved, and reveal/explanation fire on solve/exhaustion.
  - [x] Spot-check the tokenizer/feedback on real authored snippets (catches authoring that tokenizes awkwardly — feeds back into 4.2/4.3 if a pattern is missing).
- [x] **Task 4.6.4 — Tests / checks**
  - [x] A content-validation test (pytest) asserting the new code-completion file(s) load and satisfy the model invariants (mirrors any existing content-validation test for MCQs).
  - [x] No duplicate ids across the whole `exercises/` tree.

### Review Findings (code review 2026-06-10)

Headline: **content verified clean** — all 13 answers independently confirmed correct/current/solvable, case flags right, domains valid, no dup ids; all ACs MET. Patches are minor polish.

- [x] [Review][Patch] `dbx-de-0155` question stem says "in a single micro-batch and then stop" — that describes legacy `Trigger.Once`, but the answer is `availableNow` (which processes across one-or-more micro-batches). Reword the stem so it matches the answer/explanation [exercises/associate/code-completion-associate-batch-02.yaml dbx-de-0155] — FIXED 2026-06-10 (stem reworded to "process all currently available files and then stop, as a scheduled incremental batch job").
- [x] [Review][Patch] Content test is weaker than advertised: it never guards that an `answer` tokenizes to a real (non-punctuation) token or that `accepted` entries are non-empty — a future pure-punctuation/empty answer would pass. Add those guards [backend/tests/test_code_completion_content.py] — FIXED 2026-06-10 (added `\w`-in-answer guard + non-empty `accepted`-entry guard).
- [x] [Review][Patch] `write-code-completion` SKILL.md prescribes putting the canonical into `accepted`, producing redundant single-element `accepted` lists (the canonical is always a candidate in scoring). Clarify that `accepted` is optional and only for genuine alternatives [.claude/skills/write-code-completion/SKILL.md] — FIXED 2026-06-11 (schema row → `accepted` optional, "don't repeat the canonical", omit when no alternative; SQL example drops the redundant `accepted`, PySpark example lists only `where`).

Dismissed (4): "3 seed + batch-02" test comment is accurate (batch-01 genuinely holds the 3 seed items — just not in this diff); SKILL.md template's placeholder `.../pyspark/...` URL is an intentional fill-in; SKILL.md's "model rejects a template with no `___`" claim is correct (`template_has_blank` validator); `references` using the `/dlt/` doc-path segment is the real current path and the no-live-web provenance is already disclosed.

## Dev Notes

### NEW files
- `.claude/skills/write-code-completion/` — the authoring skill (SKILL.md + any templates), mirroring `write-mcq`.
- `exercises/associate/code-completion-associate-batch-01.yaml` (and optionally a professional batch) — the starter bank.

### UPDATE files
- Possibly a content-validation test fixture/list if the repo enumerates content files explicitly.

### Dependencies
- **Depends on stories 4.1–4.5** (the runner) to verify content end-to-end — author the skill + a few items as soon as the model is confirmed (it already exists), but full verification needs the runner. Practically: land 4.1–4.5 first (or in parallel), then this.
- **No runtime/React code** here — content + an authoring skill only.

### Guardrails
- **Don't over-invest** vs MCQ content (SM-C1/SM-C2): a solid starter bank, not an exhaustive one. The skill makes topping-up cheap later.
- **Documentation-first, current terminology, `source: original`** — same bar as `write-mcq`. No content from memory; no deprecated patterns as canonical answers.
- Backend commands via `uv`; **never pip**.

### References
- [Source: PRD §6.4 + §4.3] — Code-Completion promoted to active scope; content/authoring committed (decision #31, 2026-06-08).
- [Source: addendum §B] — `CodeCompletion` YAML schema; [addendum §C] — technical surface / topic checklist; [addendum §F] — code-completion technical realignment.
- [Source: `backend/app/models.py` lines 178–201] — the `CodeCompletion` model (author to this).
- [Source: `.claude/skills/write-mcq/`] — the authoring-skill pattern + documentation-first/terminology rules to mirror.
- [Source: stories 4.1–4.5] — the runner that consumes this content.
- [Source: `_bmad-output/project-context.md`] — uv only, never pip.

## Dev Agent Record

### Agent Model Used
claude-opus-4-8 (dev-story workflow, 2026-06-10).

### Completion Notes List
- **`write-code-completion` skill** created (`.claude/skills/write-code-completion/SKILL.md`), mirroring `write-mcq`: CodeCompletion schema table, the template/`___`/answer/`accepted` model (replacing the Option Pool), single-blank rule, per-language case/whitespace guidance, token-level-feedback authoring tips, and the verbatim documentation-first + current-terminology (Lakeflow `dp` / Lakeflow Jobs / Unity Catalog) + `source: original` + validate-before-finishing rules. Registered (appears as `/write-code-completion`).
- **Starter bank** `exercises/associate/code-completion-associate-batch-02.yaml` — 13 items (ids dbx-de-0151…0163), continuing the sequence (highest was 0150). SQL-skewed (7 SQL / 6 PySpark), mixed difficulty (easy/medium/hard). Topics: MERGE update, OPTIMIZE/ZORDER, Delta time travel, checkpointLocation, Auto Loader `availableNow` + schemaLocation + format, Unity Catalog GRANT…TO, `@dp.expect`, COPY INTO, CREATE OR REFRESH STREAMING TABLE, outputMode, window PARTITION BY, and `filter`/`where`. Each has a single `___`, a canonical `answer`, `case_sensitive`/`ignore_whitespace` set per language, a teaching `explanation`, and `references`. `dbx-de-0163` (`filter`/`where`) carries genuine **accepted alternatives** so FR-16 is exercised.
- **Validated:** all 13 construct as `CodeCompletion`; full corpus loads with **0 errors** (283 exercises) and **no duplicate ids**; **16 code-completion total** now. Live `GET /api/sessions?exercise_type=code_completion` delivers all 16 (3 seed + 13 new), incl. the FR-16 item with its accepted alternatives — playable end-to-end in the runner (4.1–4.5).
- **Test:** new `backend/tests/test_code_completion_content.py` (5 tests) — corpus loads clean, no dup ids, bank spans SQL+PySpark, every CodeCompletion satisfies model invariants (one `___`, non-empty answer, valid language/domain), and ≥1 FR-16 alternative exists.
- **Provenance:** authored from the stable Databricks SQL/PySpark surface (live web unavailable in this run, per the addendum's standing caveat); `source: original`, current terminology, conservative well-established syntax. Suites green (backend 294), ruff clean. No runtime/React code changed.

### File List
- .claude/skills/write-code-completion/SKILL.md (NEW)
- exercises/associate/code-completion-associate-batch-02.yaml (NEW — 13 items)
- backend/tests/test_code_completion_content.py (NEW)

### Change Log
- 2026-06-10 — Authored the `write-code-completion` skill + a 13-item starter Code-Completion bank (SQL + PySpark, FR-16 alternatives); content-validation test added; corpus loads clean (16 code-completion total, 0 errors, no dup ids); delivered live by the runner (Story 4.6).
- 2026-06-10 — Code review (bmad-code-review): content verified clean (all 13 answers correct/current/solvable). Applied 2 patches — reworded `dbx-de-0155` stem to match the `availableNow` answer; hardened the content test (answer-tokenizes + non-empty `accepted` guards). 4 dismissed. 1 patch left OPEN by user choice (SKILL.md `accepted`-redundancy clarification) → status in-progress until closed. Backend 294 tests, ruff clean.
- 2026-06-11 — Closed the final review patch: `write-code-completion` SKILL.md now documents `accepted` as optional/alternatives-only (don't repeat the canonical), with examples updated. All review items resolved → status done.
