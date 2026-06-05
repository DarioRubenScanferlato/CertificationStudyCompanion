---
review_date: 2026-06-05
scope: Epic 2 — Exercise Content Management System (Stories 2.1–2.5)
reviewer: bmad-code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor)
files_reviewed: 12 (3 modified, 9 new) ~2884 diff lines
---

# Epic 2 — Code Review Findings

## Summary

- **4** decision-needed → all resolved (D2, D3 applied; D1, D4 deferred to Anki pass)
- **12** patch → **9 non-Anki applied**, 7 Anki-related deferred (incl. D1/D4)
- **8** defer → unchanged
- **6** dismissed as noise

All three review layers completed (none failed). This pass fixed all non-Anki issues
per user request; Anki-specific patches remain as action items.

## Review Findings

### Decisions (resolved 2026-06-05)

- **D1 — Anki endpoint error contract** → RESOLVED: use proper HTTP status codes (400 invalid filter, 404 no matches, file on 200). Converted to patch, **deferred as Anki action item** (not applied this pass). [main.py export_anki]
- **D2 — Filter case/whitespace consistency** → RESOLVED: all filters case-insensitive + whitespace-trimmed. **APPLIED.** [main.py get_exercises, content.py filter_exercises]
- **D3 — MCQ `answer` ↔ `Option.correct`** → RESOLVED: derive `answer` from `Option.correct` (single source of truth). **APPLIED.** [models.py MCQ]
- **D4 — genanki dependency placement** → RESOLVED: lazy import + move to optional-dependencies. **Deferred as Anki action item** (not applied this pass). [pyproject.toml, main.py, anki.py]

### Patch — Applied (non-Anki)

- [x] [Review][Patch] HIGH — Unknown exercise `type` now rejected as `unknown_type` (missing type still defaults to MCQ); explicit type dispatch via `TYPE_MODELS` [content.py] (blind+edge+auditor)
- [x] [Review][Patch] HIGH — Duplicate exercise IDs detected at load and reported as `duplicate_id`, preventing silent GUID collision [content.py] (blind+edge)
- [x] [Review][Patch] MED — All filters validated case-insensitively + whitespace-trimmed [main.py get_exercises, content.py filter_exercises] (blind+edge) [D2]
- [x] [Review][Patch] MED — `problem_mark` value bound and null-checked before `.line` access [content.py YAMLError handler] (blind)
- [x] [Review][Patch] MED — `app.state.exercises` read via `getattr(..., [])` guard [main.py get_exercises] (blind+edge)
- [x] [Review][Patch] LOW — Removed dead clause `or e.domain == domain`; all filters compare normalized `.value` [content.py filter_exercises] (blind+auditor)
- [x] [Review][Patch] LOW — Removed unused `Optional` import in models.py [models.py] (blind+edge)
- [x] [Review][Patch] LOW — Replaced vacuous `assert error_count >= 0` with meaningful YAML-tab syntax-error assertions [test_content_validation.py] (blind)
- [x] [Review][Patch] LOW — `single_choice` now validated to have exactly one correct option (via derive-answer root_validator) [models.py MCQ] (blind) [D3]

### Patch — Deferred as Anki action items (not applied this pass)

- [ ] [Review][Patch] HIGH — Temp `.apkg` file leaked on every export (success and exception paths); `delete=False` with no cleanup [main.py export_anki] (blind+edge+auditor)
- [ ] [Review][Patch] MED — `/api/export/anki` performs no filter validation; a typo'd domain looks like an empty result [main.py export_anki] (blind+edge+auditor)
- [ ] [Review][Patch] MED — Anki card fields inserted as raw HTML; `<`, `>` in SQL/PySpark content breaks card rendering [anki.py export_to_anki] (blind+edge) [M6]
- [ ] [Review][Patch] LOW — `get_deck_info` unused `json` import + inconsistent return shape [anki.py get_deck_info] (blind+edge+auditor)
- [ ] [Review][Patch] LOW — Unused `ExerciseType` import in anki.py [anki.py] (blind)
- [ ] [Review][Patch] [D1] Anki endpoint HTTP status codes [main.py export_anki]
- [ ] [Review][Patch] [D4] Lazy genanki import + optional dependency [main.py, anki.py, pyproject.toml]

### Deferred (pre-existing / out-of-scope now)

- [x] [Review][Defer] CodeCompletion path has zero test coverage and zero YAML content (Phase 2 feature) [models.py, tests/, exercises/] — deferred (edge+auditor)
- [x] [Review][Defer] conftest duplicates lifespan loading logic; shared mutable `app.state` across test session; bare `TestClient(app)` may not run lifespan [conftest.py, test_filtering.py] — deferred, test infra works currently (blind+edge)
- [x] [Review][Defer] `answer_references_valid_options` is Pydantic-v1 order-dependent and silently skips the cross-check when `options` validation fails [models.py] — deferred, Pydantic v1 limitation (blind)
- [x] [Review][Defer] Filter comparisons rely on str-Enum equality coincidence rather than `.value` [content.py filter_exercises] — deferred, fragile but functional (blind+auditor)
- [x] [Review][Defer] List/scalar-root YAML misclassified as `file_read_error` instead of `missing_exercises_key` [content.py] — deferred, edge case (edge)
- [x] [Review][Defer] `test_get_deck_info_invalid_file` reads temp file while handle still open (cross-platform fragility) [test_anki.py] — deferred, passes on dev platform (blind)
- [x] [Review][Defer] `exercise_set` filter named in Story 2.2 architecture context never implemented (spec is internally inconsistent) [main.py, content.py] — deferred (auditor)
- [x] [Review][Defer] Story files 2.2–2.5 still show unchecked tasks / `ready-for-dev`; Story 2.1 completion notes cite wrong line counts (models.py 167 vs actual 124) [spec files] — deferred, tracking hygiene (auditor)

### Dismissed (noise / false positives)

- `exercise_type` query param vs `type` response field name — reasonable API clarity choice
- `test_anki.py`/`test_anki_endpoint.py` vs spec-named `test_export.py` — naming only, behavior covered
- No standalone `convert_mcq_to_note` function (inlined) — equivalent behavior
- `export_to_anki` vs spec-named `export_exercises_to_anki` — naming only
- Hardcoded deck/model IDs — intentional for reproducible re-import
- `NamedTemporaryFile` vs `mkstemp` idiom — folded into temp-leak patch
