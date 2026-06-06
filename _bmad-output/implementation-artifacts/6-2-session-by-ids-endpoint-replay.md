---
status: ready-for-dev
baseline_commit: 10824eb
---

# Story 6.2: Session-by-IDs Endpoint (Replay)

**Epic:** 6 - Session Control & Study QoL
**Story Key:** 6-2-session-by-ids-endpoint-replay

## Story Statement

As the **frontend**,
I want **`POST /api/sessions {exerciseIds}` to build a fresh session for a specific set of exercises**,
So that **"Restart" and "Practice these again" re-sample options and re-randomize order rather than replaying identical questions**.

This closes gap **G2** from architecture rev 3 — the replay endpoint that powers the Summary screen's "Restart this session" (UX-DR4) and "Practice these N again" (UX-DR10) actions, while preserving the FR-20/21 freshness and non-leakage guarantees.

## Acceptance Criteria

**Given** a list of exercise ids
**When** I call `POST /api/sessions` with body `{exerciseIds: [...]}`
**Then** the response uses the standard `{success, data, error}` wrapper and `data` is a list of session entries whose shape matches `GET /api/sessions` (each MCQ carrying exactly 4 flag-less `displayedOptions` of `{id, text}`, in randomized order)
**And** the Displayed Options are freshly sampled and shuffled per call (the correct option and/or distractors can differ from a prior presentation of the same exercise; the correct option is not position-stable)
**And** no `correct` field appears anywhere in the payload (non-leakage preserved — FR-20)
**And** unknown / unmatched ids are dropped and logged at WARNING, not treated as fatal (the request still succeeds over the recognized subset)
**And** an empty `exerciseIds` (or one that matches nothing) returns a successful empty list `data: []`, not an error
**And** it reuses the Story 5.3 randomizer (`app/session.py build_session`) over the filtered-by-id exercise list (no duplicated sampling/shuffle logic)
**And** `pytest` tests cover a known id set, freshness across repeated calls, and unknown-id handling

## Architecture Context

- **Decision (G2):** `POST /api/sessions` builds a session from an explicit exercise-id set. Request `{exerciseIds: [...]}`; **same response shape as `GET /api/sessions`**, with freshly sampled + shuffled Displayed Options and re-randomized order so replays keep FR-20/21 freshness. The client holds only flag-less options and therefore cannot re-sample itself — the backend must rebuild. Unknown ids are dropped (logged), not fatal. [Source: architecture.md#L352, #L854]
- **Non-leakage (FR-20):** the response carries only `{id, text}` per Displayed Option; `correct` flags never leave the backend. [Source: architecture.md#L461]
- **Freshness (FR-20/21):** per-presentation sampling + position shuffle, plus per-session order randomization, computed server-side, uniform-at-random, no seed / no anti-repeat memory. [Source: architecture.md#L459-#L460, #L458]
- **Reuse the randomizer:** the randomness lives in `app/session.py build_session` / `build_displayed_options` (Epic 5, Story 5.3). This story only adds id-filtering + the POST route; it does NOT re-implement sampling. [Source: architecture.md#L888; backend/app/session.py]
- **Response wrapper:** all endpoints return `{success: bool, data, error}` (AR-5). [Source: architecture.md#L350-#L353]

### Current behavior of `GET /api/sessions` (to mirror)

`backend/app/main.py` `get_session()` (lines 136-200):
1. Reads `app.state.exercises` defensively via `getattr(app.state, "exercises", [])`.
2. Validates `domain` / `difficulty` query params case-insensitively against the `Domain` / `Difficulty` enums; returns `{success: False, data: [], error}` on an invalid filter.
3. Calls `filter_exercises(exercises, domain=..., difficulty=...)` from `app/content.py`.
4. Passes the filtered list to `build_session(filtered)` and returns `{success: True, data: session, error: None}`. An empty filter result is a successful empty session, not an error.

`build_session(exercises)` (`backend/app/session.py`, lines 104-128): keeps only `MCQ` instances that are not `code_completion`, shuffles a copy of that list (FR-21), and returns one `build_session_entry` per MCQ. Each entry is `{exerciseId, type, domain, difficulty, question, codeContext, displayedOptions}` where `displayedOptions` is 4 `{id, text}` dicts (1 correct + 3 incorrect, sampled and shuffled, no `correct` flag — FR-20).

### How the POST variant reuses `build_session`

Instead of filtering by domain/difficulty, the POST route filters `app.state.exercises` down to the exercises whose `id` is in the request's `exerciseIds`, then passes that filtered list straight into the same `build_session(...)`. Because `build_session` re-shuffles order and `build_displayed_options` re-samples + re-shuffles options on every call, replays are automatically fresh with zero new randomization code. Unknown ids simply don't match any loaded exercise and are dropped; log them at WARNING so a stale frontend id set is diagnosable.

## Tasks/Subtasks

- [ ] Task 6.2.1: Define the request model
  - [ ] In `backend/app/main.py`, add a `SessionByIdsRequest(BaseModel)` with `exerciseIds: list[str] = Field(...)` (camelCase JSON field, per AR-12), mirroring the existing `FeedbackRequest` style
  - [ ] Document that ids are the original authored exercise ids (e.g. `dbx-de-0001`)

- [ ] Task 6.2.2: Implement the `POST /api/sessions` route
  - [ ] Add `@app.post("/api/sessions")` handler `post_session(request: SessionByIdsRequest)`
  - [ ] Read exercises defensively: `exercises = getattr(app.state, "exercises", [])`
  - [ ] Build a lookup of recognized ids; partition `request.exerciseIds` into matched vs unknown
  - [ ] Log dropped/unknown ids at WARNING (include the ids), do not raise
  - [ ] Preserve the order the ids were given when collecting matched exercises (order is re-randomized by `build_session` anyway, but keep selection deterministic for testability)
  - [ ] Call `build_session(matched)` and return `{success: True, data: session, error: None}`
  - [ ] Empty / all-unknown `exerciseIds` returns `{success: True, data: [], error: None}`

- [ ] Task 6.2.3: Confirm shape parity with `GET /api/sessions`
  - [ ] Reuse `build_session` exactly (no inline sampling/shuffle) so the entry shape and non-leakage are identical by construction

- [ ] Task 6.2.4: Tests (`backend/tests/`, e.g. `test_sessions_post.py`)
  - [ ] Known id set: POST a subset of real loaded ids; assert `success`, that `data` length equals the number of MCQs among those ids, that each entry has 4 `displayedOptions` of exactly `{id, text}`, and that the returned `exerciseId`s are a subset of the requested ids
  - [ ] Non-leakage: assert no `correct` key anywhere in any displayed option
  - [ ] Freshness across calls: POST the same id set twice; assert that across enough calls the option ordering and/or the sampled option set for a given exercise varies (matches the Story 5.3 freshness test approach — assert *not always identical* rather than *always different* to avoid flakiness)
  - [ ] Unknown-id handling: POST a mix of valid + bogus ids; assert `success: True`, the bogus ids are absent from `data`, and only matched exercises appear
  - [ ] Empty input: POST `{exerciseIds: []}` → `success: True`, `data: []`
  - [ ] Run with `uv run pytest` (see Dev Notes)

## Dev Notes

- **UPDATE** `backend/app/main.py` — add `SessionByIdsRequest` model and the `POST /api/sessions` route alongside the existing `GET /api/sessions` (line 136) and `FeedbackRequest` (line 247). Do not change `get_session`.
- **NEW** `backend/tests/test_sessions_post.py` (or extend the existing sessions test module if one exists) — the test cases above.
- **No changes** to `backend/app/session.py` or `backend/app/content.py` — both `build_session` (session.py:104) and the exercise corpus in `app.state.exercises` already provide everything. Reuse, don't fork.
- **What to preserve:**
  - The `{success, data, error}` wrapper (AR-5).
  - Exact `GET /api/sessions` entry shape (`build_session` guarantees this).
  - FR-20 non-leakage — only `{id, text}` per displayed option; never emit `correct`.
  - FR-20/21 freshness — every call re-samples and re-orders; do not cache or memoize the built session.
  - Defensive `getattr(app.state, "exercises", [])` access so the route is safe if hit before startup.
- **Unknown-id policy:** drop + log at WARNING (mirrors the loader's tolerant logging style in `content.py`); a replay must never 4xx just because the frontend's id set drifted from the corpus.
- **Non-MCQ ids:** if an id resolves to a `code_completion` exercise, `build_session` silently skips it (same as `GET /api/sessions`); that is acceptable for MVP.
- **Tooling — uv, never pip.** Run tests with `uv run pytest` from `backend/`. Do not invoke `pip` or call `pytest` directly outside the uv environment.

## References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 6, Story 6.2 (lines 720-734)]
- [Source: _bmad-output/planning-artifacts/architecture.md — G2 decision (lines 352, 854); FR-20 non-leakage (line 461); FR-20/21 freshness (lines 458-460); revision note rev 3 (line 10)]
- [Source: backend/app/main.py — `GET /api/sessions` (lines 136-200), `{success, data, error}` wrapper, `app.state.exercises`, `FeedbackRequest` model pattern (lines 247-260)]
- [Source: backend/app/session.py — `build_session` (lines 104-128), `build_displayed_options` (lines 37-69), `build_session_entry` (lines 72-101)]
- [Source: backend/app/content.py — `filter_exercises` (lines 258-311), loader behavior/logging style]
- [Source: epics.md — Story 5.3 Server-Side Session Randomizer (lines 628-643); Story 5.4 GET /api/sessions (lines 647-661)]

## Dev Agent Record

### Implementation Plan

(To be filled in by the dev agent)

### Subtasks Completed

(To be filled in as implementation progresses)

### Completion Notes

(To be filled in upon task completion)

## File List

(Files will be listed here upon completion)

## Change Log

- Initial story creation — 2026-06-06

## Status

ready-for-dev
