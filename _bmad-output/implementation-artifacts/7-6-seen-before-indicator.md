---
baseline_commit: 247164b0171190bdd3630562503050f58917dd9c
---

# Story 7.6: Seen-Before Indicator

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **student practicing questions**,
I want **a small, unobtrusive indicator on each exercise that I've attempted before**,
so that **I instantly know whether I'm seeing fresh material or revisiting something, without it leaking whether I got it right**.

## Acceptance Criteria

**Given** a built practice session and recorded attempt history
**When** `GET /api/sessions` (normal mode) builds the session
**Then** each MCQ session entry carries a boolean `seen` field — `true` when the exercise has ≥1 recorded attempt in the store, `false` otherwise
**And** the `seen` flag is derived from `store.attempted_ids()` (the same signal that drives unseen-first ordering), not from anything that reveals correctness
**And** option sampling/position-shuffle (FR-20) and unseen-first ordering (FR-24) remain unchanged

**Given** a replay session
**When** `POST /api/sessions` builds a session from explicit ids (`prioritize_unseen=False`)
**Then** entries still carry the correct `seen` flag (replayed exercises are typically already-seen, so this is the common case the indicator must handle)

**Given** a Mock-Exam session (`mode=mock`)
**When** `build_mock_session` builds the set
**Then** entries do **not** carry a truthy `seen` flag (mock deliberately ignores history; the indicator stays hidden to preserve exam realism)

**Given** a Code-Completion session entry
**When** the session is built
**Then** its `seen` flag is `false` (Code-Completion attempts are not recorded in the MCQ-scoped store, so there is no seen signal — it must never falsely render as seen)

**Given** I am viewing an exercise whose `seen` flag is `true` in the MCQ runner (`MCQPractice.jsx`)
**When** the question renders
**Then** a small **grey eye icon** appears in the metadata header row (alongside the domain/difficulty badges)
**And** hovering the icon shows a tooltip reading "You've attempted this exercise before"
**And** the icon is accessible: it has an equivalent accessible name (screen-reader text / `aria-label`), and it is decorative-grey (`text-gray-400`), visually subordinate to the domain/difficulty badges
**And** when `seen` is falsy the icon is **not** rendered at all

**Given** I am viewing a (seen) exercise in the Code-Completion runner (`CodeCompletion.jsx`)
**When** the question renders
**Then** the same indicator behavior applies — but because Code-Completion `seen` is always `false`, the icon will not currently appear there (the shared component must still be wired so it lights up automatically if Code-Completion attempts are ever recorded)

**Given** the changes above
**When** the test suites run
**Then** `pytest` covers: `seen=true` for an attempted MCQ, `seen=false` for an unattempted MCQ, `seen=false` for Code-Completion, correct flags through both `GET` and `POST /api/sessions`, and no truthy `seen` on mock entries
**And** `vitest` covers: the eye icon + tooltip render when `seen` is true, the icon is absent when `seen` is falsy, and the accessible name is present — for both runners
**And** backend lint (`ruff`) and frontend lint are clean

## Tasks / Subtasks

- [x] **Task 1 — Stamp `seen` onto session entries (backend)** (AC: 1, 2, 4)
  - [x] In `backend/app/session.py`, compute `attempted = store.attempted_ids()` **once** inside `build_session(...)` (covers BOTH `prioritize_unseen=True` and `False`) and stamp `entry["seen"]` on each built entry.
  - [x] Avoid a duplicate store read: `_order_unseen_first` refactored to accept an optional pre-fetched `attempted`/`last_seen` (defaults preserve prior behavior); `build_session` now reads the store at most once per call.
  - [x] Code-Completion entries report `seen=false`. Implemented defensively (keyed on entry type), so they never falsely render as seen even on an id collision — see Completion Notes.
  - [x] `build_mock_session` leaves `seen` unset (mock indicator stays hidden); added an intentional-exclusion comment (exam realism).
- [x] **Task 2 — Document the new entry field (backend)** (AC: 1)
  - [x] Updated `build_session_entry` / `build_code_completion_entry` / `build_session` / `build_mock_session` docstrings in `session.py` and the `GET /api/sessions` shape block in `main.py` to document `"seen": bool` (and the mock omission).
- [x] **Task 3 — Shared `SeenIndicator` component (frontend)** (AC: 5, 6)
  - [x] Added `frontend/src/components/SeenIndicator.jsx`: renders nothing when `seen` is falsy; otherwise a grey eye SVG (`text-gray-400`) with `title` + `sr-only` accessible name. `aria-hidden` SVG.
  - [x] No new dependency — inline SVG + native `title`, matching the existing convention.
- [x] **Task 4 — Wire the indicator into both runners** (AC: 5, 6)
  - [x] `MCQPractice.jsx`: `<SeenIndicator seen={exercise.seen} />` in the metadata header row, before the Timer.
  - [x] `CodeCompletion.jsx`: same indicator in its mirrored metadata header.
- [x] **Task 5 — Tests** (AC: 7, 8, 9)
  - [x] Backend: `seen` true/false for attempted/unattempted MCQ, false for Code-Completion, present on `GET` + `POST /api/sessions`, not truthy on `mode=mock`. Updated the two shape-pinning endpoint tests to include `seen`.
  - [x] Frontend: `SeenIndicator.test.jsx` (present/absent/accessible name) + `MCQPractice.test.jsx` (eye present for seen, absent for unseen/absent).
- [x] **Task 6 — Verify** (AC: all)
  - [x] `cd backend && uv run pytest` → 314 passed; `uv run ruff check .` → clean.
  - [x] `cd frontend && npx vitest run` → 182 passed; `eslint` on changed files → clean.

### Review Findings

Code review 2026-06-11 (3 adversarial layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor). 0 decision-needed, 1 patch, 0 deferred, 6 dismissed as noise.

- [x] [Review][Patch] `build_session` docstring overstates store reads — says "the store is read at most once per call", but `last_seen_map()` is still a separate read inside `_order_unseen_first` when `prioritize_unseen=True`. Only the `attempted_ids()` duplicate read is eliminated. [backend/app/session.py:359] — Fixed: docstring now states `attempted_ids()` is read once (not twice) and notes `_order_unseen_first` still does its own `last_seen_map()` read.

Reviewer note (informational, not a 7.6 defect): the `git diff HEAD` for `backend/app/main.py` also contains Story 9.1's certification-registry startup code (pre-existing uncommitted work in the same file). 7.6's only main.py change is the `"seen": bool` docstring shape note. Keep the 9.1 code out of any 7.6-scoped commit; it's tracked under story 9-1.

## Dev Notes

### What this story does (and does not) change

This is a small QoL enhancement on top of the existing Epic 7 attempt-tracking machinery. The "seen" signal **already exists** server-side — `store.attempted_ids()` is what powers unseen-first ordering (Story 7.3). This story merely (a) surfaces that boolean onto each session entry and (b) renders a quiet grey eye + tooltip when it's true. No schema change, no new endpoint, no change to ordering, sampling, or grading.

### Backend — current state of files being modified

- **`backend/app/session.py`** — `build_session(exercises, *, prioritize_unseen=True)` is the single funnel for the normal session (`GET /api/sessions` calls it; `POST /api/sessions` calls it with `prioritize_unseen=False`). It currently returns entries WITHOUT a `seen` field. `_order_unseen_first(exercises)` already reads `store.attempted_ids()` and `store.last_seen_map()`. `build_mock_session(...)` deliberately does **not** consult the store (representative exam set) — leave it that way; do not add a truthy `seen` there.
  - **Preserve:** the Code-Completion sprinkle logic, the unseen/seen partition, FR-20 random sampling, and the "input list is not mutated" contract. The `seen` stamp must be additive — every existing field on each entry stays as-is.
- **`backend/app/store.py`** — `attempted_ids(exam=None, domain=None, difficulty=None, path=None) -> set[str]` returns distinct attempted exercise ids. Call it with **no filters** for the `seen` stamp (the indicator means "attempted ever", matching the global unseen signal `build_session` already uses). DB path is overridable via `ATTEMPT_DB_PATH` env var or `path=` arg — tests use this for a temp DB.
- **`backend/app/main.py`** — `GET /api/sessions` (line ~164) → normal path calls `build_session(filtered)`; mock path calls `build_mock_session(...)`. `POST /api/sessions` (line ~389) calls `build_session(matched, prioritize_unseen=False)`. The endpoints just pass the builder output straight into the `{success, data, error}` wrapper, so stamping `seen` in `build_session` automatically flows to both — **no endpoint logic change needed**, only the docstring shape note.

#### Recommended backend implementation sketch

```python
# session.py — build_session(...)
runnable = [ex for ex in exercises if isinstance(ex, (MCQ, CodeCompletion))]
attempted = store.attempted_ids()  # fetch once, no filters

if prioritize_unseen:
    order = _order_unseen_first(runnable, attempted=attempted)  # reuse, don't re-query
else:
    order = list(runnable)
    random.shuffle(order)

entries = [_build_entry(ex) for ex in order]
for entry in entries:
    entry["seen"] = entry["exerciseId"] in attempted
return entries
```

Refactor `_order_unseen_first` to accept the pre-fetched set so the store is read at most once:

```python
def _order_unseen_first(exercises, attempted=None, last_seen=None):
    if attempted is None:
        attempted = store.attempted_ids()
    if last_seen is None:
        last_seen = store.last_seen_map()
    ...
```

### Frontend — current state of files being modified

- The `seen` flag rides through untouched: `SessionContext` stores raw API entries and exposes `currentExercise`, so `currentExercise.seen` is available in both runners with **no context change**.
- **`frontend/src/pages/MCQPractice.jsx`** — metadata header is the `<div className="flex items-center gap-2 shrink-0">` block (≈ lines 235–262) holding the domain badge (`bg-databricks-50`), difficulty badge (`DIFFICULTY_STYLES`), optional `<Timer />`, and the End-session button. Drop `<SeenIndicator seen={exercise.seen} />` in here, before the Timer.
- **`frontend/src/pages/CodeCompletion.jsx`** — mirrored metadata header (≈ lines 132–146) with the same domain/difficulty badges. Add the same indicator there for parity (it won't show today since CC `seen` is always false, but the wiring future-proofs it).
- **No tooltip/icon library exists.** `package.json` has none; tooltips elsewhere use the native `title` attribute and accessibility via `sr-only` text / `aria-label` (see `MCQPractice.jsx`'s `aria-label="Keyboard shortcuts"`, the `aria-hidden` glyphs, `Timer.jsx`). Follow that pattern exactly — inline SVG eye + `title` + `sr-only`/`aria-label`. Do **not** add a dependency.

#### Recommended `SeenIndicator.jsx` sketch

```jsx
export default function SeenIndicator({ seen }) {
  if (!seen) return null
  const label = "You've attempted this exercise before"
  return (
    <span title={label} className="inline-flex items-center text-gray-400">
      <span className="sr-only">{label}</span>
      <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4" fill="none"
           stroke="currentColor" strokeWidth="2">
        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </span>
  )
}
```

(Exact markup is the dev's call as long as it renders a grey eye, exposes the accessible name, shows the tooltip on hover, and renders nothing when `seen` is falsy.)

### Testing standards

- **Backend:** pytest, tests in `backend/tests/`. Seed history with `store.record_attempt(...)` against a temp DB (`ATTEMPT_DB_PATH` or `path=`). Existing session/endpoint tests live in `backend/tests/test_sessions.py` / `test_sessions_post.py` — extend those rather than starting fresh. Run with `uv run pytest` (no pip).
- **Frontend:** vitest + Testing Library, co-located `*.test.jsx`. Mock the api in page tests as the existing `MCQPractice.test.jsx` does; query the indicator by its accessible name (`getByTitle` / `getByLabelText` / role `img` with name). Assert absence with `queryBy...` returning null.

### Project Structure Notes

- New file: `frontend/src/components/SeenIndicator.jsx` (+ `SeenIndicator.test.jsx`) — sits alongside the other shared presentational components (`ProgressBar`, `Timer`, `ReadinessIndicator`).
- Modified: `backend/app/session.py`, `backend/app/main.py` (docstring only), `frontend/src/pages/MCQPractice.jsx`, `frontend/src/pages/CodeCompletion.jsx`, plus the corresponding test files.
- No migrations, no new endpoints, no config changes. Additive `seen` field is backward-compatible (older clients ignore it).
- **Decision — global vs filtered "seen":** the stamp uses unfiltered `attempted_ids()` (attempted *ever*, in any exam/domain), matching the global signal `build_session` already relies on. A given exercise id is exam-specific anyway, so this is unambiguous.
- **Decision — mock excluded:** the indicator is intentionally suppressed in Mock-Exam mode to keep the simulation exam-like. If product later wants it in mock too, it's a one-line addition in `build_mock_session`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 7: Answer & Stats Tracking] — FR-22 (persist attempts), FR-24 (unseen-first), AR-16/AR-17 (store + endpoints) establish the seen/unseen signal this story surfaces.
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3: Unseen-First Session Ordering] — defines the unseen/seen partition (`attempted_ids`) reused here.
- [Source: backend/app/session.py] — `build_session`, `_order_unseen_first`, `build_mock_session`, `SessionEntry` shape.
- [Source: backend/app/store.py#attempted_ids] — the seen signal; temp-DB override for tests.
- [Source: backend/app/main.py] — `GET /api/sessions` (~164), `POST /api/sessions` (~389), response wrapper + entry-shape docstring.
- [Source: frontend/src/pages/MCQPractice.jsx#L235] — metadata header row where the indicator mounts.
- [Source: frontend/src/pages/CodeCompletion.jsx#L132] — mirrored metadata header row.
- [Source: _bmad-output/project-context.md] — backend rule: use **uv**, never pip.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (1M context)

### Debug Log References

- Backend: `cd backend && uv run pytest -q` → 314 passed. `uv run ruff check .` → clean.
- Frontend: `npx vitest run` → 182 passed (16 files). `eslint` on changed files → clean.

### Completion Notes List

- **`seen` derived from the existing signal, fetched once.** `build_session` now calls `store.attempted_ids()` a single time and (a) threads it into `_order_unseen_first` (refactored to accept optional `attempted`/`last_seen`, defaults unchanged) and (b) stamps `entry["seen"]` on every built entry — so neither ordering mode adds a second store read. Flows automatically to both `GET` and `POST /api/sessions` (no endpoint logic change).
- **Deviation from the story's "do not special-case Code-Completion" note — intentional.** AC explicitly requires CC `seen` to be `false` and to "never falsely render as seen". The generic `id in attempted` check would return `true` if an MCQ attempt row happened to share the CC id. The stamp is therefore keyed on entry type: `entry["seen"] = entry["type"] != "code_completion" and entry["exerciseId"] in attempted`. This satisfies the AC literally and defensively; a test seeds a colliding id to prove CC stays `false`.
- **Mock-Exam excluded.** `build_mock_session` leaves `seen` unset; a test asserts no mock entry carries a truthy `seen` even when every exercise is attempted (exam realism).
- **Two existing shape-pinning endpoint tests updated** (`test_sessions.py`, `test_sessions_post.py`) to include the new additive `seen` key — required because they assert the exact key set.
- **Frontend:** `SeenIndicator` renders nothing when falsy; otherwise a grey eye SVG with a `title` tooltip + `sr-only` accessible name (no icon-library dependency, matching the repo convention). Wired into both runners via `exercise.seen`, which rides through `SessionContext` untouched. CC won't show the eye today (its `seen` is always false) but the wiring future-proofs it.

### File List

- `backend/app/session.py` (modified) — `build_session` stamps `seen`; `_order_unseen_first` accepts pre-fetched `attempted`/`last_seen`; docstrings.
- `backend/app/main.py` (modified) — `GET /api/sessions` docstring shape block documents `seen`.
- `backend/tests/test_session.py` (modified) — `TestSeenFlag`.
- `backend/tests/test_code_completion_session.py` (modified) — CC `seen` always false.
- `backend/tests/test_mock_exam.py` (modified) — mock entries carry no truthy `seen`.
- `backend/tests/test_sessions.py` (modified) — `seen` in expected MCQ/CC key sets + endpoint `seen` test.
- `backend/tests/test_sessions_post.py` (modified) — `seen` in expected key set + replay `seen` test.
- `frontend/src/components/SeenIndicator.jsx` (new) — the indicator component.
- `frontend/src/components/SeenIndicator.test.jsx` (new) — component tests.
- `frontend/src/pages/MCQPractice.jsx` (modified) — import + render `<SeenIndicator>`.
- `frontend/src/pages/CodeCompletion.jsx` (modified) — import + render `<SeenIndicator>`.
- `frontend/src/pages/MCQPractice.test.jsx` (modified) — indicator present/absent tests.

## Change Log

- 2026-06-11 — Implemented Story 7.6 (seen-before indicator): backend `seen` flag on session entries + frontend grey-eye `SeenIndicator` in both runners. Backend 314 tests pass, frontend 182 tests pass, lint clean. Status → review.
