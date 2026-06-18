---
status: done
baseline_commit: 247164b
---

# Story 9.1: Per-Certification Config Model & Loader

**Epic:** 9 - Multi-Provider / Multi-Certification
**Story Key:** 9-1-per-certification-config-model-loader

## Story Statement

As a **content author / maintainer**,
I want **each certification's blueprint (Provider, domains, weights, exam parameters) declared in a file-based config with a validating loader**,
So that **adding a certification becomes content + config (no code change) — and the existing hardcoded Databricks values move to a single source of truth without changing any behavior**.

(PRD §4.7 / FR-29; addendum §G; architecture rev 6 / AR-19; decision-log #36/#39.)

## Acceptance Criteria

**Given** the app
**When** it starts
**Then** a new **per-Certification config registry** is loaded from a file-based YAML (`config/certifications.yaml`) and validated against Pydantic models — failing **loudly** (clear error naming the problem) on a malformed/invalid config
**And** the registry declares, per Certification: `id` (the existing `exam` value), `name`, `total_questions`, `duration_minutes`, `pass_bar`, and a `domains` list of `{ name, weight }`, nested under a Provider (`id`, `name`)
**And** a **seed config re-expresses today's hardcoded values EXACTLY**: Databricks `associate` (45Q / 90min / pass_bar 0.70 / the 7 Associate domains + weights) and `professional` (59Q / 120min / pass_bar 0.70 / the 10 Professional domains + weights), each domain-weight set summing to 100
**And** a new loader module exposes the registry + lookup helpers (e.g. `get_certification(exam_id)`, `domain_weights(exam_id)`, `exam_params(exam_id)`) — **consumed by Story 9.2**, which does the actual rewiring
**And** this story is **ADDITIVE ONLY**: it does NOT modify `models.py`'s `ExamType`/`Domain` enums, `MOCK_EXAM_CONFIGS`, or any runtime behavior — every existing test stays green (no Databricks DE regression — SM-C3)
**And** `pytest` covers: the seed loads + validates; malformed/invalid configs (bad weight sum, missing field, unknown duplicate id) fail loudly; and a **parity test** asserting the seed's certifications/domains/weights/params **exactly match** the current `MOCK_EXAM_CONFIGS` + `Domain` enum (the anchor that lets 9.2 switch over provably without behavior change)

## Story Requirements (from epics.md Story 9.1)

Per-Certification config (canonical domain list, domain weights, exam parameters: `total_questions`/`duration_minutes`/`pass_bar`) declared in a file-based YAML loaded at startup; Pydantic model; **seed config re-expressing today's Databricks Associate (45/90) + Professional (59/120) literals + their domain weights**; pytest covers load + validation + the seed matching current values. This is the **unblocker for Epic 9** — Story 9.2 (make domains/mock params config-driven), 9.3 (`GET /api/certifications` + config-driven frontend), 9.4 (cert-scoped validation), 9.5 (rebrand) all build on it.

## Developer Context & Guardrails

### Scope discipline (READ FIRST)
- **9.1 = create the config + model + loader + tests. NOTHING ELSE.** Do **not** touch `ExamType`/`Domain` enums, `MOCK_EXAM_CONFIGS`, `session.py` builders, `content.py` filters, or any endpoint — that rewiring is **Story 9.2**. Keeping 9.1 additive means it cannot regress Databricks DE by construction.
- The `exam` field stays the Certification identifier (decision #36): a Certification's `id` in the config IS the existing `exam` value (`associate` / `professional`). Do not rename it.
- **OQ-6 (config location/shape):** default to a **single file `config/certifications.yaml`** at the project root (architecture rev 6 added `config/certifications.yaml` to the structure). One file, a `providers:` list. (A per-cert-file split is a later option; don't build it.)

### The exact seed values to re-express (source of truth = current code)
From `backend/app/session.py` `MOCK_EXAM_CONFIGS` and `backend/app/models.py` `Domain` enum (both verified against the May-2026 Associate / 2026 Professional blueprints). `pass_bar` = `store.py` `READINESS_THRESHOLD` = **0.70** for both.

```yaml
# config/certifications.yaml
providers:
  - id: databricks
    name: "Databricks"
    certifications:
      - id: associate            # == the existing `exam` value
        name: "Databricks Certified Data Engineer Associate"
        total_questions: 45
        duration_minutes: 90
        pass_bar: 0.70
        domains:                 # weights sum to 100
          - { name: "Databricks Intelligence Platform", weight: 6 }
          - { name: "Data Ingestion and Loading", weight: 21 }
          - { name: "Data Transformation and Modeling", weight: 22 }
          - { name: "Working with Lakeflow Jobs", weight: 16 }
          - { name: "Implementing CI/CD", weight: 10 }
          - { name: "Troubleshooting, Monitoring, and Optimization", weight: 10 }
          - { name: "Governance and Security", weight: 15 }
      - id: professional
        name: "Databricks Certified Data Engineer Professional"
        total_questions: 59
        duration_minutes: 120
        pass_bar: 0.70
        domains:                 # weights sum to 100
          - { name: "Developing Code for Data Processing", weight: 22 }
          - { name: "Data Ingestion & Acquisition", weight: 7 }
          - { name: "Data Transformation, Cleansing, and Quality", weight: 10 }
          - { name: "Data Sharing and Federation", weight: 5 }
          - { name: "Monitoring and Alerting", weight: 10 }
          - { name: "Cost & Performance Optimization", weight: 13 }
          - { name: "Ensuring Data Security and Compliance", weight: 10 }
          - { name: "Debugging and Deploying", weight: 10 }
          - { name: "Data Modelling", weight: 6 }
          - { name: "Data Governance", weight: 7 }
```
**Domain name strings must match the `Domain` enum VALUES byte-for-byte** (e.g. `"Cost & Performance Optimization"` with the ampersand, `"Troubleshooting, Monitoring, and Optimization"` with the Oxford comma) — the parity test enforces this.

### Models (Pydantic, in a new module)
- `CertificationDomain(name: str, weight: int)` — `weight` ≥ 0.
- `Certification(id: str, name: str, total_questions: int>0, duration_minutes: int>0, pass_bar: float in (0,1], domains: list[CertificationDomain])` — validator: `domains` non-empty AND `sum(weights) == 100`; `id` non-empty.
- `Provider(id: str, name: str, certifications: list[Certification])` — `certifications` non-empty.
- `CertificationRegistry(providers: list[Provider])` — validator: certification `id`s are globally unique across providers (no dup `exam` ids).
- Use the project's Pydantic version + validator style already in `backend/app/models.py` (e.g. `@validator`). Reuse the `str, Enum`-free plain models.

### Loader (new module)
- New module `backend/app/certifications.py` (parallels `content.py`).
  - `load_certifications(path: Path | None = None) -> CertificationRegistry` — resolve `config/certifications.yaml` via the SAME project-root walk `content.py` uses (`load_exercises_from_directory` lines ~94-104), parse YAML (`yaml.safe_load`), construct `CertificationRegistry(**data)`. On `yaml.YAMLError` or Pydantic `ValidationError`, raise a clear error naming the file + problem (fail-loud — FR-3 spirit). Single author; a clear stack trace is acceptable, but name the file.
  - Lookup helpers keyed by `exam` id (case-insensitive, mirroring `filter_exercises`): `get_certification(registry, exam_id)`, `domain_weights(registry, exam_id) -> dict[str,int]`, `exam_params(registry, exam_id) -> {total_questions, duration_minutes, pass_bar}`. These are what Story 9.2 will call to replace `MOCK_EXAM_CONFIGS`.
- **Startup wiring:** in `main.py` `lifespan` (lines 29-44), after `init_db()` / `load_exercises_from_directory()`, load the registry into `app.state.certifications` and log a one-line summary. A malformed config should fail loudly at startup (don't swallow). This makes the config live without yet changing any behavior.

### Files
**NEW:**
- `config/certifications.yaml` — the seed registry (the YAML above).
- `backend/app/certifications.py` — models + `load_certifications` + helpers.
- `backend/tests/test_certifications.py` — load/validate/malformed + the parity test.

**UPDATE (minimal, additive):**
- `backend/app/main.py` — `lifespan`: load the registry into `app.state.certifications` (1 import + ~3 lines). Do not touch anything else.

**DO NOT TOUCH:** `backend/app/models.py` (enums), `backend/app/session.py` (`MOCK_EXAM_CONFIGS`, builders), `backend/app/content.py`, any endpoint, any frontend file. (Those are Stories 9.2–9.5.)

### Files being modified — current state (read before editing)
- `backend/app/main.py` `lifespan` (lines 29-44): currently `init_db()` then `load_exercises_from_directory()` → sets `app.state.exercises` / `app.state.error_log`. **Preserve** this exactly; only append the certifications load. The `getattr(app.state, "exercises", [])` guard pattern is used by endpoints — follow the same defensive style if any endpoint later reads `app.state.certifications` (not in this story).
- `backend/app/session.py` `MOCK_EXAM_CONFIGS` (the values above) + `_largest_remainder_targets` — **read but do not change**; the parity test reads `MOCK_EXAM_CONFIGS` to assert the seed matches.
- `backend/app/models.py` `Domain` enum — **read but do not change**; the parity test reads `Domain` members to assert every weighted domain name is an exact enum value and the per-exam domain sets match.

### Testing (pytest, via `uv` — NEVER pip; project-context.md)
- `test_certifications.py`:
  - Seed loads + validates (no error); registry has 1 provider (`databricks`) with 2 certifications.
  - Helpers: `exam_params("associate")` → 45/90/0.70; `domain_weights("professional")` sums to 100; case-insensitive id lookup.
  - **Malformed configs fail loudly** (use temp files): weights not summing to 100; missing required field; duplicate certification id; empty domains; non-existent file or bad YAML → clear error.
  - **Parity test (the anchor):** for each `ExamType`, assert the seed certification's `total_questions`/`duration_minutes` == `MOCK_EXAM_CONFIGS[exam]` and its `{domain_name: weight}` == `{d.value: w for d, w in MOCK_EXAM_CONFIGS[exam].domain_weights.items()}`; assert every seed domain name is a valid `Domain` enum value; assert `pass_bar == READINESS_THRESHOLD`.
- Mirror `test_content_validation.py` / `test_feedback_store.py` style (temp-file fixtures for the malformed cases). Use `load_certifications(path=tmp_path/...)`.
- **Run the FULL backend suite** — it must stay green (additive story; nothing existing changes).

## Architecture Compliance
- AR-19 (architecture rev 6): per-Certification config loader; the `exam` field retained as the Certification id; frontend will fetch via a future `GET /api/certifications` (Story 9.3 — not here). Config is file-based YAML loaded at startup, mirroring content loading.
- Fail-loud validation matches the content-loader stance. No DB; the registry lives in `app.state` in memory.
- **Docker (rev 6 / OQ-8):** `config/` must be readable by the backend container (bind-mount alongside `exercises/`) — a deployment concern for Epic 10, just keep the config at a mountable path.

## References
- [PRD §4.7 FR-29] per-Certification configuration; [addendum §G] the config schema + refactor sketch (this story is its first half — model + loader; 9.2 is the rewiring).
- [architecture.md rev 6 frontmatter] AR-19; `config/certifications.yaml` in the structure.
- [decision-log #36] `exam`→Certification semantics retained; [#39] full flow; [#40] deferred switcher UI.
- [backend/app/session.py] `MOCK_EXAM_CONFIGS` (seed source); [backend/app/models.py] `Domain` enum (domain name source); [backend/app/store.py] `READINESS_THRESHOLD` (pass_bar); [backend/app/content.py] `load_exercises_from_directory` (loader/path-walk pattern to mirror); [backend/app/main.py] `lifespan` (startup hook).
- [project-context.md] uv only, never pip.

## Dev Agent Record

### Agent Model Used
claude-opus-4-8[1m] (Claude Code, dev-story workflow).

### Completion Notes List
Implemented additive-only, per the scope discipline — no enum/`MOCK_EXAM_CONFIGS`/endpoint changes.

- **Config (`config/certifications.yaml`):** seed registry at project root, re-expressing today's hardcoded values exactly (Databricks `associate` 45/90/0.70 + 7 domains; `professional` 59/120/0.70 + 10 domains; each weight set sums to 100). Domain name strings copied byte-for-byte from the `Domain` enum values.
- **Models + loader (`backend/app/certifications.py`):** Pydantic **v1** (`validator`/`root_validator`, matching `models.py`) models `CertificationDomain` / `Certification` / `Provider` / `CertificationRegistry`. Validators: weight ≥ 0; `total_questions`/`duration_minutes` > 0; `pass_bar` in (0,1]; non-empty `id`; non-empty `domains` summing to exactly 100; non-empty `certifications`/`providers`; globally-unique certification ids (case-insensitive) across providers. `load_certifications(path=None)` resolves `config/certifications.yaml` via the SAME project-root walk `content.py` uses, parses with `yaml.safe_load`, and **fails loudly** — a new `CertificationConfigError` naming the file is raised on missing file / bad YAML / non-mapping / validation failure. Helpers `get_certification` / `domain_weights` / `exam_params` are keyed by `exam` id, case-insensitive (mirroring `filter_exercises`). These are what Story 9.2 will call.
- **Startup wiring (`backend/app/main.py`):** `lifespan` now loads the registry into `app.state.certifications` after the existing exercise load and logs a one-line summary. A malformed config fails loudly at startup (not swallowed). No other behavior touched — exercise loading preserved exactly.
- **Tests (`backend/tests/test_certifications.py`, 13 tests, all pass):** seed loads + validates (1 provider, 2 certs); helpers (`exam_params("associate")`→45/90/0.70, `domain_weights("professional")` sums to 100, case-insensitive lookup, unknown id raises); malformed configs fail loudly (bad weight sum, missing field, duplicate/case-variant id, empty domains, missing file, bad YAML, non-mapping); and the **parity anchor** — for each `ExamType`, asserts seed `total_questions`/`duration_minutes` == `MOCK_EXAM_CONFIGS[exam]`, `{domain: weight}` map matches exactly, every seed domain name is a valid `Domain` enum value, and `pass_bar == READINESS_THRESHOLD`.

**Validation:** `uv run pytest tests/test_certifications.py` → 13 passed. `uv run ruff check` on all changed/new files → clean. Full suite → 312 passed, **2 failed** — both pre-existing failures in **uncommitted Story 7.6 WIP** (`app/session.py` is working-tree-modified, adding the `seen` flag; 7-6 is in `review`): `test_code_completion_session.py::...::test_code_completion_seen_is_always_false` (fails in isolation, exercises the 7.6 `seen` flag) and `test_sessions_post.py::...::test_post_entry_shape_matches_get` (passes in isolation; full-suite ordering only). Neither references certifications; both are independent of this additive story. No Databricks DE regression introduced by 9.1 (SM-C3 satisfied).

### File List
**NEW:**
- `config/certifications.yaml`
- `backend/app/certifications.py`
- `backend/tests/test_certifications.py`

**MODIFIED:**
- `backend/app/main.py` (`lifespan`: load registry into `app.state.certifications` + 1 import)

### Change Log
- 2026-06-11: Story 9.1 implemented — per-Certification config model (Pydantic v1), file-based fail-loud loader + lookup helpers, seed `config/certifications.yaml` re-expressing today's Databricks Associate/Professional literals, startup wiring into `app.state.certifications`, and 13 tests incl. the parity anchor vs `MOCK_EXAM_CONFIGS`/`Domain`/`READINESS_THRESHOLD`. Additive only — no enum/`MOCK_EXAM_CONFIGS`/endpoint changes. Status → review.
- 2026-06-12: Code review (Blind Hunter + Edge Case Hunter + Acceptance Auditor, scoped to 9.1's 4 files). Auditor confirmed all 9 ACs satisfied. 7 patch findings + 4 deferred + 3 dismissed — see Review Findings below.
- 2026-06-12: Applied all 7 review patches to `backend/app/certifications.py` — strict-int coercion via `conint(strict=True, …)` (+ `pass_bar` bool guard), file-aware `_resolve_config_path` (`is_file()`), `get_certification` empty/None guard, `id` stored stripped, duplicate-domain-name rejection, non-empty `name` fields, and full dup-id reporting. Added 10 regression tests (`TestReviewHardening`). `ruff` clean; full backend suite **324 passed, 0 failed** (the prior 2 failures were entangled 7.6 WIP, since committed). No unresolved High/Medium findings → Status → done.

## Review Findings (AI Code Review — 2026-06-12)

Scope: commit `2e4e9eb` limited to 9.1's files (`certifications.py`, `main.py`, `test_certifications.py`, `certifications.yaml`). Layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor (all completed; none failed). Acceptance Auditor confirmed **all 9 acceptance criteria satisfied** — these findings are robustness hardening, not AC violations.

### Patch (fix candidates — unambiguous)
- [x] [Review][Patch] **Lax numeric coercion defeats `ge=0` / sum-to-100 fail-loud guarantee** [backend/app/certifications.py:49,57-59,69-77] — Pydantic v1 coerces `int` fields *before* validators run, so a float `weight: 100.9`→`100` (and `weight: -0.5`→`0`) passes; `bool` (`weight: true`/YAML `yes`)→`1`; `pass_bar: 1`(int)→`1.0`. A fractional/typo'd weight is silently accepted or yields a misleading "got 99". Fix: use `StrictInt` for `weight`/`total_questions`/`duration_minutes` (+ reject `bool`), and reject `bool` for `pass_bar`. (HIGH; source: edge)
- [x] [Review][Patch] **`_resolve_config_path` matches the first ancestor dir merely *named* `config`** [backend/app/certifications.py:138-144] — if an unrelated `config/` exists up-tree (or a non-dir file named `config`), it returns a path whose file is absent → misleading "not found" pointing at the wrong location, even when the real config exists higher up. Fix: require `(candidate / CONFIG_FILENAME).is_file()` (and/or `candidate.is_dir()`). NOTE: `content.py` shares this latent pattern; fixing here is a strict improvement, not a divergence from intent. (MEDIUM; source: blind+edge)
- [x] [Review][Patch] **`get_certification(None)` raises `AttributeError`, violating its documented `Raises: CertificationConfigError`** [backend/app/certifications.py:~201] — `exam_id.strip()` on `None` crashes raw; `domain_weights`/`exam_params` inherit it. 9.2 consumers catching `CertificationConfigError` won't catch this. Fix: guard `if not exam_id or not exam_id.strip(): raise CertificationConfigError(...)` at the top. (MEDIUM; source: edge)
- [x] [Review][Patch] **`Certification.id` validated stripped but stored unstripped** [backend/app/certifications.py:62-67] — `id: " associate "` is stored verbatim, so `cert.id != "associate"` even though lookup/dedup normalize with `.strip().lower()`. Dedup and storage disagree (`"associate"` vs `" associate "` collide on lookup but aren't flagged as dup). Fix: `return v.strip()` in `id_not_empty`. (MEDIUM; source: edge)
- [x] [Review][Patch] **Duplicate domain `name`s within one certification silently collapse** [backend/app/certifications.py:69-77,~210] — the `domains` validator checks count + sum only; `domain_weights` builds `{d.name: d.weight}`, so two domains with the same name collapse and the returned map no longer sums to 100 — breaking the invariant on the helper's actual output. Fix: reject `len({d.name for d in v}) != len(v)` in the `domains` validator. (LOW; source: edge)
- [x] [Review][Patch] **Empty-string `name` accepted on domain/cert/provider** [backend/app/certifications.py:48] — `id` has a non-empty validator but `name` fields don't; a blank `CertificationDomain.name` (the enum join key) produces a structurally-valid-but-useless entry. Fix: `min_length=1` (at minimum on `CertificationDomain.name`). (LOW; source: edge)
- [x] [Review][Patch] **Duplicate-id error reports only the second (raw) colliding id** [backend/app/certifications.py:119-126] — collision is detected on the normalized key but `dupes.add(cert.id)` records only the later raw id, so the message omits the first conflicting entry. Fix: report all ids sharing a normalized key. (LOW; source: blind)

### Deferred (recorded in deferred-work.md)
- [x] [Review][Defer] **`pydantic` version mismatch: `requirements.txt`==2.5.0 vs `pyproject.toml`<2.0 (venv runs v1)** — pre-existing dependency inconsistency; affects this module's validator/coercion correctness. Reconcile to one canonical version. (elevated importance)
- [x] [Review][Defer] **No startup cross-check of registry ids vs loaded exercise `exam` values** — intentionally out of scope; belongs to Story 9.4 (cert-scoped validation & content mapping).
- [x] [Review][Defer] **`main.py` `"seen"` docstring hunk is out-of-scope Story 7.6 content** committed alongside 9.1 — documentation-only, no action for 9.1.
- [x] [Review][Defer] **AC5 "every existing test green" not observable** in a clean full-suite run due to entangled 7.6 WIP (2 failing tests) — re-confirm once 7.6 lands.

### Dismissed (noise / per-spec / handled-by-design)
- `exam_params` returning `dict[str, object]` — the dict shape is exactly what the spec prescribed (`{total_questions, duration_minutes, pass_bar}`); design-per-spec, not a defect.
- Broad `except Exception` in the loader — defensively correct: it also catches non-`ValidationError` construction errors (e.g. non-string YAML keys via `**data`), always names the file, and chains via `from e`. The edge layer tested it and cleared it; the spec's "ValidationError" was illustrative.
- Parity test not asserting per-exam domain-set composition — the `seed_map == expected_map` assertion already pins exact per-exam domain membership against `MOCK_EXAM_CONFIGS`; non-issue (auditor self-retracted).
