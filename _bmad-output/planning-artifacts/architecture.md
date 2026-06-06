---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-06-05'
lastStep: 8
revisions:
  - date: '2026-06-05'
    summary: 'PRD rev 2 — randomness & variety: Option Pool (FR-19), server-side Displayed-Option sampling + position shuffle (FR-20), randomized session order (FR-21); single-select only (FR-9 removed). Added GET /api/sessions, revised POST /api/feedback contract, session randomizer decision, re-study variety cross-cutting concern.'
  - date: '2026-06-05'
    summary: 'UX QoL pass (EXPERIENCE.md) — closed 3 gaps: G1 GET /api/exercises/count (leak-free Start-screen match count); G2 POST /api/sessions {exerciseIds} for replay (Restart-same / Practice-incorrect, keeps FR-20/21 freshness); G3 frontend feedback-retention + new reducer actions/states (prev, skip, endToSummary, replay) for Back/Review-incorrect/partial-Summary. See ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md.'
  - date: '2026-06-07'
    summary: 'Rev 4 — PRD rev 3 scope expansion (Epics 7 & 8). REVERSED the no-persistence/stateless NFR: added a LOCAL SQLite attempt store (store.py, sqlite3 stdlib, backend/data/progress.db gitignored). POST /api/feedback now records attempts (+timeTakenMs). GET /api/sessions ordering is history-aware unseen-first (FR-24, supersedes FR-21 ordering). New GET /api/stats + GET /api/readiness (FR-23/25). Mock-Exam builder (mode=mock, domain-weighted full-length, exam-scoped, ignores unseen-first; Associate 45Q/90min, Pro 59Q/120min — FR-27). Timer + per-question timing are frontend (FR-26/28). New FE: StatsDashboard, ReadinessIndicator, Timer/Countdown, MockExam.'
inputDocuments:
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/.decision-log.md
workflowType: 'architecture'
project_name: 'DataBricks-DE-cert-study-companion'
user_name: 'Dario'
date: '2026-06-05'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements (28 total; FR-9 removed/tombstoned; FR-22–FR-28 added in PRD rev 3):**

1. **Exercise Content Format & Loading (FR-1 through FR-4, FR-18):** Portable, standardized, human-authorable exercise format (YAML-authored, optionally JSON-served). Runtime file loading from a designated directory. Blueprint-aligned Domain tagging. Anki export support.

2. **Multiple-Choice Practice (FR-5 through FR-12, FR-19 through FR-21):** Exam-realistic MCQ runner — domain/difficulty filtering, single-question-at-a-time view, immediate feedback, per-distractor explanations with doc links, end-of-session summary. **Single-select only** (multi-select removed, PRD rev 2). Each MCQ is an **Option Pool** (≥1 correct, ≥3 incorrect, no upper bound — FR-19); the runner samples **4 Displayed Options** (1 correct + 3 distractors) in **shuffled positions** per presentation (FR-20) and presents Exercises in **randomized order** per session (FR-21). Sampling/shuffle/order randomization are computed **server-side** (correct flags never leave the backend).

3. **Code-Completion "Wordle" Practice (FR-13 through FR-17, Phase 2):** Novel syntax-drilling exercise type with token-level positional feedback (green/yellow/grey). Single-line/fill-in-blank scope. Whitespace-insensitive. Accepts alternative correct answers. Critical design: playfulness and delight are load-bearing, not incidental.

4. **Exercise Generation (FR deferred, Phase future):** Optional in-app generation from Databricks docs; committed path is agent-skill authoring into the standardized format.

5. **Answer & Stats Tracking (FR-22 through FR-25, PRD rev 3 / Epic 7):** Persist attempt history locally (FR-22), a stats dashboard with overall + per-Domain accuracy/trends/weak-areas (FR-23), **unseen-first** session prioritization (FR-24), and a readiness indicator vs the ~70% bar (FR-25). Introduces local persistence (see NFR change below).

6. **Timed Practice / Mock Exam (FR-26 through FR-28, PRD rev 3 / Epic 8):** Optional per-session countdown with auto-end (FR-26), a domain-weighted full-length **Mock-Exam mode** at real exam timing — Associate 45Q/90min, Pro 59Q/120min (FR-27), and per-question timing that feeds the stats (FR-28). Timer/timing are client-side.

**Non-Functional Requirements (Shaping Architecture):**

- **Code-Completion feedback latency: < 100ms from keystroke to rendered feedback.** Target is client-side computation; no perceptible server round-trip. This is the primary driver of the frontend technology choice (React/vanilla JS vs. HTMX).
- **~~Single-user, local, no persistence (MVP).~~ → Single-user, local, with LOCAL persistence (PRD rev 3, 2026-06-07).** No accounts, no auth, no multi-user/server-side user data, no sync. Content stays file-based; the user's own **answer history** is persisted in a **local SQLite store** (`sqlite3` stdlib, no pip). This **reverses the prior no-persistence stance and the stateless-session property** — `GET /api/sessions` and `POST /api/feedback` now read/write that store. See the Persistence decision in Core Architectural Decisions.
- **Content portability (FR-18).** Exercise format must export cleanly to Anki so studying is never gated on app completion. This is the linchpin of the Build-vs-Borrow strategy.
- **Playfulness in Code-Completion.** Wordle-like guess-and-narrow loop is the differentiator; implementation must preserve delight, not reduce it to a correctness check.

**Build-vs-Borrow Decision (Phase 1 Impact):**

- **Borrow/go-lean for MCQ runner.** MCQ practice is table-stakes (every cert tool has it); Anki (via Anki import script) or a deliberately minimal built-in runner are both acceptable for MVP study.
- **Build for novelty.** The Wordle-style code-completion drill is the only piece worth from-scratch investment.
- **Content is primary MVP.** ~50–75 original, blueprint-aligned Associate MCQs + committed agent-skill authoring track. Content velocity beats app polish.

### Technical Constraints & Dependencies

**Content Model:**
- Format: YAML for authoring, optionally JSON internally
- Storage: Files at runtime (no database in MVP)
- Loading: Runtime discovery of Exercise Set files from a designated directory
- Validation: Fail loudly with file/Exercise locators; single-author tolerance (stack trace OK)
- Export: One-shot converter (script) to Anki format; two-way sync out of scope

**Code-Completion Technical Surface:**
- Tokenizer: Language-specific (SQL keywords case-insensitive, PySpark identifiers case-sensitive)
- Feedback algorithm: Token-level green (correct token, correct position) / yellow (correct token, wrong position) / grey (absent)
- Scope: Single-line or single fill-in-the-blank slot; multi-line snippets explicitly out of scope
- Whitespace handling: Non-semantic whitespace ignored; user not penalized for indentation
- Alternatives: Authored "accepted alternatives" set; AST/execution equivalence validation out of scope for MVP

**Platform & Deployment:**
- Single-user local app (no auth, no hosting in v1)
- Content version-controlled (git)
- Future sharing via portable format; not a current constraint

### Cross-Cutting Concerns Identified

**1. Content Portability**
- Drives the whole Build-vs-Borrow strategy. Anki export path is critical for v1 studying.
- Architectural implication: Content schema must be clean enough for scripted conversion; no app-specific metadata or database relationships.

**2. Playfulness & Delight (Code-Completion)**
- Wordle-like feel is intentional UX differentiation, not a gimmick.
- Architectural implication: Feedback must render instantly, visual design must preserve the game-like loop (attempt → colored feedback → refine), not reduce it to correctness.

**3. Frontend Latency Boundary**
- < 100ms code feedback targets client-side computation only.
- Architectural implication: Frontend technology must support responsive keystroke-to-render. HTMX's server-round-trip model is risky; React (or vanilla JS with client state) is safer.

**4. Format Extensibility**
- Proposed schema supports 8 future exercise types (output prediction, spot-the-bug, ordering, match definitions, config fill-in, scenario MCQs, rapid-fire true/false, flashcards).
- Architectural implication: Shared fields (`id`, `domain`, `difficulty`, `explanation`, `exam`, `source`, `tags`) allow future types to reuse the session/filtering/analytics layer without refactoring the loader.

**5. Content as the Bottleneck**
- Not app beauty; time-to-passing-exam is the real constraint.
- Architectural implication: Minimize app complexity, maximize content authoring velocity. Prefer borrowing table-stakes features (MCQ runner) to building them.

**6. Re-study Variety / Freshness (Randomness)**
- An MCQ should feel new on the 2nd/3rd view rather than memorized-by-position. Driven by the Option Pool (≥1 correct, ≥3 incorrect, no upper bound) plus per-presentation sampling/shuffle (FR-20) and per-session question-order randomization (FR-21).
- Architectural implication: the runner is **stateless and non-deterministic per request** — sampling and ordering happen **server-side** at session-build / presentation time, with no anti-repeat memory in MVP (uniform-at-random). The full pool and `correct` flags stay on the backend; the client only ever receives 4 flag-less Displayed Options, so it cannot pre-compute the answer. This concern only touches the MCQ runner and its API contract; the content schema (FR-19) and validation absorb the rest.

### Scale & Complexity Assessment

**Project Complexity: Medium (but timeline-constrained)**

- Real-time features: Yes (Code-Completion < 100ms feedback)
- Multi-tenancy: No (single-user)
- Regulatory compliance: No
- Integration complexity: Minimal (Anki export script, Databricks doc links)
- User interaction complexity: Low-to-Medium (filtered practice sessions, simple form-like MCQ, typing-based code exercises)
- Data complexity & volume: Very low (~50–75 exercises at launch, flat file-based)

**Estimated Architectural Components:**
- Content loader (file → parsed exercises in memory)
- Exercise filtering/session builder (domain, difficulty, type) + **session randomizer** (option-pool sampling, option-position shuffle, exercise-order randomization — server-side)
- MCQ renderer & input handler (**single-select only**; renders 4 server-supplied Displayed Options)
- Code-Completion renderer, tokenizer, feedback engine
- Anki export converter (separate utility script)
- (Optional) Lean session runner UI
- (Phase 2) Code-Completion tokenizer & feedback rendering

**Primary Technical Domain:** Single-user study tool with client-side interactivity (not API, not distributed system)

---

## Starter Template Evaluation

### Primary Technology Domain

Single-user, local study app with client-side interactivity and real-time feedback. Not a distributed system; not an API-first product. Desktop/web app optimized for a single learner.

### Technology Stack Selection

**Frontend Decision: React (via Vite)**

**Rationale:**
- Code-Completion feedback target (< 100ms) requires client-side computation (tokenizer, feedback rendering). React's component state and event handling are well-suited for keystroke-level reactivity.
- Rich interactivity without server round-trips. Keystroke → tokenize → render feedback must happen in-browser.
- Vite provides a lightweight, fast dev server and minimal build overhead (vs. Next.js, which adds unnecessary SSR complexity for a local app).
- Ecosystem support for code rendering, syntax highlighting, interactive forms.

**Rejected Alternative:** HTMX
- Server-round-trip model conflicts with < 100ms keystroke feedback latency.
- Would require JS sprinkles anyway, defeating HTMX's philosophy.
- Not the right fit for client-heavy, real-time interactions.

**Backend Decision: Python + FastAPI**

**Rationale:**
- Minimal, async-ready framework for file loading, content parsing, and export operations.
- Lower friction for parallel content-authoring agent-skill workstream (Python ecosystem, easy to test, easy to extend).
- File-based content (no database in MVP) aligns with Python's strength in data manipulation and format conversion.
- FastAPI's async support handles multiple file types and future generation features cleanly.
- Single-user, local deployment means no complex ops or scaling concerns.

**Rejected Alternative:** Rust
- Higher upfront learning curve; doesn't solve the bottleneck (content authoring + exam prep).
- Lean binary is a nice-to-have, not a must-have for a local tool.
- Python's faster iteration better serves the timeline.

### Starter Template Approach

**Decision: Hand-Rolled, No Monolithic Scaffold**

**Rationale:**
- Project scope is simple enough that hand-rolling minimal scaffolds is faster than integrating a heavy starter.
- Your specific tech stack (Vite + React for frontend, FastAPI for backend, YAML content loading) is not a standard pairing in existing starters.
- Custom scaffold gives you clarity and avoids technical debt from unused boilerplate.

**Suggested File Structure:**

```
project-root/
├── exercises/               # PRIMARY DELIVERABLE
│   ├── associate/          # Domain-organized subdirectories
│   │   ├── lakehouse.yaml
│   │   ├── elt-sql-python.yaml
│   │   ├── incremental-processing.yaml
│   │   ├── production-pipelines.yaml
│   │   └── data-governance.yaml
│   └── professional/       # (Phase 2, when Professional cert exercises added)
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── content.py       # Content loading, parsing, filtering
│   │   ├── models.py        # Exercise, Session data models
│   │   └── export.py        # Anki export logic
│   ├── requirements.txt      # Python dependencies (managed via uv)
│   └── pyproject.toml        # (optional, for uv)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── SessionSelect.jsx
│   │   │   ├── MCQPractice.jsx
│   │   │   └── CodeCompletion.jsx (Phase 2)
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   ├── vite.config.js
│   ├── package.json
│   └── index.html
└── docs/
    ├── exercise-format.md   # YAML schema documentation
    └── architecture.md      # (this file)
```

**Rationale for `exercises/` at root:** Content is the primary MVP deliverable. Peer-level placement (same hierarchy as frontend/ and backend/) visually reinforces that the content bank is the durable product; the app shell is the delivery mechanism.

### Architectural Decisions Established by This Choice

**Language & Runtime:**
- Frontend: JavaScript/JSX (React), browser runtime
- Backend: Python 3.10+, async runtime (FastAPI)
- Content: YAML (authored), optionally JSON (served internally)

**Build & Development:**
- Frontend: Vite (dev server, bundler)
- Backend: FastAPI dev server (`uvicorn`)
- Python package manager: `uv` (per PRD preference)

**Code Organization:**
- Frontend: Component-based structure (pages, components, hooks, utils)
- Backend: API route structure (content loading, filtering, feedback, export endpoints)
- Content: YAML files organized by domain, loaded at startup, held in memory

**API Surface (Backend → Frontend):**
- REST endpoints for:
  - `GET /sessions` — create Practice Session (filters by domain, difficulty, type)
  - `GET /exercises/{id}` — retrieve single Exercise data (MCQ or Code-Completion template)
  - `POST /feedback` — submit answer, receive correctness feedback
  - `GET /export/anki` — export MCQs to Anki format (script or endpoint)

**Testing & Quality:**
- Frontend: Vitest or Jest (TBD during implementation stories)
- Backend: pytest with async support
- Linting: ESLint (frontend), ruff (backend)

**Development Experience:**
- Frontend: Hot module reload via Vite (near-instant feedback during dev)
- Backend: Auto-reload via `uvicorn --reload`
- No containerization for MVP (local development only)

### Deployment & Packaging (MVP Out of Scope)

For v1 (exam deadline), deployment is "run locally":
- Backend: `python -m uvicorn app.main:app --reload` (or via `uv run`)
- Frontend: `npm run dev` (Vite dev server)
- Both run on `localhost`; frontend proxies API calls to backend

Future packaging (Phase 2+): Consider Tauri or Electron wrapper if distributing to peers.

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):** All made (starter, tech stack, file structure).

**Important Decisions (Shape Architecture):**
- Frontend state management approach
- Code-Completion tokenizer strategy
- Error handling format
- Content validation approach

**Deferred Decisions (Post-MVP):**
- Persistence / session history (Phase 2+)
- Multi-user / hosting (Phase 2+)
- In-app content generation (deferred)
- Deployment packaging (Tauri/Electron)

### Frontend Architecture

**Decision: State Management**

**Choice:** React Context + React hooks (`useState`, `useEffect`) for session and exercise state.

**Rationale:**
- Session scope is simple: current Exercise, selected answers, feedback rendered.
- No time-travel debugging, undo/redo, or complex derived state needed.
- Avoids external state library overhead; Context gives us enough structure.
- Easier to test (no store abstraction layer).
- Lower friction for solo builder.

**Affected Components:**
- SessionSelect page → filters, creates session → sends to MCQ/CodeCompletion page
- MCQPractice page → holds current exercise, selections, feedback state
- CodeCompletion page (Phase 2) → holds attempt, feedback, attempt count
- Session wrapper → provides session context (exercises list, user progress)

**QoL additions (UX rev — EXPERIENCE.md):** the session reducer expands to support the quality-of-life behaviors:
- **Feedback retention (G3):** with grading server-side and `correct` flags stripped, the client must persist each `POST /api/feedback` response in `feedback[exerciseId]` as `{ correct, correctOptionId, explanation, references }`. This powers **Back/Previous read-only revisit** and the **Review-incorrect** list with no re-grade; revisiting a submitted question must **not** re-POST (answers are final).
- **New actions:** `prev` (decrement index; revisit read-only), `skip` (advance without grading; records the question as *unanswered*, not incorrect), `endToSummary` (exit Practice early → Summary over the answered subset), and an `exit`/`reset` to Start (existing `reset`). Replay actions `restartSession` / `practiceIncorrect(ids)` call `POST /api/sessions {exerciseIds}` for a fresh-sampled set.
- **Per-question state:** `unanswered | answered | skipped`, plus a furthest-reached pointer so Back/Next can't overrun; session-level `active | ended-early | completed`.
- **Partial Summary:** `computeResults` already scores only answered exercises, so the early-exit Summary needs no backend change; it surfaces answered/skipped counts.
- **New behavioral components:** progress bar (position + running correct count), persistent End-session control, Exit-confirm modal (focus-trapped), Review-incorrect list. Visual tokens inherited from DESIGN.md.

---

**Decision: Syntax Highlighting & Code Display**

**Choice:** Prism.js for syntax highlighting in exercise display and code feedback.

**Rationale:**
- Lightweight (~7KB gzipped)
- Wide language support (SQL, Python, etc.)
- No runtime compilation; fast rendering
- Easy to theme (green/yellow/grey tokens for feedback)
- Can be tree-shaken if unused languages are removed

**Installation:** `npm install prismjs`

**Affected Components:**
- MCQPractice: code snippets in questions
- CodeCompletion: template display, feedback rendering, canonical answer reveal

---

**Decision: Code-Completion Tokenizer**

**Choice:** Regex-based tokenizer (language-specific patterns) for MVP feedback.

**Rationale:**
- Target < 100ms feedback latency requires fast computation.
- No need for a full parser; tokens are sufficient (keywords, identifiers, operators, literals).
- Language-specific patterns (SQL vs. PySpark) can be simple regexes.
- If tokenization becomes a bottleneck, replace with a proper lexer later.

**Implementation Sketch:**
- `tokenize(code, language)` → array of `{token, type, position}`
- `computeFeedback(attempt, canonical, language)` → array of token colors (green/yellow/grey)
- Uses case-sensitivity rules per language (SQL keywords case-insensitive, PySpark identifiers case-sensitive)

**Example (SQL):**
```javascript
// Pseudocode
const sqlTokenPattern = /(\bSELECT\b|\bFROM\b|[a-zA-Z_]\w*|'[^']*'|\d+|[(),.;])/gi;
const tokens = code.match(sqlTokenPattern);
```

---

### API & Communication Patterns

**Decision: REST API Format**

**Choice:** Simple REST endpoints, JSON request/response, standard HTTP status codes.

**Endpoints (Backend):**
- `GET /api/sessions` → **build a Practice Session** (filters: domain, difficulty, type). Returns Exercises in **randomized order** (FR-21), each MCQ carrying its **4 sampled, shuffled Displayed Options without `correct` flags** (FR-20). This is the primary MCQ-runner entry point; the randomness lives here.
  - Response `data`: `[{ exerciseId, domain, difficulty, question, codeContext?, displayedOptions: [{ id, text } × 4] }, ...]`
- `POST /api/sessions` → **build a session from an explicit exercise-id set** (UX "Restart same session" / "Practice these N again" — EXPERIENCE.md). Request: `{ exerciseIds: [...] }`. Same response shape as `GET /api/sessions`, with **freshly sampled + shuffled Displayed Options and re-randomized order** so replays keep FR-20/21 freshness (the client cannot re-sample — it holds only flag-less options). Unknown ids are dropped (logged), not fatal.
- `GET /api/exercises/count` → **lightweight match count** for the Start screen "{n} questions match" (filters: domain, difficulty, type). Response `data`: `{ count }`. Returns **no pools/options/flags** — so the practice client never receives `correct` flags (preserves the FR-20 non-leakage rule that `GET /api/exercises` would violate).
- `GET /api/exercises` → list/inspect exercises (admin/debug, filters). Note: this returns authored exercises incl. pools/flags; the **runner uses `/api/sessions` + `/api/exercises/count`**, never this, so pools/correct flags aren't shipped to the practice UI.
- `POST /api/feedback` → submit answer, get correctness + explanation
  - Request (MCQ): `{ exerciseId, displayedOptionIds: [...], selectedId, type: "mcq" }` — `displayedOptionIds` echoes the 4 shown so the backend scores against exactly what the user saw
  - Request (Code-Completion, Phase 2): `{ exerciseId, attempt, type: "code-completion" }`
  - Response: `{ correct: bool, correctOptionId, explanation: string, references: [...] }`
- `GET /api/export/anki` → trigger Anki export (returns download or JSON). Note: export flattens each pool to one correct + distractors; runner-only sampling/shuffle/order (FR-20/21) do not apply to the export.

**Response Format (Standard):**
```json
{
  "success": true,
  "data": { /* ... */ },
  "error": null
}
```

or on error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "EXERCISE_NOT_FOUND",
    "message": "Exercise ID dbx-de-0142 not found"
  }
}
```

---

**Decision: Error Handling**

**Choice:** Descriptive HTTP status codes + machine-readable error codes in JSON.

**Error Response Example:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Option Pool invalid for single_choice exercise: needs >=1 correct and >=3 incorrect options, found 1 correct / 2 incorrect.",
    "details": {
      "file": "exercises/associate/incremental-processing.yaml",
      "exerciseId": "dbx-de-0142"
    }
  }
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad request (malformed input)
- 404: Exercise not found
- 500: Server error (e.g., file load failure)

---

### Data Architecture

**Decision: Content Loading & Caching**

**Choice:** Load all YAML exercises into memory at startup; cache for session.

**Rationale:**
- File-based (~50–75 exercises at MVP = small in-memory footprint)
- No database queries during practice sessions (fast)
- Single-user, no concurrent writes to exercises
- Session filtering is in-memory joins

**Backend Implementation:**
- At startup: Scan `exercises/` directory, parse all YAML files into an Exercise[] in memory
- On `GET /api/exercises`, filter this list and return
- No re-loading between requests (session-scoped cache)

**Caching Strategy:**
- Restart app to pick up new exercise files (acceptable for solo builder)
- Future (Phase 2): Hot-reload or file-watch for live updates

---

**Decision: Content Validation**

**Choice:** Fail fast with descriptive error; no partial loads. Single-author tolerance.

**Rationale:**
- You are the single author; stack traces are acceptable error reporting.
- If a YAML file is malformed, failure is better than silent drops.
- Error message should name the file and ideally the Exercise `id` and field.

**Backend Validation:**
- Parse YAML → validate against schema (id, domain, type, required fields)
- **Option Pool rule (FR-19):** every MCQ (`single_choice`) must have **≥1 correct and ≥3 incorrect** options; otherwise it can't yield a 1-correct + 3-distractor display. Multiple `correct: true` options are allowed and treated as **interchangeable alternatives** (the Pydantic validator's old "single_choice ⇒ exactly one correct" rule is relaxed accordingly). The removed `multi_choice` type is rejected.
- If any Exercise is invalid, log error with file + id + what's wrong, skip that Exercise
- If entire file fails to parse, raise error (halt startup? or skip file with warning?)

**Decision sub-choice:** On file parse failure → **skip file with warning** (allows partial launch; easier dev iteration). On Exercise schema failure → **skip Exercise with error log** (don't crash entire content load for one bad question).

---

**Decision: MCQ Session Randomizer (Option Pool sampling, shuffle, order)**

**Choice:** A server-side session randomizer, invoked when `GET /api/sessions` builds a session. It is stateless and non-deterministic per request.

**Responsibilities:**
- **Exercise-order (FR-21 → FR-24, rev 4):** ordering is now **history-aware (unseen-first)** — unanswered Exercises before seen ones (within the active filters), seen fallback ordered least-recently-seen; randomize *within* the unseen group. Option sampling/shuffle stay random. (Mock-Exam mode ignores unseen-first — see below.)
- **Displayed-Option sampling (FR-20):** for each MCQ, sample **1** correct option from the pool's correct set and **3** incorrect options from the pool's incorrect set (uniform-at-random, no anti-repeat memory).
- **Option-position shuffle (FR-20):** randomize the slot order of the 4 Displayed Options so the correct answer isn't position-stable.
- **Answer non-leakage:** strip `correct` flags; the response carries only `{ id, text }` per Displayed Option.

**Rationale:**
- Coheres with the existing pattern: correctness is already evaluated server-side via `POST /api/feedback`. Keeping sampling server-side means the full pool and correct flags never reach the browser, so the client cannot pre-compute the answer (the failure mode of a client-side tier).
- ~~Stateless RNG per request gives freshness for free with no persistence.~~ **(rev 4)** Sampling/shuffle remain stateless RNG; **ordering** now reads the attempt store (unseen-first). The randomizer is no longer fully stateless.

**Scoring contract:** `POST /api/feedback` receives `displayedOptionIds` + `selectedId` (+ optional `timeTakenMs`, rev 4) and scores against exactly the 4 options the user saw (single-select: correct iff `selectedId` is the displayed correct option). The former multi-select all-or-nothing path (old FR-9) is removed.

**Implementation note:** lives in `content.py` / `session.py` alongside filtering; `feedback.py` owns scoring. RNG is standard-library.

---

**Decision: Local Persistence — SQLite attempt store (rev 4, FR-22)**

**Choice:** A **local SQLite** database (`sqlite3`, Python stdlib — **no pip dependency**), created-if-absent at startup, holding the single user's answer history. This **reverses the prior no-persistence / stateless-session NFR**; single-user/local is retained (no accounts, no server, no sync).

**Why SQLite over a JSON file:** attempt-level history + the queries the stats/readiness/unseen-first features need (and the still-deferred SRS) are natural in SQL and trivial at this scale; stdlib means zero new dependency. JSON was the considered, rejected alternative (addendum §E).

**Schema (indicative):** `attempts(id INTEGER PK, exercise_id TEXT, exam TEXT, domain TEXT, correct INTEGER, selected_id TEXT, time_taken_ms INTEGER, answered_at TEXT)`. Stats are aggregations over it; "seen" = a row exists for `exercise_id`.
- **Location:** gitignored local file, e.g. `backend/data/progress.db` (add `backend/data/` to `.gitignore`).
- **Module:** new `backend/app/store.py` — `record_attempt(...)`, `attempted_ids(filters)`, `domain_accuracy()`, `overall_stats()`, `last_seen_map()`; opens a connection per request (or a module-level connection with `check_same_thread=False`). Create-table-if-not-exists on startup (lifespan).

**Write hook:** `POST /api/feedback` (already grades server-side) calls `store.record_attempt(...)` with exercise id, exam, domain, correctness, selected id, and the client-supplied `timeTakenMs` (FR-28). Recording failures must not break grading (best-effort write, logged).

**Read paths:** `GET /api/sessions` consults `store.attempted_ids` for unseen-first (FR-24); new `GET /api/stats` (FR-23) and `GET /api/readiness` (FR-25) aggregate the store.

---

**Decision: Stats & Readiness endpoints (rev 4, FR-23/FR-25)**

**Choice:** Read-only endpoints over the attempt store, standard `{success, data, error}` wrapper.
- `GET /api/stats` → overall accuracy + attempts, per-Domain accuracy/attempts, and a trend series (e.g. by day). Optional `exam` filter.
- `GET /api/readiness` → rolling-window accuracy vs the **~70%** planning heuristic, overall + per-Domain readiness flags. (~70% is guidance, not an official cut — addendum §C.)

**Frontend:** a `StatsDashboard` page/section + a `ReadinessIndicator` component (DESIGN.md tokens; weak domains visually distinct).

---

**Decision: Mock-Exam session builder (rev 4, FR-27)**

**Choice:** A builder variant (e.g. `GET /api/sessions?mode=mock&exam=...`, or a dedicated `GET /api/mock-exam`) that assembles a **domain-weighted, full-length** set scoped to one Exam — Associate ≈45Q/90min, Professional ≈59Q/120min, per the §C weights — and stamps the exam **duration** in the response. It **ignores unseen-first** (a mock must be representative, not unseen-biased) and may repeat seen questions. Exam-style scoring reuses the §4.5 per-Domain breakdown at the end.

**Timer is frontend (FR-26/FR-28):** the countdown, auto-submit-at-zero, and per-question elapsed timing live in React; the client sends `timeTakenMs` with each `POST /api/feedback`. No server-side timer/clock. New frontend: a `Timer`/`Countdown` component (used by both the optional session timer and Mock-Exam mode) and a `MockExam` flow/page; SessionSelect gains a "timed?" / "mock exam" affordance.

---

### Infrastructure & Deployment

**Decision: Development Server Setup**

**Choice:** Two concurrent dev servers (frontend on 3000, backend on 8000) with frontend proxy to backend.

**Frontend (Vite):**
- `npm run dev` → starts on `localhost:3000`
- Vite config proxies `/api/*` to `localhost:8000`

**Backend (FastAPI):**
- `python -m uvicorn app.main:app --reload` (or `uv run uvicorn ...`)
- Runs on `localhost:8000`
- Auto-reload on source changes

**Start-up Script (future):**
```bash
# Run both in parallel (e.g. via Makefile or shell script)
uvicorn app.main:app --reload &
npm run dev
```

---

**Decision: Build & Export Artifacts**

**Choice:** Frontend builds to `dist/` (Vite default); Anki export is a standalone Python script.

**Frontend Build:**
- `npm run build` → outputs to `frontend/dist/`
- Includes all assets, optimized bundle

**Anki Export (Python Script):**
- Standalone script: `backend/scripts/export_anki.py`
- Reads exercises from memory or directly from YAML files
- Outputs `.apkg` (Anki deck package) or JSON format
- Can be run independently of the app

---

### Decision Impact Analysis

**Implementation Sequence:**
1. Backend: Content loader (YAML parsing, in-memory cache, validation)
2. Backend: API endpoints (exercises list, single exercise, feedback logic)
3. Frontend: SessionSelect page (filter UI, session creation)
4. Frontend: MCQPractice page (exercise display, answer selection, feedback)
5. Backend: Anki export script
6. Frontend: CodeCompletion page (Phase 2)
7. Packaging & deployment (Phase 2+)

**Cross-Component Dependencies:**
- Frontend pages depend on Backend API contracts (endpoint shapes, response format)
- Feedback logic (correctness evaluation) is Backend; feedback rendering is Frontend
- Content validation happens in Backend; Frontend consumes validated exercises
- Export script is independent; can be tested separately from app

---

## Implementation Patterns & Consistency Rules

To prevent conflicts between AI agents implementing different components, these patterns are **mandatory for all code**:

### Naming Patterns

**React Components:**
- **Format:** PascalCase file names and component names
- **Examples:** `MCQPractice.jsx`, `CodeCompletion.jsx`, `SessionSelect.jsx`
- **Non-Examples:** ❌ `mcqPractice.jsx`, ❌ `mcq-practice.jsx`

**Functions & Variables:**
- **Format:** camelCase
- **Examples:** `getSessionExercises()`, `isLoadingFeedback`, `handleAnswerSubmit()`
- **Non-Examples:** ❌ `get_session_exercises()`, ❌ `is_loading_feedback`

**API Endpoints:**
- **Format:** Plural nouns, lowercase, hyphens for multi-word
- **Examples:** `/api/exercises`, `/api/feedback`, `/api/session-history` (future)
- **Non-Examples:** ❌ `/api/exercise`, ❌ `/api/Exercises`, ❌ `/api/get-exercises`

**JSON Fields (API & Frontend State):**
- **Format:** camelCase
- **Examples:** `{ exerciseId, exerciseDomain, isCorrect, selectedAnswers }`
- **Backend conversion:** Backend converts `exercise_id` (internal) ↔ `exerciseId` (JSON)
- **Non-Examples:** ❌ `{ exercise_id, exercise_domain, is_correct }`

**State Variables (React):**
- **Format:** `is{Name}`, `has{Name}`, `{collection}List` for loading/boolean/collection states
- **Examples:** `isLoading`, `hasError`, `isFeedbackShown`, `exercisesList`
- **Non-Examples:** ❌ `loading`, ❌ `feedback_shown`, ❌ `exercises`

### Structure Patterns

**Frontend Organization:**
```
frontend/src/
├── pages/
│   ├── SessionSelect.jsx       # Choose domain/difficulty
│   ├── MCQPractice.jsx         # Single MCQ view + feedback
│   └── CodeCompletion.jsx      # (Phase 2) Wordle-style exercise
├── components/
│   ├── ExerciseDisplay.jsx     # Shared; renders MCQ or code
│   ├── Feedback.jsx            # Correctness + explanation
│   └── FeedbackTokens.jsx      # (Phase 2) Green/yellow/grey coloring
├── hooks/
│   ├── useSession.js           # Session context consumer
│   └── useExerciseFeedback.js  # Feedback computation
├── utils/
│   ├── api.js                  # API call wrappers
│   └── formatters.js           # Format helpers
└── context/
    └── SessionContext.jsx      # Session state provider
```

**Backend Organization:**
```
backend/
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── content.py              # Exercise loading, filtering, parsing
│   ├── models.py               # Pydantic models (Exercise, Session, etc.)
│   ├── feedback.py             # Correctness evaluation logic
│   └── export.py               # Anki export functions
├── scripts/
│   └── export_anki.py          # Standalone Anki export script
├── exercises/                  # (Actually at project root; symlink or copy here for imports?)
└── requirements.txt            # Dependencies
```

**Tests:**
- **Co-located:** `ComponentName.test.jsx` in same directory as component
- **Backend:** `test_content.py` alongside `content.py`
- **Run:** `npm test` (frontend) and `pytest` (backend)

### Format Patterns

**API Response Wrapper (All Endpoints):**
```json
{
  "success": true,
  "data": { /* endpoint-specific payload */ },
  "error": null
}
```

**API Error Response:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "EXERCISE_NOT_FOUND",
    "message": "Exercise ID dbx-de-0142 not found in domain Incremental Data Processing",
    "details": {
      "exerciseId": "dbx-de-0142",
      "domain": "Incremental Data Processing"
    }
  }
}
```

**Date & Time Format:**
- **Timestamps:** ISO 8601 strings in JSON (e.g., `"2026-06-05T14:30:00Z"`)
- **Display:** Locale-specific in UI (leave to browser/Intl API)

**Boolean Representations:**
- **Always:** `true` / `false` (not `1` / `0`)

### Communication Patterns

**State Management (React Context):**
- **SessionContext:** Holds `exercises[]`, `currentExerciseIndex`, `selectedAnswers`, `feedback`
- **Updates:** Use `useReducer` for complex orchestration OR separate `useState` for simple pieces
- **Pattern:** All state updates are immutable (don't mutate arrays/objects directly)

**Example (Simple useState):**
```javascript
const [currentIndex, setCurrentIndex] = useState(0);
const [selectedAnswers, setSelectedAnswers] = useState({}); // {exerciseId: answer}
const [feedback, setFeedback] = useState(null);
```

**Loading State Pattern:**
```javascript
const [isLoading, setIsLoading] = useState(false);
const [isSubmitted, setIsSubmitted] = useState(false);

// Usage:
if (isLoading) return <Spinner />;
if (isSubmitted && feedback) return <Feedback data={feedback} />;
```

### Error Handling Patterns

**Backend Error Codes (Standard Set):**
- `EXERCISE_NOT_FOUND` — 404
- `VALIDATION_ERROR` — 400
- `INTERNAL_SERVER_ERROR` — 500
- `MALFORMED_YAML` — 400 (file parse failure)

**Frontend Error Handling:**
- Catch API errors, set `hasError` state
- Display user-friendly message (from API `message` field)
- Log full error details (for debugging)

**User-Facing Error Messages:**
- **Good:** "We couldn't find that question. Please try refreshing the page."
- **Bad:** ❌ "ExerciseNotFoundError", ❌ "500 Internal Server Error"

### Code Examples

**Good Pattern (Frontend):**
```javascript
// ✅ React component with clear state management
export function MCQPractice() {
  const { exercises, currentIndex, feedback } = useContext(SessionContext);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitAnswer = async () => {
    setIsSubmitting(true);
    const result = await api.submitAnswer(exercises[currentIndex].id, selectedAnswer);
    setFeedback(result.feedback);
    setIsSubmitting(false);
  };

  if (isSubmitting) return <Spinner />;
  return <ExerciseDisplay exercise={exercises[currentIndex]} onSubmit={handleSubmitAnswer} />;
}
```

**Good Pattern (Backend):**
```python
# ✅ FastAPI endpoint with standard response wrapper
@app.get("/api/exercises")
async def get_exercises(domain: str = None, difficulty: str = None):
    try:
        exercises = content.filter_exercises(domain=domain, difficulty=difficulty)
        return {"success": True, "data": exercises, "error": None}
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "error": {"code": "VALIDATION_ERROR", "message": str(e)}
        }
```

**Anti-Pattern (Frontend):**
```javascript
// ❌ Inconsistent naming, mixing state styles
export function mcq_practice() {
  const [feedback_shown, setFeedbackShown] = useState(false);
  const [answer_data, set_answer_data] = useState({});

  // ❌ Naming inconsistency; unclear if exercise is singular or list
  const [exercise, setExercise] = useState();
}
```

**Anti-Pattern (Backend):**
```python
# ❌ Inconsistent response format
@app.get("/exercises")
def get_exercises():
    return content.exercises  # Direct return; inconsistent with error case

# vs

@app.get("/feedback")
def post_feedback():
    return {"error": "..."}  # Different format
```

### Enforcement Guidelines

**All AI Agents MUST:**
1. Use the exact response wrapper format for all API endpoints
2. Follow camelCase for JSON fields and JavaScript variables
3. Use PascalCase for React component files
4. Organize files in the specified directory structure
5. Co-locate tests with source files (`.test.jsx`, `.test.py`)
6. Use `is{Name}`, `has{Name}` for boolean/loading state
7. Throw/catch errors with the standard error code + message format

**Pattern Verification:**
- Linting: ESLint (frontend), ruff (backend) to enforce naming
- Code review: Check response formats, state naming, file organization
- Tests: Verify API response structure includes `success`, `data`, `error` keys

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
project-root/
│
├── exercises/                              # PRIMARY DELIVERABLE (content bank)
│   ├── associate/
│   │   ├── databricks-lakehouse.yaml
│   │   ├── elt-sql-python.yaml
│   │   ├── incremental-processing.yaml
│   │   ├── production-pipelines.yaml
│   │   └── data-governance.yaml
│   └── professional/                       # (Phase 2)
│
├── frontend/                               # React + Vite frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .eslintrc.cjs
│   ├── src/
│   │   ├── main.jsx                       # Entry point
│   │   ├── App.jsx                        # App wrapper, routing
│   │   ├── pages/
│   │   │   ├── SessionSelect.jsx          # Domain/difficulty filter + session creation
│   │   │   ├── SessionSelect.test.jsx
│   │   │   ├── MCQPractice.jsx            # Single MCQ view + feedback (FR-5–12)
│   │   │   ├── MCQPractice.test.jsx
│   │   │   ├── CodeCompletion.jsx         # Wordle-style exercise (Phase 2, FR-13–17)
│   │   │   └── CodeCompletion.test.jsx
│   │   ├── components/
│   │   │   ├── ExerciseDisplay.jsx        # Shared; renders MCQ question + code
│   │   │   ├── ExerciseDisplay.test.jsx
│   │   │   ├── Feedback.jsx               # Correctness + explanation + doc link
│   │   │   ├── Feedback.test.jsx
│   │   │   ├── FeedbackTokens.jsx         # (Phase 2) Green/yellow/grey token coloring
│   │   │   ├── Spinner.jsx                # Loading indicator
│   │   │   └── SessionSummary.jsx         # End-of-session score + domain breakdown
│   │   ├── hooks/
│   │   │   ├── useSession.js              # Session context consumer hook
│   │   │   ├── useExerciseFeedback.js     # Feedback computation (calls backend)
│   │   │   └── useFetch.js                # Generic fetch + error handling
│   │   ├── context/
│   │   │   ├── SessionContext.jsx         # Provides {exercises, currentIndex, selectedAnswers, feedback}
│   │   │   └── SessionContext.test.jsx
│   │   ├── utils/
│   │   │   ├── api.js                     # API call wrappers (getExercises, submitFeedback, exportAnki)
│   │   │   ├── api.test.js
│   │   │   ├── formatters.js              # Format helpers (e.g., explanation rendering)
│   │   │   └── tokenizer.js               # (Phase 2) Code tokenization for Wordle feedback
│   │   ├── styles/
│   │   │   └── global.css                 # Global styles
│   │   └── assets/
│   │       └── (images, icons if any)
│   └── dist/                              # Build output (generated)
│
├── backend/                                # Python + FastAPI backend
│   ├── main.py                            # Entry point (for direct run)
│   ├── requirements.txt                   # Python dependencies
│   ├── pyproject.toml                     # (optional, for uv)
│   ├── app/
│   │   ├── main.py                        # FastAPI app initialization (FR-5–12)
│   │   ├── content.py                     # Load YAML, parse, filter Exercises (FR-1–4)
│   │   ├── content.test.py
│   │   ├── models.py                      # Pydantic models (Exercise, Session, Feedback)
│   │   ├── models.test.py
│   │   ├── feedback.py                    # Correctness evaluation logic (MCQ + Code-Completion)
│   │   ├── feedback.test.py
│   │   ├── export.py                      # Anki export functions (FR-18)
│   │   └── export.test.py
│   ├── scripts/
│   │   ├── export_anki.py                 # Standalone Anki export script (FR-18)
│   │   └── export_anki.test.py
│   └── __pycache__/                       # (generated)
│
├── docs/
│   ├── architecture.md                    # (this file)
│   └── exercise-format.md                 # YAML schema documentation + examples
│
├── .gitignore
├── .env.example
├── README.md                              # Project overview, setup instructions
└── (git tracking files)
```

### Architectural Boundaries

**API Boundaries:**
- `GET /api/sessions` → Builds a Practice Session: filtered (FR-5), **unseen-first ordered** (FR-24, rev 4 — was order-randomized FR-21) Exercises, each MCQ carrying **4 sampled + shuffled, flag-less Displayed Options** (FR-20). Accepts `exam` (FR-7.x). Optional `mode=mock` → Mock-Exam builder (FR-27: domain-weighted, full-length, exam-scoped, ignores unseen-first, returns the exam `durationMinutes`). Primary runner entry point.
- `POST /api/sessions` → Builds a session from an explicit `exerciseIds[]` (UX replay); freshly sampled/shuffled.
- `GET /api/exercises/count` → Match count `{count}` for the Start-screen filter preview; leak-free. Accepts `exam`.
- `GET /api/exercises` → Inspect/list authored exercises (admin/debug); not used by the practice UI.
- `POST /api/feedback` → MCQ answer submission `{exerciseId, displayedOptionIds, selectedId, timeTakenMs?}`; returns `{correct, correctOptionId, explanation, references}` (FR-8, FR-10). Single-select scoring. **(rev 4)** also **records the attempt** to the SQLite store (FR-22/FR-28) — best-effort, never blocks grading.
- `GET /api/stats` → **(rev 4, FR-23)** overall + per-Domain accuracy/attempts + trend, over the attempt store. Optional `exam`.
- `GET /api/readiness` → **(rev 4, FR-25)** rolling-window accuracy vs ~70%, overall + per-Domain readiness.
- `POST /api/feedback/code-completion` → (Phase 2) Code submission + token-level feedback (FR-14)
- `GET /api/export/anki` → Anki export (FR-18)

**Component Boundaries:**
- **SessionSelect** (Frontend) → User selects domain/difficulty → calls `GET /api/sessions?domain=...&difficulty=...` → receives order-randomized exercises with pre-sampled, shuffled Displayed Options → routes to MCQPractice
- **MCQPractice** (Frontend) → Holds current Exercise from SessionContext → renders the 4 Displayed Options as single-select (radio) → user selects one → calls `POST /api/feedback` with `displayedOptionIds` + `selectedId` → renders Feedback component. No client-side sampling/shuffle — the backend already did it.
- **CodeCompletion** (Frontend, Phase 2) → Tokenizes user input → calls `POST /api/feedback/code-completion` on keystroke → renders green/yellow/grey feedback
- **SessionContext** (Frontend) → Global session state; shared across pages
- **content.py** (Backend) → Sole authority on Exercise loading, parsing, filtering; all API routes call it
- **feedback.py** (Backend) → Sole authority on correctness evaluation; MCQ and Code-Completion variants
- **export.py** (Backend) → Standalone; no app dependencies; can be tested independently

**Service Boundaries:**
- Backend services communicate via function calls (no async queues, no event bus in MVP)
- Frontend pages consume SessionContext + call API via `api.js` utility
- No inter-process communication; single process per service

**Data Boundaries:**
- **Content flow:** `exercises/*.yaml` → `content.py` (loads at startup) → in-memory list (full pools incl. `correct` flags, server-only)
- **Session flow:** `GET /api/sessions` → session randomizer filters + order-randomizes + samples 1-correct/3-distractor + shuffles positions + strips `correct` flags → Frontend SessionContext (flag-less Displayed Options only)
- **Feedback flow:** Frontend `POST /api/feedback` (`displayedOptionIds` + `selectedId`) → `feedback.py` single-select scoring → response (`correct`, `correctOptionId`, explanation) → `Feedback` component renders
- **Export flow:** `export.py` reads `exercises/*.yaml` → generates Anki format → downloads
- **No persistence** in MVP; session is ephemeral (memory-only)

### Requirements to Structure Mapping

| FR Group | Feature | Frontend Files | Backend Files | Content |
|----------|---------|---|---|---|
| **FR-1–4, FR-18, FR-19** | Exercise format (incl. Option Pool ≥1/≥3), loading, validation, portability | `api.js` (calls endpoints) | `content.py`, `export.py`, `models.py` (Option Pool validation) | `exercises/` (YAML) |
| **FR-5–12** | MCQ Practice (MVP priority) | `SessionSelect.jsx`, `MCQPractice.jsx`, `Feedback.jsx`, `SessionSummary.jsx` | `main.py` (/api endpoints), `feedback.py` (single-select correctness) | `associate/` YAML MCQs |
| **FR-20, FR-21** | Server-side sampling, option shuffle, randomized session order | `SessionSelect.jsx`/`MCQPractice.jsx` (consume `/api/sessions`) | `content.py` / `session.py` (session randomizer), `main.py` (`GET /api/sessions`) | — |
| **FR-22–25** | Answer & Stats Tracking (Epic 7) | `StatsDashboard.jsx`, `ReadinessIndicator.jsx`, `api.js` | `store.py` (SQLite), `main.py` (`GET /api/stats`, `/api/readiness`; record in `POST /api/feedback`), `session.py` (unseen-first) | `backend/data/progress.db` (gitignored) |
| **FR-26–28** | Timed Practice / Mock Exam (Epic 8) | `Timer.jsx`/`Countdown.jsx`, `MockExam.jsx`, `SessionSelect.jsx` (timed/mock affordance) | `session.py` (mock-exam builder), `main.py` (`mode=mock`) | — |
| **FR-13–17** | Code-Completion (Phase 2) | `CodeCompletion.jsx`, `FeedbackTokens.jsx`, `tokenizer.js` | `feedback.py` (code variant), `models.py` (CodeCompletion schema) | `associate/` code exercises |

### Integration Points

**Frontend ↔ Backend Communication:**
- Via REST API (`/api/*` endpoints)
- All requests/responses use standard `{success, data, error}` wrapper
- Frontend `api.js` wraps all HTTP calls; centralizes error handling

**Content Ingestion:**
- Backend loads YAML at startup → in-memory Exercise list
- No database; caching is in-memory
- Frontend never touches YAML directly; consumes via API

**External Integrations:**
- Explanation references (links to Databricks docs) open in new browser tab (external)
- Anki export: Standalone script; runs independently

**Error Propagation:**
- Backend errors → HTTP status + error JSON
- Frontend catches, sets `hasError` state → displays user-friendly message

### Development Workflow

**Backend Startup:**
```bash
cd backend
python -m uvicorn app.main:app --reload
# Runs on http://localhost:8000
# Auto-reloads on .py changes
```

**Frontend Startup:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
# Vite proxies /api/* to http://localhost:8000
# Hot module reload on .jsx/.css changes
```

**Content Iteration:**
```bash
# Edit exercises/associate/*.yaml
# Option 1: Restart backend (uvicorn --reload detects)
# Option 2: Implement file-watch in content.py (future)
```

**Testing:**
```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest

# Both with coverage
npm run test:coverage && pytest --cov
```

### Build & Deployment (Post-MVP)

**Frontend Build:**
```bash
cd frontend && npm run build
# Outputs to frontend/dist/
```

**Backend Packaging:**
```bash
# Single-binary: pyinstaller or similar
# Docker: Dockerfile wraps FastAPI + exercises/
# Run: python -m uvicorn app.main:app (or packaged binary)
```

**Anki Export Script:**
```bash
python backend/scripts/export_anki.py --output mydecks.apkg
```

---

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All technology choices (React + Vite frontend, Python + FastAPI backend, YAML content, Prism.js syntax highlighting, Context + useState state management) work seamlessly together with no version conflicts. All selections are modern, well-maintained, and proven in production.

**Pattern Consistency:**
Implementation patterns (camelCase for JS, PascalCase for components, REST endpoints, `{success, data, error}` response wrapper) align perfectly with React + FastAPI conventions. All patterns reinforce the chosen technology stack without friction or workarounds.

**Structure Alignment:**
Project structure (`exercises/` at root, `frontend/` and `backend/` as peer directories) directly reinforces the architectural priority: content is the primary deliverable; the app shell is the delivery mechanism. File organization supports all implementation patterns (co-located tests, component-based frontend, modular backend services). Boundaries are clean, explicit, and enforceable by linters and code review.

---

### Requirements Coverage Validation ✅

**Functional Requirements (21 total; FR-9 tombstoned):**

| Group | FRs | Architectural Support |
|-------|-----|----------------------|
| Content format & loading | FR-1–4, FR-18, FR-19 | `exercises/` YAML + `content.py` parser + Pydantic models (Option Pool ≥1/≥3 validation) + `export.py` Anki export ✓ |
| MCQ practice (MVP) | FR-5–12 | `SessionSelect.jsx`, `MCQPractice.jsx`, REST endpoints, Context state, `Feedback.jsx` (single-select) ✓ |
| Re-study variety / randomness | FR-20, FR-21 | Server-side session randomizer in `content.py`/`session.py` + `GET /api/sessions`; sampling, option shuffle, order randomization; flag-less Displayed Options ✓ |
| Code-Completion (Phase 2) | FR-13–17 | `CodeCompletion.jsx`, `FeedbackTokens.jsx`, `tokenizer.js`, `feedback.py` code variant ✓ |
| Exercise generation (deferred) | FR-4.4 | Format is generation-ready; authoring path is agent-skill (separate workstream) ✓ |

**Non-Functional Requirements:**

| NFR | Architectural Support |
|-----|----------------------|
| Code-Completion feedback < 100ms | Client-side tokenizer + instant DOM updates via React state ✓ |
| Single-user, local, **local persistence (rev 4)** | No auth/multi-user/sync; content file-based; answer history in a local SQLite store (`store.py`), read/written by sessions + feedback ✓ |
| Portability (Anki export) | `export.py` + standalone `export_anki.py` script ensures content survives app evolution ✓ |
| Content extensibility | Shared `id/domain/difficulty/explanation` fields support 8 future exercise types ✓ |

---

### Implementation Readiness Validation ✅

**Decision Completeness:**
All critical decisions documented with versions:
- Frontend: React 18+, Vite (latest), ESLint
- Backend: FastAPI (latest), Python 3.10+, pytest
- State: React Context + useState (immutable updates)
- Rendering: Prism.js for syntax highlighting
- Tokenization: Regex-based, language-specific (SQL case-insensitive, PySpark case-sensitive)
- Errors: Standard JSON wrapper with machine-readable codes
- Content: YAML→memory cache→REST API flow

**Structure Completeness:**
- ✅ All directories defined (44+ files/directories with explicit purposes)
- ✅ All critical files listed (pages, components, hooks, utilities, services)
- ✅ Requirements mapped to specific locations (FR-1 → exercises/, FR-5–12 → SessionSelect+MCQPractice+/api/exercises, etc.)
- ✅ Integration points explicit (7 API endpoints, 3 data flows: content→API, feedback→response, export→Anki format)

**Pattern Completeness:**
- ✅ Naming (7 conventions: components PascalCase, functions camelCase, APIs lowercase plural, JSON camelCase, state `is{Name}`, etc.)
- ✅ Structure (Frontend org, Backend org, Test co-location)
- ✅ Format (API wrapper, error codes, date ISO 8601)
- ✅ Communication (Context state flow, loading state naming)
- ✅ Process (Error codes + user messages, forbidden patterns)
- ✅ Examples (Good patterns, anti-patterns, React hook example, FastAPI endpoint example)

---

### Architecture Completeness Checklist

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (medium complexity, single-user, file-based, no database)
- [x] Technical constraints identified (< 100ms latency, file-based content, portable format)
- [x] Cross-cutting concerns mapped (Content portability, Build-vs-Borrow, Wordle playfulness)
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified (React 18+, Vite, FastAPI, Python 3.10+, Prism.js)
- [x] Integration patterns defined (REST API, content loading, feedback flow, export)
- [x] Performance considerations addressed (client-side tokenizer for < 100ms target)
- [x] Naming conventions established (7 categories with examples + anti-patterns)
- [x] Structure patterns defined (Frontend/Backend/Content with complete file lists)
- [x] Communication patterns specified (Context state, loading state naming, error codes)
- [x] Process patterns documented (Error handling, user-facing messages)
- [x] Complete directory structure defined (all 44+ files/directories with purposes)
- [x] Component boundaries established (SessionSelect → MCQPractice → Feedback data flow)
- [x] Integration points mapped (7 API endpoints, 3 data flows, Anki export)
- [x] Requirements to structure mapping complete (all 18 FRs + NFRs mapped)

---

### Architecture Readiness Assessment

**Overall Status:** ✅ **READY FOR IMPLEMENTATION**

All 16 checklist items verified. No critical gaps. All requirements architecturally supported. Implementation patterns are comprehensive, enforceable, and sufficient for AI agents or human developers to build consistently.

**Confidence Level:** **High**

The architecture is detailed, coherent, and provides clear guidance without over-specification. Clean boundaries, explicit patterns, concrete examples, and complete structure minimize ambiguity and conflict.

**Key Strengths:**
1. **Content-first prioritization** directly reflects the real MVP bottleneck (content authoring + exam prep, not app polish)
2. **Clear service separation** (content.py, feedback.py, export.py) prevents entanglement
3. **Comprehensive naming conventions** address the 7 most likely agent conflicts (components, functions, variables, endpoints, JSON fields, state, flags)
4. **Build-vs-Borrow strategy** is architecturally explicit: borrow MCQ runner (table-stakes), build Wordle feature (novel)
5. **Portable format** ensures content survives app evolution and is never locked into the app

**Areas for Future Enhancement (Post-MVP):**
- Startup convenience scripts (Makefile for `make dev`, `make test`)
- Docker configuration for Phase 2 distribution / sharing with peers
- SRS / analytics layer (Phase 2+, requires persistence)
- Hot-reload for exercises (file-watch in content.py for dev convenience)

---

### Implementation Handoff

This architecture document is **ready to guide implementation**. AI agents or team members can begin work immediately following these guidelines:

**Golden Path (Recommended Order):**
1. Initialize project structure (create all directories listed above; create empty files)
2. Implement Backend Phase 1:
   - `models.py` (Pydantic models: Exercise/MCQ with Option Pool ≥1/≥3 validation, Session, Feedback)
   - `content.py` (YAML loading, filtering, validation) + session randomizer (sampling, option shuffle, order randomization — FR-19/20/21)
   - `main.py` (FastAPI app + `GET /api/sessions` endpoint returning flag-less Displayed Options)
3. Implement Frontend Phase 1:
   - `SessionContext.jsx` + `useSession.js` (context provider + consumer hook)
   - `SessionSelect.jsx` (domain/difficulty filter UI)
   - `api.js` (HTTP wrapper + `GET /api/sessions` call)
4. Implement Backend Phase 1b:
   - `feedback.py` (single-select MCQ correctness; scores `selectedId` against the displayed correct option)
   - `main.py` `POST /api/feedback` endpoint (`displayedOptionIds` + `selectedId`)
5. Implement Frontend Phase 1b:
   - `MCQPractice.jsx` (exercise display + answer selection)
   - `Feedback.jsx` (correctness + explanation rendering)
   - `ExerciseDisplay.jsx` (code snippet rendering with Prism.js)
6. Author initial exercise content (`exercises/associate/*.yaml` — ~50–75 MCQs)
7. Implement Anki export:
   - `export.py` (MCQ → Anki format conversion)
   - `scripts/export_anki.py` (standalone CLI)
   - Test + validate export to Anki
8. Phase 2 (after exam deadline):
   - `CodeCompletion.jsx` + `FeedbackTokens.jsx`
   - `tokenizer.js` (language-specific tokenization)
   - `feedback.py` code-completion variant + `/api/feedback/code-completion`
   - Test Wordle feedback rendering

**Constraints & Guardrails for Implementers:**
- **MUST:** Follow all naming conventions (FR-specific patterns are non-negotiable for multi-agent consistency)
- **MUST:** Use the standard API response wrapper on every endpoint
- **MUST:** Keep error handling consistent (error codes + user-friendly messages)
- **MUST:** Place tests co-located with source files (`.test.jsx`, `.test.py`)
- **MUST:** Respect component/service boundaries (no cross-cutting state mutations)
- **Should:** Review this document before starting each major component
- **Should:** Refer to implementation patterns for naming/structure questions

---
