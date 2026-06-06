# Addendum — Databricks DE Cert Study Companion

Companion to `prd.md`. Holds the technical how, the decisions considered, and the Discovery research that informs downstream work (architecture, design, content authoring) but does not belong in the capability-focused PRD.

> **Caveat on research below:** Both Discovery research passes ran in an environment where live web access (WebSearch/WebFetch/curl) was blocked. The digests are grounded in model knowledge with a January 2026 cutoff. **Before authoring MCQs at volume, verify the Associate domain list and weights against the live official Databricks PDF exam guide** (see PRD OQ-1). Other facts (question counts, passing score, price, DLT/Workflows naming) are provisional and nice-to-know but not blocking — MCQs will be authored to the current official Databricks documentation as the source of truth, not reverse-engineered from real exam questions.

---

## A. Technology choices (deferred to architecture)

The user explicitly deferred stack decisions to the architecture phase. Constraints/preferences to carry forward:

- **Frontend:** React **or** HTMX — to be investigated during architecture. Trade-off framing: the Code-Completion ("Wordle") feature needs responsive, per-keystroke, client-side Positional Feedback (< 100ms). React (or any rich client framework) makes this straightforward; HTMX is oriented around server round-trips and would need care (or some client-side JS) to hit the latency target for that feature. The MCQ core is well within HTMX's comfort zone. This tension is the key input to the frontend decision.
- **Backend:** Rust **or** Python (with `uv`) — to be investigated. Given the single-user, local scope and that the heaviest logic is parsing exercise files plus simple session state, either is viable: Python+uv likely lowers friction for content tooling and a future generation feature, while Rust offers a leaner single-binary local app.
- **Deployment:** local single-user (no auth/hosting in v1). Sharing/hosting is a non-committed future path the file-based content format is meant to keep open.
- **Content storage:** file-based, version-controlled (git). `[Open: YAML-author / JSON-serve vs. YAML-only — OQ-2.]`

---

## B. Proposed Exercise file schema (input to OQ-2 / FR-1)

Authoring in **YAML** (multiline code, comments, readable); the app may serve/store **JSON**. Two record types share a set of common fields.

**MCQ — Option Pool model (updated 2026-06-05, PRD rev 2):**
Each MCQ is authored as an **Option Pool**: **≥1 correct and ≥3 incorrect** Options, no upper bound — extra correct *alternatives* and/or distractors are encouraged so the runner can show a different 1-correct + 3-distractor combination on each view (PRD FR-19/FR-20). MCQ practice is **single-select only**; the `multi_choice` "select all that apply" variant is removed (PRD decision 2026-06-05). Multiple `correct: true` Options in a pool are **interchangeable alternatives** (any one is valid alone), never a jointly-required set.

```yaml
- id: dbx-de-0142
  type: single_choice            # single_choice only (multi_choice removed)
  exam: associate                # associate | professional
  domain: "Incremental Data Processing"
  subdomain: "Auto Loader"
  difficulty: medium             # easy | medium | hard
  question: |
    Which option configures Auto Loader to infer and evolve schema?
  code_context: |                # optional snippet shown with the question
    spark.readStream.format("cloudFiles")...
  options:                       # Option Pool: >=1 correct, >=3 incorrect, no upper bound
    - id: a
      text: "cloudFiles.schemaLocation"
      correct: true
    - id: b                      # extra correct ALTERNATIVE (interchangeable, not jointly required)
      text: "Set cloudFiles.schemaLocation to a writable path"
      correct: true
    - id: c
      text: "cloudFiles.format"
      correct: false
    - id: d
      text: "checkpointLocation"
      correct: false
    - id: e                      # extra distractor — deepens the pool for freshness
      text: "mergeSchema"
      correct: false
  answer: [a, b]                 # derived from correct:true flags; the runner shows ONE correct + 3 distractors
  explanation: |
    schemaLocation stores the inferred schema and enables evolution.
    Why not c/d/e: ...           # per-distractor rationale
  references:
    - "https://docs.databricks.com/.../auto-loader"
  tags: [streaming, ingestion]
  source: original               # provenance / anti-braindump flag
```

**Code-Completion:**
```yaml
- id: dbx-code-0007
  type: code_completion
  exam: associate
  domain: "ELT with Spark SQL and Python"
  language: pyspark              # pyspark | sql
  difficulty: easy
  prompt: "Read a Delta table named events into a DataFrame."
  template: 'df = spark.read.format("___").table("events")'   # ___ = blank slot
  answer: "delta"
  accepted: ["delta"]           # valid alternative phrasings (FR-16)
  case_sensitive: false
  feedback_granularity: token   # token only in v1 (per-char rejected — see §D)
  ignore_whitespace: true
  hint: "Default Lakehouse table format."
  explanation: |
    Delta is the default table format on Databricks...
```

Shared fields (`id`, `domain`, `difficulty`, `explanation`, `exam`, `source`, `tags`) let session logic and future analytics/SRS treat both types uniformly. Reference standards considered: OpenTDB (minimal JSON shape), Aiken/GIFT (lightweight MCQ text), QTI (rejected — too heavyweight), and Anki (SRS metadata pattern for later).

---

## C. Discovery research — exam structure & technical surface (provisional, verify OQ-1)

**Two role-based certs.** Identified by name + version date (no AWS-style codes). Online proctored (Kryterion/Webassessor). Both ~$200/attempt, valid 2 years; retake the current exam to renew. **No hands-on/coding-execution items** — code appears *inside* questions (read snippet, pick answer), which is exactly the surface the app mimics.

- **Associate** — ~45 scored MCQ, 90 min. SQL-leaning. Predominantly single-best-answer with a minority "select all that apply." *(The app deliberately simplifies to single-select only — PRD rev 2; real-exam "select all" items are reworked into single-correct questions or pooled alternatives.)* Domain weights (most recent published guide):
  1. Databricks Lakehouse Platform ~24%
  2. ELT with Spark SQL and Python ~29%
  3. Incremental Data Processing ~22%
  4. Production Pipelines ~16%
  5. Data Governance ~9%
- **Professional** — **59 scored MCQ, 120 min, $200, 2yr validity.** Heavier PySpark/streaming/ops, scenario-based; assumes Python proficiency + ~2yr Databricks experience. **Domain weights (2026 blueprint — VERIFIED 2026-06-06 against databricks.com/learn/certification/data-engineer-professional and corroborating study guides; supersedes the prior model-knowledge 6-domain list):**
  1. Developing Code for Data Processing (Python & SQL) — **22%**
  2. Cost & Performance Optimization — **13%**
  3. Data Transformation, Cleansing, and Quality — **10%**
  4. Monitoring and Alerting — **10%**
  5. Ensuring Data Security and Compliance — **10%**
  6. Debugging and Deploying — **10%**
  7. Data Ingestion & Acquisition — **7%**
  8. Data Governance — **7%** (shared with Associate)
  9. Data Modelling — **6%**
  10. Data Sharing and Federation — **5%**

  Professional technical surface emphasized (per official page + study guides): Databricks Asset Bundles + CLI + REST API (CI/CD, IaC deploy), Git-based workflows, Lakeflow Spark Declarative Pipelines vs Structured Streaming, Auto Loader, Pandas/Python UDFs, **liquid clustering vs partitioning/Z-Order, deletion vectors, Change Data Feed**, system tables + Spark UI + Query Profiler (observability/cost), row filters & column masks, ACLs, PII masking/tokenization, Delta Sharing + Lakehouse Federation, Unity Catalog permission inheritance, serverless compute. `[NOTE: Reddit was not directly accessible to the research crawler; topic-focus signal came from aggregated exam-taker study guides/write-ups (Medium, passitexams, certifhub, certificationpractice, ExamTopics topic lists), not raw Reddit threads.]`

> Passing score: pass/fail scaled score; ~70% is a commonly-reported *planning heuristic*, not an officially fixed per-domain cut. **Verify.**

**Official study sources Databricks points to:** the per-exam **PDF Exam Guide** (authoritative for scope/weights); **Databricks Academy** courses ("Data Engineering with Databricks" for Associate; "Advanced Data Engineering with Databricks" for Professional); `docs.databricks.com`; published sample/practice questions; Apache Spark docs.

**Naming churn to handle in content:** Delta Live Tables → **Lakeflow Declarative Pipelines**; Workflows → **Lakeflow Jobs**. Build a name-alias layer so both old and new names are accepted in questions/snippets, since the exam corpus and docs are mid-rename.

**Technical surface for content & Code-Completion exercises** (SQL-skew = Associate, PySpark/streaming/ops = Professional):
- **Delta Lake:** `CREATE TABLE ... USING DELTA`, CTAS, managed vs external `LOCATION`; `MERGE INTO ... WHEN MATCHED/NOT MATCHED`, `UPDATE`, `DELETE`, `INSERT OVERWRITE`; time travel (`VERSION AS OF`, `TIMESTAMP AS OF`, `DESCRIBE HISTORY`); `OPTIMIZE`, `ZORDER BY`, `VACUUM`, `RESTORE`, liquid clustering (`CLUSTER BY`); `DESCRIBE DETAIL/EXTENDED`; CHECK constraints; Change Data Feed (`enableChangeDataFeed`, `TABLE_CHANGES`, `readChangeFeed`).
- **Spark SQL:** three-level namespace `catalog.schema.table`, `USE CATALOG/SCHEMA`; views (`TEMP`/`GLOBAL TEMP`, `global_temp.`); `EXPLODE`, `from_json`/`to_json`, `cast`, higher-order funcs (`transform`, `filter`); semi-structured access `col:field`/`col.field`; `COPY INTO`; CTEs, window functions `OVER (PARTITION BY ... ORDER BY ...)`, `PIVOT`; SQL UDFs.
- **PySpark/DataFrame API:** `spark.read.format(...).option(...).load()`, `spark.table()`; writes `.write.format("delta").mode(...).saveAsTable()`, `.partitionBy()`, `mergeSchema`; transforms `select/selectExpr/withColumn/filter/where/groupBy().agg()/join/dropDuplicates/orderBy`; `pyspark.sql.functions` (`col, lit, expr, when, explode, from_json`); `StructType/StructField`, `printSchema`.
- **Auto Loader:** `format("cloudFiles")`, `cloudFiles.format`, `cloudFiles.schemaLocation`, `schemaEvolutionMode`, `inferColumnTypes`, `_rescued_data`, directory-listing vs file-notification; vs `COPY INTO` trade-offs.
- **Structured Streaming:** `readStream`/`writeStream`; triggers (`processingTime`, `availableNow`, deprecated `once`); output modes `append/update/complete`; `checkpointLocation`, exactly-once/idempotency; `withWatermark`, `window()`, stateful ops; `foreachBatch` upserts; medallion architecture.
- **DLT / Lakeflow Declarative Pipelines:** SQL `CREATE OR REFRESH STREAMING TABLE` / `MATERIALIZED VIEW` (and older `CREATE LIVE TABLE` / `STREAMING LIVE TABLE`); `STREAM(LIVE.table)`, `LIVE.table`; Python `@dlt.table`, `@dlt.view`, `dlt.read[_stream]`; expectations `EXPECT ... ON VIOLATION DROP ROW/FAIL UPDATE`, `@dlt.expect[_or_drop/_or_fail]`; `APPLY CHANGES INTO` (CDC/SCD); triggered vs continuous, dev vs prod.
- **Unity Catalog & governance:** three-level namespace; `GRANT/REVOKE` (`SELECT, MODIFY, USE CATALOG/SCHEMA, CREATE`); `CREATE CATALOG/EXTERNAL LOCATION/STORAGE CREDENTIAL`; ownership, `SHOW GRANTS`, dynamic views / row filters / column masks; lineage, Delta Sharing.
- **Jobs / Lakeflow Jobs:** multi-task DAGs, task types (notebook/SQL/DLT/Python), cron scheduling, retries/alerts; job vs all-purpose clusters; `dbutils.widgets`, `dbutils.jobs.taskValues`; repair run, concurrent runs.
- **Platform basics (Associate-heavy):** workspace, clusters, DBFS vs UC volumes, notebook magics (`%sql/%python/%run/%fs`), `dbutils`, Repos/Git folders, SQL warehouses, medallion architecture.

---

## D. Discovery research — comparables & the "Wordle-for-code" design space

**What serious cert candidates value** (consistent across Udemy practice tests, Tutorials Dojo, Whizlabs, MeasureUp, ExamTopics, Anki/Brainscape):
1. **Per-answer explanations with references** — the single most-cited differentiator (why correct *and* why each distractor is wrong). → captured in FR-10.
2. **Blueprint-domain tagging** for drilling weak domains. → FR-4, FR-5.
3. **Two modes: timed mock vs. untimed review.** → review is MVP (FR-8/10); timed is deferred.
4. **Per-domain analytics + readiness indicator.** → deferred phase.
5. **Spaced repetition / missed-question pool.** → deferred phase.
6. **Exam realism** (question style/length, flag-for-review, navigation). → FR-6.
7. **No-braindump credibility** ("original, blueprint-aligned, explained"). → `source` field, §5 Non-Goal.

**"Wordle for code" — prior art & opportunity.** Wordle clones abound (Worldle, Heardle, and **Nerdle** — the closest structural analog, validating a formula with positional feedback). No established, well-known "Wordle for code" product appears to own this space — a genuine opportunity, but a **moderate-confidence** claim to verify manually. Relevant adjacent tools: typing.io / SpeedCoder (code typing — key insight: *skip auto-generated whitespace so learners aren't penalized for indentation*), and DataCamp/Codecademy/SQLBolt (fill-in-the-blank, validated by execution).

**UX pitfalls porting Wordle to code (the substantive design input → drove §4.3 assumptions):**
1. **Whitespace ambiguity** — significant (Python) vs not (SQL); don't color spaces. → ignore non-semantic whitespace.
2. **Token vs character granularity** — meaningful unit is the token, not the char; per-char rewards letter-guessing. → token-level default.
3. **"Yellow / wrong position" barely applies at the char level** — code position is syntactically rigid; a misplaced `)` is just wrong. → **Resolved (2026-06-05): keep green/yellow/grey but at the TOKEN level** (Nerdle-style), where yellow = token present in the answer but in the wrong slot. Per-character feedback rejected.
4. **Multiple valid answers** — `COUNT(*)` vs `count(1)`, `.filter` vs `.where`. → accepted-alternatives set (FR-16); AST/exec equivalence out of scope for MVP of the feature.
5. **Fixed grid breaks on multi-line** — scope to one line / one blank. → single-line/fill-in-blank scope.
6. **Case-sensitivity** — SQL keywords case-insensitive, identifiers/PySpark methods case-sensitive. → explicit per-language case policy.
7. **Hint leakage / triviality** — coloring can reveal the answer in one guess. → limit guesses, possibly hide length / reveal slots not chars.
8. **Cognitive-load mismatch** — keep a teaching/explanation layer so it tests API knowledge, not letter frequency. → FR-17.

**Design recommendation carried into PRD:** token-level (Nerdle-style) feedback, ignore non-semantic whitespace (typing.io), single-line/fill-in-blank scope, validate against canonical + accepted-alternatives. Recommend a design spike before committing FR-13–FR-16 (PRD note + OQ-3).
