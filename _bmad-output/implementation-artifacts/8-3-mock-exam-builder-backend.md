---
status: ready-for-dev
baseline_commit: 4cce825
---

# Story 8.3: Mock-Exam Builder (Backend)

**Epic:** 8 - Timed Practice / Mock Exam
**Story Key:** 8-3-mock-exam-builder-backend

## Story Statement

As a **student**,
I want **a full-length, domain-weighted exam scoped to one exam level**,
So that **I can rehearse the real test**.

## Acceptance Criteria

(Verbatim from epics.md Story 8.3; expanded into testable Given/When/Then.)

**Given** `GET /api/sessions?mode=mock&exam=...`
**When** a mock exam is built
**Then** it assembles a **domain-weighted, full-length** set scoped to that Exam (Associate ≈ 45Q / 90min, Professional ≈ 59Q / 120min per addendum §C weights), **ignoring** unseen-first (representative, may repeat seen)
[Source: epics.md Story 8.3; architecture.md#mock-exam-session-builder; PRD §4.6 FR-27]

**Given** a mock exam is built for an Exam
**When** the response is returned
**Then** the response **stamps the exam `durationMinutes`** (Associate 90, Professional 120) and otherwise matches the existing session shape — each MCQ carries 4 sampled + shuffled, **flag-less** Displayed Options (no `correct` leakage)
[Source: architecture.md "stamps the exam duration"; architecture.md#answer-non-leakage]

**Given** the `exam` scope on a mock request
**When** the set is assembled
**Then** it **never mixes exams** — it respects the exam filter (only that exam's exercises), reusing `filter_exercises`
[Source: epics.md Story 8.3 "never mixes exams"; FR-7.x exam filter; backend/app/content.py `filter_exercises`]

**Given** the per-Domain weighting
**When** the full-length set is sampled
**Then** the per-Domain counts approximate that exam's published weight split (addendum §C), within rounding, and total the exam's full length
[Source: addendum §C; PRD §4.6 FR-27 "weighted by its Domain split"]

**Given** a mock build for an exam whose corpus is smaller than the target size for a domain
**When** sampling cannot fully satisfy a domain's target (not enough authored questions)
**Then** behavior is defined and deterministic-in-shape: the builder takes all available for that domain and does not error (it may fall short of the ideal count rather than fabricating/duplicating beyond the pool); the response is still a successful session
[Source: derived — corpus is finite (Associate 72, Professional 60 at 6.7); graceful degradation, no crash]

**Given** the test suite
**When** `pytest` runs
**Then** tests cover: sizing per exam, per-Domain weighting per exam, `durationMinutes` stamping, exam-scoping (no exam mixing), and that **unseen-first is NOT applied** in mock mode
[Source: epics.md Story 8.3 AC bullet 4]

## Architecture Context

- **Response wrapper:** All endpoints return `{success, data, error}`. Mock mode keeps this envelope; `durationMinutes` is stamped alongside the session data (e.g. top-level beside `data`, or inside a result object — see Dev Notes). [Source: architecture.md#api-design]
- **`GET /api/sessions` (rev 4):** Builds a Practice Session — filtered (FR-5), **unseen-first ordered** (FR-24), each MCQ carrying 4 sampled + shuffled, flag-less Displayed Options (FR-20). Accepts `exam` (FR-7.x). This story adds an **optional `mode=mock`** → Mock-Exam builder: domain-weighted, full-length, exam-scoped, **ignores unseen-first**, returns the exam `durationMinutes`. Primary runner entry point. [Source: architecture.md line 893; architecture.md "Decision: Mock-Exam session builder (rev 4, FR-27)" line 505]
- **Mock-Exam builder decision (rev 4, FR-27):** A builder variant via `GET /api/sessions?mode=mock&exam=...` that assembles a domain-weighted, full-length set scoped to one Exam (Associate ≈45Q/90min, Professional ≈59Q/120min per §C weights) and stamps the exam duration. It **ignores unseen-first** (a mock must be representative, not unseen-biased) and **may repeat seen** questions. Exam-style scoring reuses the §4.5 per-Domain breakdown at session end (frontend, Story 8.4). [Source: architecture.md lines 505-509; addendum §E line 169]
- **Timer is frontend (FR-26/28):** countdown, auto-submit-at-zero, and per-question elapsed timing live in React. The backend only **stamps the duration**; it runs no server-side clock. [Source: architecture.md line 509; PRD §4.6 FR-26/FR-28]
- **Answer non-leakage:** Displayed Options never include the `correct` flag; correctness is resolved server-side. Mock mode must preserve this — it reuses the same option-sampling path. [Source: architecture.md#answer-non-leakage; backend/app/session.py docstring]
- **Exam taxonomies (CURRENT):** Associate uses the **7 current Associate domains** (May 2026 blueprint, migrated): Databricks Intelligence Platform, Data Ingestion and Loading, Data Transformation and Modeling, Working with Lakeflow Jobs, Implementing CI/CD, Troubleshooting/Monitoring/Optimization, Governance and Security. Professional uses its **10 domains**. The two exams now use independent taxonomies. [Source: backend/app/models.py `Domain` enum lines 42-61]
- **Exam sizes / durations / weights (authoritative source = addendum §C — BOTH exams now VERIFIED, OQ-1 resolved):** Associate **45Q / 90min** (7 domains); Professional **59Q / 120min** (10 domains). Associate section weights (verified 2026-06-07 vs the official May 2026 Associate Exam Guide PDF): Databricks Intelligence Platform **6%**, Data Ingestion and Loading **21%**, Data Transformation and Modeling **22%**, Working with Lakeflow Jobs **16%**, Implementing CI/CD **10%**, Troubleshooting, Monitoring, and Optimization **10%**, Governance and Security **15%** (=100%). [Source: addendum §C; PRD §4.6 FR-27]

## Tasks / Subtasks

- [ ] **Define exam sizing/duration/weight config (single source of truth).**
  - [ ] Add a per-exam config (e.g. in `backend/app/session.py` or `backend/app/models.py`) mapping each `ExamType` → `{total_questions, durationMinutes, domain_weights: {Domain: weight}}`.
  - [ ] Populate Professional from addendum §C (59Q / 120min; the 10 verified domain weights).
  - [ ] Populate Associate (**45Q / 90min**) with the VERIFIED 7-domain weights (§C, OQ-1 resolved): Intelligence Platform 6, Data Ingestion and Loading 21, Data Transformation and Modeling 22, Working with Lakeflow Jobs 16, Implementing CI/CD 10, Troubleshooting/Monitoring/Optimization 10, Governance and Security 15 (percent). Key by the `Domain` enum members. [Source: addendum §C; models.py Domain]
  - [ ] Domain weights for each exam should be keyed by the `Domain` enum members that actually belong to that exam.

- [ ] **Add the domain-weighted full-length sampler.**
  - [ ] Add `build_mock_session(exercises, *, exam)` (or equivalent) to `backend/app/session.py` that: (1) groups the (already exam-scoped) exercises by `Domain`; (2) computes per-domain target counts from the weights × total size (largest-remainder rounding so counts sum to the target); (3) samples per domain (random, may repeat seen — i.e. does NOT consult the attempt store); (4) flattens and **orders randomly**; (5) renders each via the existing `build_session_entry` so Displayed Options stay sampled/shuffled/flag-less.
  - [ ] **Ignore unseen-first:** do NOT call `_order_unseen_first`. Either call `build_session(..., prioritize_unseen=False)` for the final ordering pass, or order randomly inside `build_mock_session`. [Source: session.py `build_session(prioritize_unseen=False)`; architecture.md line 505]
  - [ ] Graceful under-supply: if a domain has fewer authored MCQs than its target, take all available (no error, no fabrication beyond the pool).
  - [ ] Keep it a **pure function** over passed-in exercises (no file/store loads inside), matching the existing session.py contract.

- [ ] **Wire `mode=mock` into `GET /api/sessions` (`backend/app/main.py`).**
  - [ ] Add a `mode` query param (default normal/unset). Validate it case-insensitively; only `mock` activates mock mode.
  - [ ] In mock mode: require/default `exam` (reuse the existing default-exam policy → `associate`), validate `exam` as today, then **reuse `filter_exercises(exercises, exam=...)`** for exam scoping (no new filtering path). [Source: main.py lines 191-215; content.py `filter_exercises`]
  - [ ] Call `build_mock_session(filtered, exam=...)` and return the session in the standard `{success, data, error}` envelope **plus** `durationMinutes` for that exam.
  - [ ] In non-mock mode, behavior is unchanged (still unseen-first `build_session(filtered)`).

- [ ] **Tests (`pytest`, backend uses `uv`).** Add to the backend test suite:
  - [ ] Sizing: Associate mock returns ≈45 entries, Professional ≈59 (subject to corpus availability — assert against `min(target, available)` or a seeded fixture corpus large enough to hit the target).
  - [ ] Weighting: per-Domain counts approximate the configured weight split (within largest-remainder rounding) for each exam.
  - [ ] Duration: response stamps `durationMinutes` = 90 (Associate) / 120 (Professional).
  - [ ] Exam-scope: a mock for one exam contains zero exercises from the other exam (no mixing).
  - [ ] No-unseen-first: with a seeded/mocked attempt store marking some exercises seen, the mock ordering is NOT unseen-biased and the store is not consulted for ordering (e.g. patch `store.attempted_ids` and assert it is not relied upon / mock may include seen ids).
  - [ ] Non-leakage preserved: every entry has exactly 4 `displayedOptions`, none carry a `correct` flag.

## Dev Notes

- **Backend tooling: this backend uses `uv`, never `pip`.** Run/install/test via `uv` (e.g. `uv run pytest`, `uv add ...`). Do not introduce `pip install` steps.
- **Files:**
  - **UPDATE** `backend/app/session.py` — add `build_mock_session` (domain-weighted, exam-scoped, randomly ordered, history-independent). Reuse `build_session_entry` / `build_displayed_options`. Optionally house the per-exam size/duration/weight config here.
  - **UPDATE** `backend/app/main.py` — add `mode` query param to `GET /api/sessions`; on `mode=mock` route to the mock builder and stamp `durationMinutes`. Reuse existing exam validation + default-exam policy + `filter_exercises`.
  - **(Optional) UPDATE** `backend/app/models.py` — if the per-exam config (sizes/durations/weights) is co-located with the enums.
  - **UPDATE** backend tests (same dir/pattern as existing `GET /api/sessions` tests) — add mock-mode coverage.
- **Current behavior to PRESERVE:**
  - `build_session(exercises, *, prioritize_unseen=True)` (session.py): MCQ-only; `prioritize_unseen=True` → unseen-first via `_order_unseen_first` (reads the attempt `store`); `prioritize_unseen=False` → pure random order (no history). Mock mode wants the history-independent path. [session.py lines 142-185]
  - `GET /api/sessions` (main.py): validates `domain`/`difficulty`/`exam` case-insensitively; applies the default-exam policy (`exam = exam or "associate"`) so it never mixes corpora; calls `filter_exercises` then `build_session(filtered)`; returns `{success, data, error}`. [main.py lines 142-220]
  - `filter_exercises(exercises, domain, difficulty, exam, exercise_type)` (content.py): case-insensitive, compares against `.value`. Reuse `exam=` for scoping. [content.py lines 258-311]
  - Non-leakage: Displayed Options are `{id, text}` only — never re-derive or add `correct`.
- **Where sizes/durations/weights come from:** addendum §C (PRD prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md, lines 88-114) is authoritative. Associate ≈45Q/90min; Professional 59Q/120min. Professional's 10 domain weights (§C lines 98-108) are verified and map 1:1 onto the Professional `Domain` members in models.py.
- **✅ WEIGHT CONFIRMATION (RESOLVED 2026-06-07):** Associate per-domain weights are now **verified** against the official Databricks "Data Engineer Associate Exam Guide — May 2026" PDF and written into addendum §C (OQ-1 resolved). Use them directly (no placeholder): Intelligence Platform 6%, Data Ingestion and Loading 21%, Data Transformation and Modeling 22%, Working with Lakeflow Jobs 16%, Implementing CI/CD 10%, Troubleshooting/Monitoring/Optimization 10%, Governance and Security 15%. Professional weights remain verified (§C). Both exams' weight vectors are authoritative.
- **Largest-remainder rounding:** per-domain target = round-with-remainder of `weight × total`, adjusting so the per-domain counts sum exactly to the exam total (avoids off-by-one drift from naive rounding).

## References

- epics.md — Story 8.3 (lines 1004-1019); FR-27 (line 77); Epic 8 FR/AR coverage (line 269).
- architecture.md — Rev 4 summary (line 12); Epic 8 overview (line 45); ordering / unseen-first note (line 464); **Mock-Exam session builder decision** (lines 505-509); `GET /api/sessions` contract (line 893); FR-26–28 traceability (line 932).
- PRD prds/prd-.../prd.md — §4.6 FR-27 Mock-Exam mode (lines 318-324); FR-26/FR-28 (timer/timing are frontend); Acceptance pointer §4.6/FR-27 (line 410).
- addendum prds/prd-.../addendum.md — §C exam structure / sizes / durations / weights (lines 88-114); §E Mock-Exam builder note (line 169); research caveat / OQ-1 verify-Associate-weights (line 5).
- backend/app/session.py — `build_session`, `build_session_entry`, `build_displayed_options`, `_order_unseen_first`.
- backend/app/main.py — `GET /api/sessions` (`get_session`), exam validation, default-exam policy.
- backend/app/content.py — `filter_exercises`.
- backend/app/models.py — `Domain` (7 Associate + 10 Professional), `ExamType`.

## Dev Agent Record

_(empty — to be filled by the implementing dev agent)_
