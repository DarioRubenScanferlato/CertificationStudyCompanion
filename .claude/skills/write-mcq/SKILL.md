---
name: write-mcq
description: Author Databricks DE certification multiple-choice questions as schema-valid YAML matching exercises/associate/mcq-associate-batch-01.yaml and the canonical schema in the BMad addendum. Questions are single-select Option Pools grounded in current official Databricks documentation. Use when the user asks to write, generate, add, or create MCQ questions / exercises / practice questions for the study companion.
---

# Write MCQ Exercises

**Goal:** Produce multiple-choice questions for the Databricks Data Engineer certification study companion as YAML that validates against the project's Pydantic models, matches the structure of `exercises/associate/mcq-associate-batch-01.yaml`, and follows the canonical schema and authoring rules in the BMad addendum (`_bmad-output/planning-artifacts/prds/prd-*/addendum.md`, §B and §C). Every question is **single-select**, authored as an **Option Pool**, and grounded in **current official Databricks documentation** with **up-to-date terminology**.

## Authoritative sources (read these first)
- **Schema source of truth:** `backend/app/models.py` (Pydantic models).
- **Canonical authoring schema + rules:** the BMad addendum §B (field set, Option Pool model) and §C (exam structure, domain weights, naming churn, technical surface). The addendum and PRD rev 2 govern; if `models.py` lags behind (see Option Pool note below), follow the addendum and flag the gap.
- **Existing content for style/ID continuity:** `exercises/<exam>/*.yaml`.

## Schema (fields)

Each exercise is an item under a top-level `exercises:` list.

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Unique, e.g. `dbx-de-0073`. Continue the existing sequence — never reuse an ID. |
| `type` | yes | **`single_choice` only.** The `multi_choice` / "select all that apply" variant is **removed** (PRD rev 2, 2026-06-05). |
| `exam` | yes | `associate` or `professional`. |
| `domain` | yes | Must be EXACTLY one of the enum strings below. |
| `subdomain` | optional | Finer topic tag within the domain, e.g. `"Auto Loader"`. |
| `difficulty` | yes | `easy`, `medium`, or `hard`. |
| `question` | yes | The prompt. |
| `code_context` | optional | A code snippet shown with the question (rendered monospace). Use for "read this snippet, pick the answer" items. |
| `options` | yes | The **Option Pool** — see Option Pool rules below. Option ids `a, b, c, d, e, ...`. |
| `answer` | optional | Derived from the `correct: true` flags; include for readability (e.g. `[a]` or `[a, b]` when the pool has alternatives). |
| `explanation` | yes | Why the correct answer is right AND why each distractor is wrong. **Never reference options by letter (A, B, C, …) — option letters are not shown in the UI, so the user can't tell which option you mean. Refer to options by paraphrasing their content instead.** |
| `references` | recommended | The **official doc URLs you actually reviewed**, prefer `https://docs.databricks.com/...`. |
| `tags` | recommended | Lowercase topic tags, e.g. `[delta, performance]`. |
| `source` | optional | Provenance / anti-braindump flag. Defaults to `original`. |

### Valid `domain` values (Associate exam — copy exactly)
- `Databricks Lakehouse Platform`
- `ELT with Spark SQL and Python`
- `Incremental Data Processing`
- `Production Pipelines`
- `Data Governance`

(Professional domains exist in the addendum §C but are commented out in `models.py`; author Associate unless asked otherwise.)

## Option Pool rules (PRD FR-19 / FR-20 — the core model)

Each MCQ is authored as an **Option Pool**, not a fixed 4-option list:

1. **At least 1 correct** option (`correct: true`) and **at least 3 incorrect** options (`correct: false`). Minimum 4 total.
2. **No upper bound.** Add **extra correct alternatives and/or extra distractors** whenever you can — a deeper pool is the point: the runner shows a different 1-correct + 3-distractor combination on each view, so a question feels new on re-study.
3. **Single-select only.** Multiple `correct: true` options are **interchangeable alternatives** — each is a fully valid answer *on its own*, never a set that must be selected together. The runner displays exactly one correct option + three distractors, in shuffled positions. Never author a question whose correct options only make sense selected jointly (that was the removed multi_choice case).
4. Every option needs `id`, `text`, and a boolean `correct`. `answer`, if present, lists exactly the ids flagged correct.

> **Option Pool / model transition.** The target schema allows a `single_choice` pool with *more than one* `correct: true` (interchangeable alternatives). The current `models.py` validator may still enforce "single_choice ⇒ exactly one correct" until the **Option Pool epic** lands. Until that validator is updated: author exactly **one** correct + **≥3** distractors (always valid today), OR, if intentionally authoring multi-correct alternative pools ahead of the model, flag that the validation step is expected to fail pending the Option Pool epic. Default to one-correct pools unless the user asks for alternative pools.

## Documentation-first workflow (REQUIRED)

Do **not** write questions from memory. For each topic/question:

1. **Review the current official docs.** Use WebSearch / WebFetch against `docs.databricks.com` (and the official Databricks certification exam guide) before drafting. Confirm the feature, syntax, defaults, and current product names. Use the addendum §C "technical surface" as a topic checklist (Delta Lake, Spark SQL, PySpark, Auto Loader, Structured Streaming, Lakeflow Declarative Pipelines, Unity Catalog, Lakeflow Jobs, platform basics).
2. **Use up-to-date terminology + handle naming churn (addendum §C).** Databricks renames things mid-rename across docs and the exam corpus:
   - **Delta Live Tables (DLT) → Lakeflow Declarative Pipelines.** Use the current name. In pipeline code the current alias is **`dp`** (`from pyspark import pipelines as dp`, `@dp.table`, `@dp.expect`), **not** legacy `dlt` (`import dlt`, `@dlt.table`).
   - **Workflows → Lakeflow Jobs.** Use the current name.
   - **Accept both old and new names as aliases.** Since docs/exam are mid-rename, a correct answer using the current name is right; use the *legacy* name as a labeled distractor or a "formerly known as" note, not as the correct answer. Don't mark a question wrong solely for using a recognized legacy alias.
   - Prefer **Unity Catalog** governance patterns where the docs recommend them.
   - Verify CLI/SDK/SQL syntax, flags, and defaults against the docs rather than recall.
3. **Cite what you reviewed.** Put the specific doc URL(s) you actually read into `references`. If you can't verify a fact in the docs, don't turn it into a question. Keep `source: original` — content is original and blueprint-aligned, never reverse-engineered from real exam questions.

## Template

```yaml
  - id: dbx-de-0073
    type: single_choice
    exam: associate
    domain: "Incremental Data Processing"
    subdomain: "Auto Loader"
    difficulty: medium
    question: "<the question text>"
    code_context: |                 # optional
      spark.readStream.format("cloudFiles")...
    options:                        # Option Pool: >=1 correct, >=3 incorrect, deepen when you can
      - id: a
        text: "<correct answer>"
        correct: true
      - id: b
        text: "<plausible distractor>"
        correct: false
      - id: c
        text: "<plausible distractor>"
        correct: false
      - id: d
        text: "<plausible distractor>"
        correct: false
      - id: e                       # optional extra distractor — deepens the pool for freshness
        text: "<another plausible distractor>"
        correct: false
    answer: [a]
    explanation: "<why the correct option is right and why each distractor is wrong — refer to options by their content, never by letter>"
    references:
      - "https://docs.databricks.com/en/..."
    tags: [auto-loader, ingestion]
    source: original
```

Option Pool with interchangeable **correct alternatives** (single-select; runner shows ONE correct + 3 distractors). Use only when the model supports multi-correct `single_choice` pools — see the transition note above:

```yaml
    options:
      - id: a
        text: "cloudFiles.schemaLocation"
        correct: true
      - id: b
        text: "Set cloudFiles.schemaLocation to a writable path"   # interchangeable alternative
        correct: true
      - id: c
        text: "cloudFiles.format"
        correct: false
      - id: d
        text: "checkpointLocation"
        correct: false
      - id: e
        text: "mergeSchema"
        correct: false
    answer: [a, b]
```

## Workflow

1. **Clarify scope if missing.** Ask (only if unspecified): how many questions, which domain(s), difficulty mix, exam level, append vs new file, and whether to author deep pools with alternatives or one-correct pools. Default if they just say "write some": 5 questions, associate, spread across domains, mixed difficulty, one-correct pools with ≥3 distractors (add extra distractors where natural).
2. **Find the target file.** Look in `exercises/<exam>/`. To continue a batch, read the existing file and find the highest `id` so new ones continue the sequence and don't collide. New file naming: `mcq-<exam>-batch-NN.yaml`, with a top-level `exercises:` key.
3. **Research each topic in the official docs** per the documentation-first workflow.
4. **Write the questions** following the template and Option Pool rules: `single_choice`, ≥1 correct and ≥3 incorrect, plausible distractors (common misconceptions or legacy/superseded approaches), explanations that address every option, references to the docs you reviewed.
5. **Validate before finishing.** Confirm the YAML loads and passes the models. Prefer the project's loader/tests; otherwise:
   ```bash
   cd backend && python -c "import yaml; from app.models import MCQ; \
   data = yaml.safe_load(open('../exercises/associate/<file>.yaml')); \
   [MCQ(**e) for e in data['exercises'] if e['type'] == 'single_choice']; \
   print('OK', len(data['exercises']))"
   ```
   Also check: no duplicate `id`s; every question has ≥1 correct and ≥3 incorrect; `type` is `single_choice`; no jointly-required correct sets. Fix any errors before reporting done.
6. **Report** how many questions were added, to which file, the domain/difficulty breakdown, pool depths, and the docs consulted.

## Quality bar
- Grounded in current official documentation — no questions from memory, no deprecated patterns presented as correct.
- Current terminology with alias handling (Lakeflow Declarative Pipelines + `dp`; Lakeflow Jobs; Unity Catalog) per addendum §C.
- `single_choice` only; Option Pool of ≥1 correct + ≥3 incorrect; deepen pools with extra distractors/alternatives for re-study freshness.
- Correct alternatives are interchangeable, never jointly required.
- Distractors are wrong but believable (common misconceptions or legacy/superseded approaches).
- Explanations address every option, not just the correct one.
- Explanations **never reference options by letter** (A, B, C, …). Option letters are not displayed in the UI and are randomized per view, so a letter reference is meaningless to the user. Identify options by paraphrasing their content (e.g. "the option that sets `mergeSchema`") instead.
- Don't duplicate questions already in the target file — skim existing `question` text first.
