---
name: write-code-completion
description: Author Databricks DE certification Code-Completion ("Wordle-style") exercises as schema-valid YAML matching the CodeCompletion model in backend/app/models.py and exercises/associate/code-completion-*.yaml. Each is a single fill-in-the-blank (one `___`) with a canonical answer + accepted alternatives, grounded in current official Databricks documentation. Use when the user asks to write, generate, add, or create code-completion / fill-in-the-blank / Wordle-style syntax exercises for the study companion.
---

# Write Code-Completion Exercises

**Goal:** Produce Code-Completion exercises for the Databricks Data Engineer certification study companion as YAML that validates against the `CodeCompletion` Pydantic model, matches the structure of `exercises/associate/code-completion-associate-batch-01.yaml`, and follows the canonical schema and authoring rules in the BMad addendum (§B, §C, §F). Each exercise is a **single fill-in-the-blank** (`template` with exactly one `___`), graded **client-side** with token-level green/yellow/grey feedback, and grounded in **current official Databricks documentation** with **up-to-date terminology**.

This is the Code-Completion sibling of `write-mcq`. Same documentation-first + current-terminology bar; different exercise shape (template/answer/accepted instead of an Option Pool).

## Authoritative sources (read these first)
- **Schema source of truth:** `backend/app/models.py` — the `CodeCompletion` model.
- **Canonical authoring schema + rules:** BMad addendum §B (field set), §C (exam structure, domain weights, naming churn, technical surface), §F (code-completion realignment: client-side token-level green/yellow/grey, single-line/fill-in-blank, `accepted` alternatives, per-language case).
- **Existing content for style/ID continuity:** `exercises/<exam>/code-completion-*.yaml`.

## Schema (fields)

Each exercise is an item under a top-level `exercises:` list.

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Unique, e.g. `dbx-de-0151`. Continue the existing sequence — never reuse an ID (check the highest id across `exercises/`). |
| `type` | yes | **`code_completion`.** |
| `exam` | yes | `associate` or `professional`. |
| `domain` | yes | EXACTLY one of the Associate domain enum strings (below). |
| `subdomain` | optional | Finer topic tag, e.g. `"Auto Loader"`. |
| `difficulty` | yes | `easy`, `medium`, or `hard`. |
| `question` | yes | The prompt — what to do + what the blank is. |
| `language` | yes | `sql`, `pyspark`, or `python`. Drives tokenizer + Prism highlighting. |
| `template` | yes | The code with **exactly one `___`** blank. Single line or a short multi-line snippet with ONE blank. Multi-line allowed but keep the blank's line legible. |
| `answer` | yes | The **single** canonical token/phrase that fills the blank. Non-empty. |
| `accepted` | optional | Extra interchangeable correct phrasings (FR-16), e.g. `where` when the answer is `filter`. **Do NOT repeat the canonical `answer`** — it is always a candidate in scoring, so listing it again is redundant. Omit `accepted` entirely when there's no genuine alternative. Casing is handled by `case_sensitive`, so never list case variants. |
| `case_sensitive` | yes (set deliberately) | `false` for SQL-keyword blanks (SQL is case-insensitive); `true` where identifier/option casing matters (PySpark identifiers, `cloudFiles.*` option keys). Default `false`. |
| `ignore_whitespace` | yes (set deliberately) | `true` by default — the learner isn't penalized for spacing. |
| `explanation` | yes | Teach the syntax: why the answer is right, what the wrong-but-tempting tokens are, current vs legacy naming. |
| `references` | recommended | The **official doc URLs you actually reviewed** (`https://docs.databricks.com/...`). |
| `tags` | recommended | Lowercase topic tags, e.g. `[delta, merge, sql]`. |
| `source` | optional | Provenance / anti-braindump flag. Defaults to `original`. |

### Valid `domain` values (Associate exam, **May 2026 blueprint** — copy exactly)
- `Databricks Intelligence Platform`
- `Data Ingestion and Loading`
- `Data Transformation and Modeling`
- `Working with Lakeflow Jobs`
- `Implementing CI/CD`
- `Troubleshooting, Monitoring, and Optimization`
- `Governance and Security`

(Professional domains are defined in `models.py`; author Associate unless asked otherwise.)

## The fill-in-the-blank model (replaces the MCQ Option Pool)

1. **Exactly one `___` blank per `template`** (the model rejects a template with no `___`). The `answer` is the single token/phrase that fills it.
2. **`answer` non-empty** (model-enforced) and should **tokenize to something** — don't blank pure punctuation; blank a keyword, identifier, option key, or operator so the token-level feedback is meaningful.
3. **`accepted` = interchangeable alternatives** (FR-16): each is fully correct on its own. Use it for genuine synonyms (`filter`/`where`, `availableNow`/`once` only if both truly valid) — NOT for case variants (handled by `case_sensitive`).
4. **Choose the blank for pedagogy.** Token-level feedback shows green (right token, right place) / yellow (right token, wrong place) / grey (not in answer). A single-token blank mostly yields green-or-grey; a short multi-token blank (e.g. `WHEN NOT MATCHED`) lets yellow teach ordering. Prefer blanks where the answer is the *one thing being tested*.
5. **Per-language case + whitespace:** `case_sensitive: false` for SQL keywords; `true` for PySpark identifiers and `cloudFiles.*`/option keys where casing is real. `ignore_whitespace: true` unless whitespace is semantic (it almost never is here).

## Documentation-first workflow (REQUIRED)

Do **not** write from memory. For each topic/blank:

1. **Review the current official docs** (WebSearch / WebFetch against `docs.databricks.com` + the certification exam guide) before drafting. Confirm the exact keyword/option/decorator, syntax, and defaults. Use addendum §C's "technical surface" as a topic checklist (Delta Lake, Spark SQL, PySpark, Auto Loader, Structured Streaming, Lakeflow Declarative Pipelines, Unity Catalog, Lakeflow Jobs).
2. **Use up-to-date terminology + handle naming churn (addendum §C):**
   - **Delta Live Tables (DLT) → Lakeflow Declarative Pipelines.** In pipeline code the current alias is **`dp`** (`from pyspark import pipelines as dp`, `@dp.table`, `@dp.expect`), **not** legacy `dlt` (`import dlt`, `@dlt.table`). The canonical `answer` uses the current form; mention the legacy name only in the explanation as "formerly known as".
   - **Workflows → Lakeflow Jobs.** Use the current name.
   - Prefer **Unity Catalog** governance syntax.
   - Verify CLI/SDK/SQL syntax, flags, and defaults against the docs rather than recall.
3. **Cite what you reviewed** in `references`. If you can't verify the exact token in the docs, don't make it a blank. Keep `source: original`.

> If live web access is unavailable in the run environment, author from current model knowledge using the **stable, well-established** Databricks surface (as the existing batch-01 was), keep the syntax conservative, and note the provenance caveat — never invent flags/options.

## Template

```yaml
  - id: dbx-de-0151
    type: code_completion
    exam: associate
    domain: "Data Transformation and Modeling"
    subdomain: "MERGE / upsert"
    difficulty: medium
    question: "<what to do + what the blank is>"
    language: sql
    template: |
      MERGE INTO target t USING updates s ON t.id = s.id
      WHEN MATCHED THEN ___ SET *
    answer: "UPDATE"
    # no `accepted` — there's no genuine alternative phrasing; the canonical
    # answer is always a candidate, so don't repeat it here.
    case_sensitive: false        # SQL keyword
    ignore_whitespace: true
    explanation: "<teach the syntax; current vs legacy naming; why the answer fits the blank>"
    references:
      - "https://docs.databricks.com/en/sql/language-manual/delta-merge-into.html"
    tags: [delta, merge, sql]
    source: original
```

PySpark example (identifier blank — case-sensitive):

```yaml
  - id: dbx-de-0152
    type: code_completion
    exam: associate
    domain: "Data Transformation and Modeling"
    difficulty: easy
    question: "Keep only rows where age > 21."
    language: pyspark
    template: |
      df.___("age > 21")
    answer: "filter"
    accepted:
      - "where"                  # genuine interchangeable alias (FR-16) — canonical not repeated
    case_sensitive: true         # PySpark identifier
    ignore_whitespace: true
    explanation: "`df.filter(...)` and its alias `df.where(...)` both keep matching rows; identifiers are case-sensitive."
    references:
      - "https://docs.databricks.com/en/pyspark/..."
    tags: [pyspark, dataframe, filter]
    source: original
```

## Workflow

1. **Clarify scope if missing.** Ask (only if unspecified): how many, which domain(s)/topics, language mix (SQL vs PySpark), difficulty mix, exam level, append-to-batch vs new file. Default if they just say "write some": ~8–10, associate, SQL-skewed with some PySpark, mixed difficulty.
2. **Find the target file.** `exercises/<exam>/code-completion-<exam>-batch-NN.yaml` with a top-level `exercises:` key. Read existing batches; continue the highest `id` so new ones don't collide.
3. **Research each topic in the official docs** per the documentation-first workflow.
4. **Write the exercises** following the template: one `___`, a single canonical `answer`, `accepted` alternatives where a genuine alternative exists, deliberate `case_sensitive`/`ignore_whitespace`, a teaching `explanation`, and `references` to the docs reviewed.
5. **Validate before finishing.** Confirm each item loads and constructs as a `CodeCompletion`. Use `uv` (never pip):
   ```bash
   cd backend && uv run python -c "import yaml; from app.models import CodeCompletion; \
   data = yaml.safe_load(open('../exercises/associate/<file>.yaml')); \
   [CodeCompletion(**e) for e in data['exercises']]; print('OK', len(data['exercises']))"
   ```
   Also check: no duplicate `id`s anywhere in `exercises/`; every `template` contains `___`; every `answer` is non-empty and tokenizes to a real token; `domain` is an exact enum string.
6. **Report** how many were added, to which file, the language/difficulty/domain breakdown, and the docs consulted.

## Quality bar
- Grounded in current official documentation — no exercises from memory, no deprecated syntax as the canonical answer.
- Current terminology with alias handling (Lakeflow Declarative Pipelines + `dp`; Lakeflow Jobs; Unity Catalog) per addendum §C.
- Exactly one `___` per template; non-empty `answer` that tokenizes meaningfully.
- `accepted` holds genuine interchangeable phrasings (FR-16), not case variants.
- `case_sensitive`/`ignore_whitespace` set deliberately per language.
- Explanations teach the syntax and call out the current-vs-legacy naming where relevant.
- Don't duplicate an exercise already in the target file — skim existing `question`/`template` first.
- Don't over-invest vs MCQ content (SM-C1/SM-C2): a solid starter bank, not exhaustive.
