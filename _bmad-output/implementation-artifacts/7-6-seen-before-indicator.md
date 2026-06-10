# Story 7.6: Seen-Before Indicator

Status: ready-for-dev

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

- [ ] **Task 1 — Stamp `seen` onto session entries (backend)** (AC: 1, 2, 4)
  - [ ] In `backend/app/session.py`, compute `attempted = store.attempted_ids()` **once** inside `build_session(...)` (covers BOTH `prioritize_unseen=True` and `False`) and stamp `entry["seen"] = entry["exerciseId"] in attempted` on each built entry.
  - [ ] Avoid a duplicate store read: `_order_unseen_first` already calls `store.attempted_ids()`. Refactor it to accept an optional pre-fetched `attempted` set (e.g. `_order_unseen_first(exercises, attempted=None, last_seen=None)`) so `build_session` queries the store at most once per call. Keep the function's existing behavior identical when called without the new args.
  - [ ] Confirm Code-Completion entries get `seen=false` for free (their ids are never in the MCQ-scoped `attempts` table) — do not special-case them, just verify.
  - [ ] Do **not** stamp a truthy `seen` in `build_mock_session` (leave it absent / `False`) so the mock indicator stays hidden. Add a one-line comment stating this is intentional (exam realism).
- [ ] **Task 2 — Document the new entry field (backend)** (AC: 1)
  - [ ] Update the `SessionEntry` shape docstrings in `session.py` (`build_session_entry`, `build_code_completion_entry`, module-level shared-contract comment) and the `GET /api/sessions` docstring in `main.py` (the "Each session entry has the shape" block) to include `"seen": bool`.
- [ ] **Task 3 — Shared `SeenIndicator` component (frontend)** (AC: 5, 6)
  - [ ] Add `frontend/src/components/SeenIndicator.jsx`: renders nothing when `seen` is falsy; otherwise renders a small inline **grey eye SVG** (`text-gray-400`) with `title="You've attempted this exercise before"`, an `aria-label` (or `<span className="sr-only">`) carrying the same text, and `role="img"` on the SVG (or wrap appropriately). Match the metadata-badge sizing used by the sibling badges (`text-xs px-2 py-1`-scale).
  - [ ] No new dependency — use an inline SVG (the codebase has no icon library; it uses inline SVG/emoji + native `title`, e.g. `Timer.jsx`, the `⌨`/`✓` glyphs in `MCQPractice.jsx`).
- [ ] **Task 4 — Wire the indicator into both runners** (AC: 5, 6)
  - [ ] In `frontend/src/pages/MCQPractice.jsx`, render `<SeenIndicator seen={exercise.seen} />` in the metadata header row (the `flex items-center gap-2 shrink-0` block around lines 235–262, next to the domain/difficulty badges, before the Timer/End-session controls).
  - [ ] In `frontend/src/pages/CodeCompletion.jsx`, render the same indicator in its mirrored metadata header (around lines 132–146, next to the domain/difficulty badges).
- [ ] **Task 5 — Tests** (AC: 7, 8, 9)
  - [ ] Backend (`backend/tests/`): extend the session-builder / endpoint tests to assert `seen` is `True` for an attempted MCQ id, `False` for an unattempted one and for Code-Completion, present on both `GET` and `POST /api/sessions` entries, and not truthy on `mode=mock` entries. Use a temp DB (`ATTEMPT_DB_PATH` / `path=` override — see `store.py`) seeded via `store.record_attempt(...)`.
  - [ ] Frontend: add `SeenIndicator.test.jsx` (renders icon + accessible name when `seen`, renders nothing when not). Extend `MCQPractice.test.jsx` (and a Code-Completion runner test if one exists) to assert the eye is present for a seen exercise and absent otherwise, querying by the accessible name / `title`.
- [ ] **Task 6 — Verify** (AC: all)
  - [ ] `cd backend && uv run pytest` green; `uv run ruff check .` clean. (Use **uv**, never pip — project rule.)
  - [ ] `cd frontend && npm test` and the lint script green.

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

### Debug Log References

### Completion Notes List

### File List
