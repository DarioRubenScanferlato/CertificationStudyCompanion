# Addendum — Cert Study Companion
*(Renamed rev 5, 2026-06-09, from "Databricks DE Cert Study Companion." Databricks DE is the first bundled Certification.)*

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

- **Associate** — **45 scored MCQ, 90 min, $200, 2yr validity.** *(The app deliberately simplifies to single-select only — PRD rev 2.)* **Section weights — VERIFIED 2026-06-07 against the official "Databricks Certified Data Engineer Associate Exam Guide" (May 4 2026 version, exam-guide PDF). This SUPERSEDES the prior model-knowledge 5-domain list (Lakehouse Platform/ELT/Incremental/Production Pipelines/Data Governance), which is RETIRED. These 7 sections match the `Domain` enum in `models.py` verbatim:**
  1. Databricks Intelligence Platform — **6%**
  2. Data Ingestion and Loading — **21%**
  3. Data Transformation and Modeling — **22%**
  4. Working with Lakeflow Jobs — **16%**
  5. Implementing CI/CD — **10%**
  6. Troubleshooting, Monitoring, and Optimization — **10%**
  7. Governance and Security — **15%**

  (sums to 100%.) Passing score not stated in the guide (commonly-reported ~70% planning heuristic). The blueprint reflects the platform's current naming: **Databricks Data Intelligence Platform**, **Lakeflow Connect** (ingestion), **Lakeflow Jobs**, **Lakeflow Spark Declarative Pipelines**, **Unity Catalog**-governed tables, **Declarative Automation Bundles** (formerly Databricks Asset Bundles), **Databricks Git Folders** (formerly Repos), Databricks CLI. **OQ-1 RESOLVED for Associate** (domain list + weights confirmed against the official guide).
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

---

## E. Persistence & Timed-Practice technical notes (input to architecture rev 4 — decided 2026-06-07)

Supports PRD §4.5 (Answer & Stats Tracking) and §4.6 (Timed Practice / Mock Exam). These reverse the prior **no-persistence / stateless-session** stance; single-user/local is retained.

**Persistence store: SQLite (Python stdlib `sqlite3`, no pip dependency).**
- Chosen over a JSON file because the stats + readiness + (eventual, still-deferred) SRS phases want attempt-level history and queries ("weakest domain", "least-recently-seen", future "due"). For ~132 questions perf is irrelevant; the choice is future-fit. JSON was the considered alternative (simpler, matches the file-based stance) — rejected for the analytics horizon.
- Location: a gitignored local DB (e.g. `backend/data/progress.db` or an XDG data dir). Single-user, no migrations framework needed initially; create-if-absent schema on startup.
- Indicative schema: `attempts(id, exercise_id, exam, domain, correct, selected_id, time_taken_ms, answered_at)`; stats are aggregations over it. "Seen" = exists in `attempts` for that `exercise_id`. "Unseen-first" = left-anti-join the filtered set against distinct attempted ids, fall back to order-by `max(answered_at)` ascending.
- **Record hook:** `POST /api/feedback` already grades server-side — write the attempt there (it has exercise, correctness, and can receive `time_taken_ms`).
- **Stateless reversal:** `GET /api/sessions` / `build_session` become history-aware (read the store to partition unseen vs seen). New read endpoints for stats/readiness (e.g. `GET /api/stats`, `GET /api/readiness`).

**Mock-Exam session builder:** a domain-weighted, full-length sampler scoped to one Exam — Associate ≈45Q/90min, Professional ≈59Q/120min (§C weights). Likely a variant of the existing session builder (or a `mode=mock` param) that ignores unseen-first (a mock should be representative, not unseen-biased) and stamps the exam duration.

**Timer:** the countdown + auto-submit are frontend (per-question timing captured client-side and sent with the feedback request as `time_taken_ms`). Backend stores it; no server-side timer needed.

**Readiness:** rolling-window accuracy vs ~70% (planning heuristic, §C) overall + per-domain — a query/computation over `attempts`, surfaced as guidance.

## F. Code-Completion technical notes (input to architecture rev 5 — decided 2026-06-08)

Supports PRD §4.3 (Code-Completion "Wordle" Practice), promoted to active scope as **Epic 4**. The `CodeCompletion` Pydantic model already exists in `backend/app/models.py` — these notes cover the *delivery + feedback* realignment the architecture doc must absorb.

**Feedback is CLIENT-SIDE — and the architecture doc must be corrected.**
- NFR-1 requires < 100ms keystroke/submit→render feedback with "no perceptible server round-trip; client-side computation" (architecture.md lines 49, 92, 142–143) — this is also the *entire* stated rationale for choosing React over HTMX (§A above; architecture lines 142–148).
- **The architecture doc's `POST /api/feedback/code-completion` endpoint (lines 363, 900, 906) is a stale inconsistency and is NOT implemented.** A per-keystroke/per-submit server round-trip directly contradicts NFR-1. **Architecture rev 5 must remove that endpoint** and the "calls POST /api/feedback/code-completion on keystroke" component-boundary line, replacing them with the client-side tokenizer + feedback engine below. The MCQ `POST /api/feedback` is unaffected.

**Client-side modules (regex tokenizer + pure feedback engine — AR-9):**
- `tokenize(code, language) → [{token, type, position}]` — regex-based, language-specific (SQL keywords case-insensitive; PySpark/Python identifiers case-sensitive); non-semantic whitespace not emitted; token types keyword/identifier/operator/literal/punctuation. Pure, synchronous, unit-tested in isolation (Epic 4 story 4.2). Lives at `frontend/src/utils/tokenizer.js`.
- `computeFeedback(attempt, canonical, language, {accepted, caseSensitive, ignoreWhitespace}) → [{token, color, position}]` — token-level green/yellow/grey with **two-pass Wordle duplicate handling** (pass 1 greens by position decrementing a target multiset; pass 2 yellows from remaining counts, else grey); scores against `[canonical, ...accepted]` and returns the best match; exposes a "solved" (all-green) signal. Pure, < 100ms (story 4.3). Lives at `frontend/src/utils/codeFeedback.js`.

**Session-builder delivery (backend) — `build_session` must stop skipping code-completion.**
- Today `build_session`/`build_mock_session` filter to `isinstance(MCQ) and type != CODE_COMPLETION` (session.py), so code-completion never reaches the runner. Rev 5: `build_session` emits a **code-completion session entry** carrying `{exerciseId, type:'code_completion', domain, difficulty, language, prompt, template, answer, accepted, caseSensitive, ignoreWhitespace, explanation, references}`. (`answer`/`accepted` ARE shipped — the client-side feedback trade-off; see PRD §4.3/FR-14. This does not relax MCQ FR-20 non-leakage.) Unseen-first ordering (FR-24) still applies to the combined list.
- **`build_mock_session` stays MCQ-only** by design (the domain-weighted mock blueprint is MCQ). Only `GET /api/sessions` (+ replay) deliver code-completion.
- `GET /api/sessions` route + `getSession` client must not assume the MCQ entry shape (no `displayedOptions` on code-completion entries).
- **Routing:** the frontend `practice` view dispatches by `currentExercise.type` (MCQ → `MCQPractice`, code_completion → `CodeCompletion`).

**Guess loop / attempt budget (FR-15):** bounded attempts via a `CODE_COMPLETION_MAX_ATTEMPTS` constant (Wordle-style default 6). On solve or exhaustion → reveal canonical answer + explanation/references; advance via the existing `useSession().next()` (no new end path; Exit-confirm reused).

**Not recorded:** Code-Completion outcomes are client-side and are **not** written to the (MCQ-scoped) `attempts` store, so they don't feed stats/readiness (§E) or per-question timing (FR-28). Known gap; a future story could add a code-completion attempt record + stats surface.

**Content & authoring (PRD §6.4, story 4.6):** a starter Code-Completion bank (SQL + PySpark, current Databricks terminology — Lakeflow Declarative Pipelines + `dp`, Lakeflow Jobs, Unity Catalog) plus a `write-code-completion` agent skill mirroring `write-mcq`. The `CodeCompletion` schema is in §B above.

---

## G. Multi-Provider / Multi-Certification config (input to architecture rev 6 — decided 2026-06-09)

Supports PRD §4.7 (FR-29/FR-30), **Epic 9**. Goal: a new Certification is **content + config, no code change**, while Databricks DE stays intact. This is a *reframe of existing hardcoded values into configuration*, not a rewrite.

**What is hardcoded today (the migration targets):**
- `backend/app/models.py` — `ExamType` enum (`associate` | `professional`) and a `Domain` enum whose members are Databricks DE's domains.
- `backend/app/session.py` — `MOCK_EXAM_CONFIGS: dict[ExamType, MockExamConfig]` with `total_questions` (45 / 59), `duration_minutes` (90 / 120), and `domain_weights` per exam (the largest-remainder mock builder reads these — FR-27).
- `frontend/src/constants.js` — `EXAMS`, `DEFAULT_EXAM`, `DOMAINS_BY_EXAM` (the per-exam Domain taxonomy the Start screen + Story 6.7 use).

**Target: a per-Certification config artifact.** A file-based, version-controlled, human-authorable registry (YAML, loaded at startup like content). Indicative shape:

```yaml
# certifications.yaml  (or one file per certification under config/certifications/)
providers:
  - id: databricks
    name: "Databricks"
    certifications:
      - id: associate                 # == the existing `exam` value (kept for back-compat — PRD §3)
        name: "Databricks Certified Data Engineer Associate"
        total_questions: 45
        duration_minutes: 90
        pass_bar: 0.70                 # readiness heuristic (PRD FR-25 / §C)
        domains:                       # canonical list + weights (sum to 100)
          - { name: "Databricks Lakehouse Platform", weight: 24 }
          - { name: "ELT with Spark SQL and Python", weight: 29 }
          # … remaining Associate domains …
      - id: professional
        name: "Databricks Certified Data Engineer Professional"
        total_questions: 59
        duration_minutes: 120
        pass_bar: 0.70
        domains: [ … Professional's 10 domains + weights … ]
```

**Refactor sketch (architecture rev 6 / Epic 9 stories):**
- **Backend:** replace the `ExamType`/`Domain` *enums* with config-driven values (a loaded `Certification` registry; `exam`/`domain` validate against the selected Certification's config). `MOCK_EXAM_CONFIGS` is **derived from config** rather than literal. `session.py`'s largest-remainder mock builder and the unseen-first/stats code key on `(certification, domain)` exactly as they key on `(exam, domain)` today — the field name `exam` is retained (PRD §3), so the change is "where do the lists/weights come from," not "rename the field." `filter_exercises` already supports `exam`; FR-30 scoping reuses it.
- **Frontend:** `constants.js` `DOMAINS_BY_EXAM`/`EXAMS` become **data fetched from a config endpoint** (e.g. `GET /api/certifications`) instead of a hand-maintained constant, so adding a Certification needs no frontend edit. The Start-screen exam selector (Story 6.7) generalizes to Provider→Certification (this iteration may keep the existing flat exam dropdown wired to the config; the polished switcher UI is deferred — decision-log #40).
- **Validation (FR-4/FR-29):** an Exercise whose `domain` isn't in its Certification's configured domain list is flagged (extends the current Domain-enum check).
- **Content layout (OQ-7):** decide whether to physically reorganize `exercises/associate|professional/` into a Provider→Certification tree (`exercises/databricks/de-associate/…`) or keep the current tree and map via config. Default: **keep current paths this iteration** to minimize churn; the config maps `exam` values to Certifications regardless of directory.

**Guardrail (SM-C3):** the refactor must not regress Databricks DE — the Associate/Professional experience, mock sizing/timing, and all existing tests stay green. The seed config simply re-expresses today's literals.

---

## H. Containerization & sharing via docker compose (input to architecture rev 6 — decided 2026-06-09)

Supports PRD §4.8 (FR-31), **Epic 10**. Goal: one `docker compose up` runs the whole app for a colleague with **only Docker installed** — no host Node/Python/uv. Each colleague runs their **own** instance (single-user per instance; not hosted multi-user — PRD §5 retained non-goal).

**Stack shape (indicative — confirm in architecture):**
- **`backend/Dockerfile`** — Python 3.10+ base; install deps via `uv` (or `pip install -r requirements.txt`); copy `backend/`; run `uvicorn app.main:app --host 0.0.0.0 --port 8000`. SQLite (`store.py`) is stdlib — no service dependency.
- **`frontend/Dockerfile`** — multi-stage: Node build (`npm ci && npm run build`) → serve `dist/` via a static server (nginx or `vite preview`), proxying `/api/*` to the backend service. (Alternatively a single image where the backend serves the built frontend — decide in architecture; two services is the cleaner default and mirrors today's dev split.)
- **`docker-compose.yml`** — two services (`backend`, `frontend`) on a shared network; `frontend` depends_on `backend`; publish the frontend port to a **documented local URL** (e.g. `http://localhost:3000`). The Vite dev proxy (`/api/*` → `backend:8000`) is replaced by the static server's proxy or compose-network service name.

**Persistence (FR-31 — history survives restart):** mount a named volume (or bind mount) at the backend's `backend/data/` so the gitignored `progress.db` lives **outside** the container layer. `docker compose down` then `up` must preserve attempts. (The store is created-if-absent on startup, so a fresh volume just starts empty.)

**Content (OQ-8):** prefer a **bind mount of `exercises/`** (and the §G config) into the backend so a colleague can add/edit content without rebuilding the image; optionally also bake a snapshot into the image for a zero-config "just run it" path. Decide one default + document it.

**README (FR-31 consequence):** document the one-command flow — clone, `docker compose up`, open the URL — plus how to add content (drop YAML + config, restart the backend service) and where history is stored (the volume). This is what makes the tool self-serve for a colleague.

**Out of scope (decision-log #35, SM-C4):** TLS/reverse-proxy/hosting, accounts/auth, a shared backend DB, multi-user concurrency, image publishing to a registry. This is local distribution, not operating a service.

**Reverses:** the architecture doc's "No containerization for MVP (local development only)" line and its "Future packaging (Phase 2+): Tauri/Electron" note — docker compose is now the committed share path.

---

## I. Question feedback & content-improvement loop (input to architecture rev 8 — decided 2026-06-10)

Supports PRD §4.9 (FR-32/FR-33), **Epic 11**. Goal: capture in-app learner feedback on a question to a **sidecar** file (authored Exercise YAML untouched), then let the `write-mcq` skill revise flagged questions from that feedback and mark them resolved.

**Sidecar store (FR-32):**
- A single YAML file alongside content, e.g. **`exercises/feedback.yaml`**, mapping Exercise `id` → list of entries:
  ```yaml
  dbx-de-0142:
    - note: "Option b and d are basically the same distractor."
      created_at: "2026-06-10T14:30:00Z"
      resolved: false
  ```
- **Authored Exercise files are never rewritten by the app** (the whole point of the sidecar — no risk to comments / Option-Pool layout). Only `feedback.yaml` is written.
- **Backend write path:** a NEW endpoint — name it to avoid colliding with the MCQ-grading `POST /api/feedback`, e.g. **`POST /api/exercise-feedback`** with `{ exerciseId, note }` → append an entry (`created_at` server-stamped, `resolved: false`). Read path (optional) `GET /api/exercise-feedback?exerciseId=` to show existing notes. Standard `{success, data, error}` wrapper. The endpoint validates that `exerciseId` exists in the loaded corpus.
- **New module** `backend/app/feedback_store.py` (distinct from MCQ `feedback.py`): `add_note(exercise_id, note)`, `notes_for(exercise_id)`, `open_notes()`, `mark_resolved(...)`. Reads/writes the YAML with a small lock; create-if-absent.
- This is the app's **first content-write path** — a narrow, deliberate reversal of the "no in-app authoring" stance (PRD §5 narrowed). It does NOT touch the SQLite attempt store (that stays MCQ-scoped, Epic 7) and does NOT modify Exercise files.

**Docker implication (ties OQ-8):** writeback requires the content location to be a **writable bind-mount** (not baked read-only into the image) — reinforces the OQ-8 "mount `exercises/`" option. **OQ-9 resolved (2026-06-11, decision-log #57): `feedback.yaml` is local-per-instance and gitignored** (like `progress.db`) — each instance keeps its own feedback; mount it on the volume / a writable path.

**Frontend (FR-32):** a lightweight "Flag / leave a note" affordance on the practice surface (MCQ feedback panel + the Code-Completion conclusion). Opens a small text box; submit calls `POST /api/exercise-feedback`. Keep it subordinate to the primary study actions (don't compete with Submit/Next). Reuses the shared runner-shell conventions (rev 7).

**Skill revision loop (FR-33):** the existing `write-mcq` skill (`.claude/skills/write-mcq/SKILL.md`) gains a feedback-aware mode: given an Exercise id (or a sweep of `open_notes()`), it reads the sidecar notes, **edits the Exercise in its source YAML** to fix the flagged issue, re-validates (Option Pool / domain rules), and **marks the feedback entries resolved** in `feedback.yaml`. The author reviews the diff (normal version-controlled edit; no approval UI). MCQ-first; a `write-code-completion` parallel is a later extension. The skill only acts on **unresolved** notes.

**Out of scope:** in-app editing of questions/options/explanations/config (still file/skill-authored); a feedback moderation/triage UI; cross-instance feedback aggregation (sharing model is per-instance).
