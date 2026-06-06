---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.7: Exam Filter & Session Scoping

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-7-exam-filter-session-scoping

## Story Statement

As a **student**,
I want **to choose which exam (Associate or Professional) I'm practicing and have domains scoped to it**,
So that **a session never mixes Associate and Professional questions now that both content sets exist**.

## Acceptance Criteria

**Given** the corpus now contains both Associate (72 exercises) and Professional (60 exercises)
**When** I open the Start screen
**Then** I can select an **exam** (Associate | Professional)
**And** the Domain dropdown lists only that exam's domains

**Given** an exam is selected on the Start screen
**When** the Domain dropdown is populated
**Then** it shows exactly the domains belonging to that exam (Associate: 5 domains; Professional: 10 domains), with **Data Governance** appearing for both because it is shared

**Given** the backend session/count endpoints
**When** I call `GET /api/sessions` or `GET /api/exercises/count` with an `exam` query param
**Then** both endpoints accept `exam` and filter the corpus by exam
**And** `exam=associate` yields only Associate exercises
**And** `exam=professional` yields only Professional exercises

**Given** no exam is selected (request omits `exam`)
**When** a session is built or a count requested
**Then** the behavior is defined and documented — the request defaults to a single exam (**Associate**) rather than silently mixing the two corpora

**Given** the Start-screen match count (Story 6.1)
**When** the selected exam changes
**Then** the displayed match count reflects the selected exam

**Given** the implementation
**When** backend exam filtering runs
**Then** it reuses the existing `filter_exercises` exam support (no new filtering path)
**And** the frontend `DOMAINS` constant is reorganized per-exam

**Given** the test suite
**When** tests run
**Then** they cover exam filtering on `GET /api/sessions` and `GET /api/exercises/count`, and the per-exam domain UI behavior

## Architecture Context

- **Response wrapper:** All endpoints return `{success, data, error}`. [Source: architecture.md#api-design]
- **`GET /api/sessions`:** Builds a randomized Practice Session — filtered, order-randomized, each MCQ carrying 4 sampled + shuffled, flag-less Displayed Options. Primary runner entry point. This story adds `exam` to its existing `domain`/`difficulty`/`type` filter set. [Source: architecture.md "GET /api/sessions → build a Practice Session (filters: domain, difficulty, type)"]
- **`GET /api/exercises/count`:** Lightweight match count `{count}` for the Start-screen "{n} questions match" preview; returns no pools/options/flags (leak-free). Introduced by Story 6.1; this story adds `exam` to its filters. [Source: architecture.md "GET /api/exercises/count → lightweight match count"; epics.md Story 6.1]
- **Non-leakage:** The count endpoint must continue to return only `{count}` (no `correct` flags); the session endpoint must continue to strip `correct` flags from Displayed Options. Adding `exam` must not change either guarantee. [Source: architecture.md#answer-non-leakage]
- **Exam field:** Each exercise carries an `exam` field (`associate | professional`). `ExamType` enum already exists in `models.py`. [Source: prds/.../addendum.md §B example YAML; backend/app/models.py `ExamType`]
- **Domain blueprint:** Associate has 5 domains; Professional has 10 (2026 blueprint, verified 2026-06-06). **Data Governance is shared by both exams.** [Source: prds/.../addendum.md §C; backend/app/models.py `Domain`]

## Tasks / Subtasks

- [x] Task 6.7.1: Add `exam` param to `GET /api/sessions` (backend)
  - [x] Add `exam: str = Query(None, ...)` to `get_session` in `backend/app/main.py`
  - [x] Validate `exam` against `ExamType` case-insensitively, matching the existing domain/difficulty validation loop (add `("exam type", exam, ExamType, "values")` to the validation tuples)
  - [x] Apply the default-exam policy: when `exam` is omitted, default to `associate` before filtering (never pass `exam=None` through to `filter_exercises`, which would mix corpora)
  - [x] Pass `exam=...` into the existing `filter_exercises(...)` call (reuse, do not add a new filtering path)
  - [x] Preserve all existing behavior: randomized order, 4 flag-less Displayed Options, empty result = successful empty session

- [x] Task 6.7.2: Add `exam` param to `GET /api/exercises/count` (backend, depends on Story 6.1)
  - [x] Add `exam: str = Query(None, ...)` to the count handler in `backend/app/main.py`
  - [x] Validate `exam` against `ExamType` case-insensitively (same loop pattern)
  - [x] Apply the same default-exam policy (default `associate` when omitted)
  - [x] Pass `exam=...` into the existing `filter_exercises(...)` call and return `{count: len(filtered)}` — still no pools/options/flags

- [x] Task 6.7.3: Reorganize `DOMAINS` per-exam (frontend)
  - [x] In `frontend/src/constants.js`, replace the flat Associate-only `DOMAINS` array with a per-exam structure, e.g. `DOMAINS_BY_EXAM = { associate: [...5...], professional: [...10...] }`
  - [x] Add an `EXAMS` constant (`['associate', 'professional']` or `{ASSOCIATE, PROFESSIONAL}`)
  - [x] Domain strings MUST match the backend `Domain` enum values exactly (copy from `models.py`); include `Data Governance` in BOTH exam lists (shared)
  - [x] If `DOMAINS` is still imported elsewhere, keep a back-compat export or update importers (only `SessionSelect.jsx` currently imports it)

- [x] Task 6.7.4: Add exam selector to the Start screen (frontend)
  - [x] In `frontend/src/pages/SessionSelect.jsx`, add an `exam` select (Associate | Professional), defaulting to `associate`
  - [x] Derive the Domain dropdown options from `DOMAINS_BY_EXAM[exam]`; reset/clear the selected `domain` when `exam` changes (a stale Professional domain must not persist into an Associate selection)
  - [x] Pass `exam` into `getSession({ exam, domain, difficulty })`
  - [x] Pass `exam` into the match-count call (Story 6.1) so the count reflects the selected exam

- [x] Task 6.7.5: Thread `exam` through the API client (frontend)
  - [x] In `frontend/src/api.js`, add `exam` to `getSession({ exam, domain, difficulty })` and append it to the query string when present
  - [x] Add `exam` to the count fetch helper (Story 6.1's `getExerciseCount`/equivalent) and append to its query string

- [x] Task 6.7.6: Tests
  - [x] Backend (`backend/tests/`): `GET /api/sessions?exam=associate` returns only Associate; `?exam=professional` returns only Professional; omitting `exam` returns the documented default (Associate only — never mixed); invalid `exam` returns `success: false`. Use `uv run pytest`.
  - [x] Backend: same coverage for `GET /api/exercises/count` (per-exam counts, default, invalid). Assert `data` is still only `{count}` (no pools/flags leaked).
  - [x] Frontend (vitest): selecting an exam renders only that exam's domains in the Domain dropdown (Associate = 5 incl. Data Governance; Professional = 10 incl. Data Governance); changing exam resets the domain selection. Use `npx vitest run` / `npm test`.

## Dev Notes

**NEW files:** none expected (all changes are edits). New tests may be added under `backend/tests/` and the frontend test folder.

**UPDATE files:**
- `backend/app/main.py` — add `exam` param + validation + default policy to `get_session` and to the Story 6.1 count handler; reuse `filter_exercises`.
- `frontend/src/constants.js` — reorganize `DOMAINS` into a per-exam structure; add `EXAMS`.
- `frontend/src/pages/SessionSelect.jsx` — add exam selector; scope Domain dropdown; reset domain on exam change; pass `exam` to session + count calls.
- `frontend/src/api.js` — add `exam` to `getSession` (and the Story 6.1 count helper) query strings.

**Current behavior to preserve:**
- `filter_exercises(exercises, domain=None, difficulty=None, exam=None, exercise_type=None)` in `backend/app/content.py` **already supports `exam`** — it normalizes the value (`.strip().lower()`) and compares against `e.exam.value.lower()`. **Do not modify `filter_exercises`;** just start passing `exam` to it. When `exam` is `None`/falsy it is a no-op (all exams), which is exactly the silent-mixing case this story prevents at the endpoint layer.
- `get_session` currently filters only by `domain`/`difficulty` and validates them case-insensitively via a `(label, value, enum_cls, valid_noun)` loop; add `exam` to that loop. It returns randomized, flag-less Displayed Options via `build_session` — that path is untouched.
- `GET /api/exercises/count` is introduced by Story 6.1 (the dependency). If 6.1's handler is not yet present when implementing, coordinate ordering; this story assumes the count handler exists and only adds the `exam` param to it.
- `GET /api/exercises` already exposes an `exam` filter and validates it against `ExamType` — mirror that exact validation pattern for the two endpoints in this story.

**Shared domain — Data Governance:** `Domain.DATA_GOVERNANCE = "Data Governance"` is the 5th Associate domain AND a Professional domain (Professional weight ~7%, 2026 blueprint). It must appear in BOTH exam lists in the frontend `DOMAINS_BY_EXAM`. The exam values are: Associate = Databricks Lakehouse Platform, ELT with Spark SQL and Python, Incremental Data Processing, Production Pipelines, Data Governance. Professional = Developing Code for Data Processing, Data Ingestion & Acquisition, Data Transformation/Cleansing/Quality, Data Sharing and Federation, Monitoring and Alerting, Cost & Performance Optimization, Ensuring Data Security and Compliance, Debugging and Deploying, Data Modelling, Data Governance. (Copy exact strings from `backend/app/models.py` `Domain`.)

**No-exam-selected default policy:** The endpoints accept `exam` as optional for HTTP compatibility, but **the API must never return a mixed-exam result**. When `exam` is omitted, the handler substitutes the default `associate` before calling `filter_exercises`. The frontend always sends an `exam` (selector defaults to Associate), so the default only governs raw/no-UI callers. Document this default in the endpoint docstrings.

**Counts:** Associate corpus = 72 exercises; Professional corpus = 60 exercises (across 10 domains). Tests can assert per-exam totals but should be tolerant if content volume grows — prefer asserting "all returned exercises have `exam == X`" plus a representative count over hard-coding 72/60 if the corpus is expected to expand.

**Tooling:** Backend uses **uv** — run with `uv run pytest`, `uv run ...`. **Never use pip.** Frontend tests use **vitest** (`npx vitest run` / `npm test`).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#story-67-exam-filter--session-scoping]
- [Source: _bmad-output/planning-artifacts/epics.md#story-61-match-count-endpoint--start-screen-preview] (dependency: `GET /api/exercises/count`)
- [Source: _bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md §B] (exam field in YAML schema)
- [Source: _bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md §C] (Associate 5 domains / Professional 10 domains 2026 blueprint; Data Governance shared)
- [Source: _bmad-output/planning-artifacts/architecture.md] (`GET /api/sessions`, `GET /api/exercises/count`, `{success,data,error}` wrapper, answer non-leakage)
- [Source: backend/app/content.py `filter_exercises`] (existing `exam` support to reuse)
- [Source: backend/app/main.py `get_session`, `get_exercises`] (validation-loop pattern to mirror)
- [Source: backend/app/models.py `Domain`, `ExamType`] (authoritative enum values)
- [Source: frontend/src/pages/SessionSelect.jsx] (current domain/difficulty selects)
- [Source: frontend/src/constants.js] (current Associate-only `DOMAINS`)
- [Source: frontend/src/api.js] (`getSession` query-string assembly)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8[1m] (Opus 4.8, 1M context)

### Completion Notes List

- **Backend `GET /api/sessions` & `GET /api/exercises/count`:** Added an optional
  `exam` query param to both, validated case-insensitively against `ExamType`
  via the existing `(label, value, enum_cls, valid_noun)` validation loop
  (`("exam type", exam, ExamType, "values")`). Applied the default-exam policy
  (`exam = exam or ExamType.ASSOCIATE.value`) *after* validation so a missing
  `exam` never passes `None` to `filter_exercises` (which would mix corpora).
  Reused the existing `filter_exercises(..., exam=...)` support — no new
  filtering path. Non-leakage and randomization paths are untouched.
- **Backend `POST /api/sessions`:** Per the orchestrator scope, added an optional
  `exam` body field (validated like the GET endpoints; invalid → `success:false`).
  When present it scopes the matched id set via `filter_exercises(matched, exam=...)`
  so a replay never mixes exams. Deliberately did NOT apply the associate default
  here: POST replays an explicit, already-scoped id set, so defaulting would
  silently drop a legitimately Professional replay. Documented in the docstring.
- **Default policy (documented):** Endpoints accept `exam` as optional for HTTP
  compatibility but never return a mixed-exam result. GET endpoints default an
  omitted `exam` to `associate`; the frontend selector always sends an explicit
  `exam` (defaults to Associate), so the backend default only governs raw callers.
- **Frontend `constants.js`:** Replaced the flat `DOMAINS` with `DOMAINS_BY_EXAM`
  ({associate:[5], professional:[10]}), added `EXAMS` + `DEFAULT_EXAM`, and kept a
  back-compat `DOMAINS` export (= associate list). Domain strings copied verbatim
  from `models.py` `Domain`; `Data Governance` appears in BOTH lists (shared).
- **Frontend `SessionSelect.jsx`:** Added an Exam selector (Associate | Professional,
  default Associate). Domain dropdown is scoped to `DOMAINS_BY_EXAM[exam]`; changing
  exam resets the selected domain. `exam` is threaded into both the live count call
  (Story 6.1 behavior preserved) and the start (`getSession`) call.
- **Frontend `api.js`:** Added `exam` to `getSession` and `getExerciseCount` params,
  appended to the query string when present.
- **Tests:** New `backend/tests/test_exam_filter.py` (per-exam isolation, disjoint
  corpora, default→associate, invalid→error, leak-free count, POST exam scoping).
  Updated the Story 6.1 `test_count.py::test_no_filter_equals_full_corpus` →
  `test_no_filter_equals_associate_corpus` to reflect the new default-exam policy.
  Updated existing `SessionSelect.test.jsx` calls to include `exam: 'associate'` and
  added a new "exam scoping" describe block (default exam, per-exam domain lists of
  5/10, domain reset on exam change, exam passed to API).
- **Verification:** `uv run pytest` → 200 passed. `npx vitest run` → 84 passed.
  Ruff: only 2 pre-existing E501 warnings on lines I did not author (the
  `exerciseIds` Field description and the unknown-id `logger.warning`).
- **Constraints honored:** Did not commit, did not edit `sprint-status.yaml`, and
  did not modify `MCQPractice.jsx`, `SessionContext.jsx`, `App.jsx`, `Summary.jsx`,
  `session.py`, `content.py`, or `models.py`.

### File List

- `backend/app/main.py` (modified) — `exam` param + validation + default policy on
  `get_session` and `get_exercise_count`; optional `exam` body field + scoping on
  `post_session` / `SessionByIdsRequest`.
- `backend/tests/test_exam_filter.py` (new) — exam filtering/scoping tests for the
  three endpoints.
- `backend/tests/test_count.py` (modified) — replaced the obsolete full-corpus
  assertion with the associate-default assertion (Story 6.7 policy).
- `frontend/src/constants.js` (modified) — `DOMAINS_BY_EXAM`, `EXAMS`, `DEFAULT_EXAM`,
  back-compat `DOMAINS`.
- `frontend/src/api.js` (modified) — `exam` in `getSession` and `getExerciseCount`.
- `frontend/src/pages/SessionSelect.jsx` (modified) — exam selector, exam-scoped
  domain dropdown, domain reset on exam change, `exam` threaded to count + session.
- `frontend/src/pages/SessionSelect.test.jsx` (modified) — updated existing call
  assertions + new exam-scoping test block.

## Change Log

- 2026-06-06 — Implemented Story 6.7 (Exam Filter & Session Scoping): added `exam`
  filtering to `GET /api/sessions`, `GET /api/exercises/count`, and `POST /api/sessions`
  (associate default on GET; explicit scope on POST), reorganized frontend domains
  per-exam, added a Start-screen exam selector, and added/updated backend + frontend
  tests. Backend 200 passed, frontend 84 passed.

## Status

review
