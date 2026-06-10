---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/architecture.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md
revisions:
  - date: '2026-06-05'
    summary: 'Added Epic 5 (MCQ Variety & Randomization — FR-7/19/20/21, AR-13/14/15) and Epic 6 (Session Control & Study QoL — UX-DR1–12, gaps G1/G2/G3) with 6 stories each. FR-9 removed. Sourced from PRD rev 2, architecture rev 3, EXPERIENCE.md.'
  - date: '2026-06-07'
    summary: 'Added Epic 7 (Answer & Stats Tracking — FR-22–25, AR-16/17; 5 stories) and Epic 8 (Timed Practice / Mock Exam — FR-26–28, AR-18; 4 stories). NFR-2/NFR-3 revised (local SQLite persistence; reverses no-persistence). FR-24 supersedes FR-21 ordering. Sourced from PRD rev 3 §4.5/§4.6, architecture rev 4, addendum §E.'
  - date: '2026-06-09'
    summary: 'Added Epic 9 (Multi-Provider / Multi-Certification — FR-29/FR-30, AR-19; 5 stories) and Epic 10 (Containerization & Sharing — FR-31, NFR-5, AR-20; 4 stories). Product renamed to "Cert Study Companion"; Databricks DE preserved as the first bundled Certification. Per-Certification config (canonical Domains, weights, exam params) moves from hardcoded into file-based YAML loaded at startup; the `exam` field is retained as the Certification identifier. Adds one-command containerized run (docker compose) for shareability. Both epics layer on shipped Epics 1–8 + Epic 4. Sourced from PRD rev 5 §4.7/§4.8, addendum §G/§H.'
---

# DataBricks-DE-cert-study-companion - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for DataBricks-DE-cert-study-companion, decomposing the requirements from the PRD, Architecture, and Addendum into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR-1:** Standardized, parseable Exercise format — The format defines each Exercise with stable `id`, Exercise Type, Domain, difficulty, question/prompt, type-specific payload, Explanation, and optional reference link(s) and tags.

**FR-2:** App loads Exercise Sets from files — The app discovers and loads Exercise Set files from a designated content location at startup, making new well-formed files available without code changes.

**FR-3:** Fail clearly on malformed content — Malformed Exercise files fail loudly with enough information to locate the problem (file + Exercise id).

**FR-4:** Blueprint-aligned Domain tagging — Domains align with Databricks' official exam blueprint so content can be filtered and weighted to mirror the real exam.

**FR-5:** Start a Practice Session with filters — User can start a session filtered by Domain, difficulty, Exercise Set, or Exercise Type.

**FR-6:** Present one MCQ at a time, exam-style — Session shows a single MCQ with question text, code snippet (if any) in monospace, and selectable Options.

**FR-7:** Select one answer and submit — User selects exactly one Option (single-select, radio affordance) and submits; selecting another replaces the prior selection. *(Revised PRD rev 2: single-select only.)*

**FR-8:** Immediate correctness feedback — On submit, app indicates whether answer was correct and which Option(s) were correct.

**FR-9:** ~~Defined multi-select scoring~~ — **REMOVED (PRD rev 2).** Multi-select variant and all-or-nothing scoring removed; MCQ is single-select only. An answer is correct iff the single selected Option is the displayed correct Option. ID retained as a tombstone.

**FR-10:** Show Explanation after answering — After submit, app shows Explanation with why-correct and why-distractor-wrong rationale, plus reference link(s).

**FR-11:** Advance through the session — User can move to next Exercise after reviewing feedback until session is complete.

**FR-12:** End-of-session summary — Session end shows simple summary: number correct / total, and per-Domain breakdown when session spans multiple Domains.

**FR-13:** Present a Code-Completion Exercise — App presents prompt, code template with blank/slot clearly indicated, and input affordance. (Phase 2)

**FR-14:** Accept a typed attempt and give Positional Feedback — On attempt, app evaluates against canonical answer and renders Positional Feedback (< 100ms target). (Phase 2)

**FR-15:** Limited guesses with reveal — User has bounded number of attempts; on solving or exhausting attempts, canonical answer is revealed. (Phase 2)

**FR-16:** Accept valid alternative answers — Authored alternative correct phrasings are treated as correct. (Phase 2)

**FR-17:** Show Explanation after Code-Completion Exercise — Explanation and references shown once exercise concludes. (Phase 2)

**FR-18:** Portable / exportable content — Exercise format is portable enough that MCQ content can be consumed by existing study tool (Anki); conversion preserves question, options, correct answer(s), and Explanation.

**FR-19:** MCQ Option Pool — Each MCQ is authored as an Option Pool with **≥1 correct and ≥3 incorrect** options, no upper bound; extra correct alternatives and/or distractors encouraged. Multiple correct options are **interchangeable alternatives**, never a jointly-required set. Validation rejects pools that can't yield a 1-correct + 3-incorrect display. *(New, PRD rev 2.)*

**FR-20:** Sample & shuffle Displayed Options — When presenting an MCQ, the runner samples **1 correct + 3 incorrect** options from the pool and renders them in **randomized positions**. Two presentations of the same question can differ in correct option and/or distractors; the correct option is not position-stable. Computed **server-side**; correct flags never sent to the client. *(New, PRD rev 2.)*

**FR-21:** Randomize Exercise order per Practice Session — *(superseded for ordering by FR-24 unseen-first, PRD rev 3; option sampling/shuffle remain random).* Computed server-side. *(PRD rev 2.)*

**FR-22:** Persist attempt history — Each answered Exercise is recorded to a durable local store (exercise id, exam, domain, correct, selected id, time taken, timestamp); history survives restarts; recorded at grade time (POST /api/feedback); displayed-but-unanswered ≠ attempt. *(New, PRD rev 3.)*

**FR-23:** Stats dashboard — Overall accuracy + total attempts, per-Domain accuracy, trend over time, and weak-Domain highlighting. *(New, PRD rev 3.)*

**FR-24:** Unseen-first prioritization — Session building serves not-yet-answered Exercises (within active filters) before seen ones; all-seen fallback orders least-recently-seen; randomize within the unseen group. *(New, PRD rev 3; supersedes FR-21 ordering.)*

**FR-25:** Readiness indicator — Rolling-window accuracy vs the ~70% pass bar, overall + per-Domain (guidance, not a guarantee). *(New, PRD rev 3.)*

**FR-26:** Optional session countdown — Any Practice Session can run with an optional countdown (set/auto duration, visible remaining time, auto-end to summary at zero); off = unchanged behavior. *(New, PRD rev 3.)*

**FR-27:** Mock-Exam mode — Domain-weighted, full-length set scoped to one Exam under real exam timing (Associate ≈45Q/90min, Pro ≈59Q/120min), auto-submit at zero, exam-style final score; ignores unseen-first. *(New, PRD rev 3.)*

**FR-28:** Per-question timing — Time taken per answered question is captured client-side and stored with the attempt (feeds FR-22/FR-23). *(New, PRD rev 3.)*

**FR-29:** Per-Certification configuration — Each Certification's canonical Domain list, Domain weights, and exam parameters (total_questions, duration_minutes, pass_bar) live in file-based YAML config loaded at startup, not hardcoded; the seed config re-expresses today's Databricks Associate (45Q/90min) and Professional (59Q/120min) literals and weights with no behavior change. *(New, PRD rev 5 §4.7.)*

**FR-30:** Multi-Certification content org + Provider/Certification selection — Content is organized under a Provider→Certification model; the user selects a Provider/Certification and sessions are scoped to it. The `exam` field is retained as the Certification identifier (associate/professional are two Certifications under the Databricks Provider, so Story 6.7's exam filter keeps working). Adding a Certification = content + config, no code change. *(New, PRD rev 5 §4.7.)*

**FR-31:** One-command containerized run — One `docker compose up` runs the whole app for a colleague with only Docker installed (no host Node/Python/uv); each colleague runs their own single-user instance; the SQLite history store persists across `docker compose down && up` via a mounted volume. *(New, PRD rev 5 §4.8; reverses the prior no-containerization stance.)*

**FR-32:** Capture question feedback in-app, persisted to a sidecar file — From the practice surface the learner attaches a free-text note to the current Exercise; it is saved to a sidecar YAML keyed by Exercise `id` (timestamp + `resolved` flag), surviving restarts, **without modifying the authored Exercise file**. *(New, PRD rev 6 §4.9; the app's first content-write path.)*

**FR-33:** Skill-driven revision of flagged questions — The `write-mcq` skill reads an Exercise's open feedback, revises the question in place in its source YAML, re-validates, and marks the feedback entries resolved (author reviews the diff). MCQ-first. *(New, PRD rev 6 §4.9.)*

### Non-Functional Requirements

**NFR-1:** Code-Completion feedback latency — Positional Feedback must feel instant (target < 100ms from keystroke to rendered feedback); comparison is small and should be computable client-side.

**NFR-2:** Single-user, local, **local persistence** *(revised PRD rev 3)* — Single-user local app, no accounts/auth/multi-user/server-side user data/sync. The user's own answer history is persisted to a **local SQLite store** (reverses the prior no-persistence stance; the session runner is no longer stateless).

**NFR-3:** Storage — Content stays file-based (YAML loaded at startup); answer history lives in a local SQLite DB (`sqlite3` stdlib, gitignored `backend/data/progress.db`). *(Revised PRD rev 3.)*

**NFR-4:** Portable format — Exercise format is portable to Anki and other tools so studying is never blocked on app completion.

**NFR-5:** Shareability — A colleague can run the whole app from a clone with only Docker installed, no host toolchain (Node/Python/uv); distribution is local self-serve (each runs their own instance), not a hosted multi-user service. *(New, PRD rev 5 §4.8.)*

### Additional Requirements (Architecture & Technical)

**AR-1:** Frontend framework — React 18+ with Vite dev server for hot module reload and fast builds.

**AR-2:** Styling solution — Tailwind CSS for styling + custom React components (no heavy component library).

**AR-3:** Backend framework — Python 3.10+ with FastAPI for async, minimal, REST API.

**AR-4:** Content format — YAML-authored exercise files in `exercises/` directory at project root; optional JSON serving internally.

**AR-5:** API design — REST endpoints with standard response wrapper: `{success: bool, data: {...}, error: {...}}`.

**AR-6:** Error handling — Standard JSON error format with machine-readable error codes + user-friendly messages.

**AR-7:** State management — React Context + useState for session state (exercises list, current index, selected answers, feedback).

**AR-8:** Code rendering — Prism.js for syntax highlighting in exercise display.

**AR-9:** ~~Code tokenization — Regex-based tokenizer (language-specific) for Code-Completion token-level feedback.~~ **SUPERSEDED 2026-06-10 (decision-log #54, Story 4.8):** feedback is now CHARACTER-level (per-letter), so no tokenizer is needed; `tokenizer.js` is removed and `codeFeedback.js` compares per-character.

**AR-10:** Development workflow — Concurrent dev servers (frontend on 3000 proxying `/api/*` to backend on 8000).

**AR-11:** Testing — Tests co-located with source files (`.test.jsx`, `.test.py`); frontend: Vitest/Jest; backend: pytest.

**AR-12:** Naming conventions — PascalCase for React components, camelCase for JS functions/variables, lowercase plural for API endpoints, camelCase for JSON fields.

**AR-13:** Server-side session randomizer — A stateless, non-deterministic (per-request) component in `content.py`/`session.py` performs option-pool sampling, option-position shuffle, and exercise-order randomization; standard-library RNG, no seed/anti-repeat memory in MVP. (Architecture rev 2.)

**AR-14:** Session API contract — `GET /api/sessions` is the runner entry point, returning order-randomized exercises each with 4 flag-less Displayed Options (`{id, text}`); `GET /api/exercises` is demoted to admin/debug so pools/correct flags never reach the practice UI. `POST /api/feedback` takes `{exerciseId, displayedOptionIds, selectedId}` and returns `{correct, correctOptionId, explanation, references}`. (Architecture rev 2.)

**AR-15:** Pydantic Option Pool validation — `models.py` enforces ≥1 correct / ≥3 incorrect for `single_choice`; the legacy "single_choice ⇒ exactly one correct" rule is relaxed to allow interchangeable alternatives; `multi_choice` is rejected. (Architecture rev 2.)

**AR-16:** Local SQLite attempt store — `backend/app/store.py` using `sqlite3` (stdlib, no pip); gitignored `backend/data/progress.db`; create-table-if-not-exists on startup (lifespan); `attempts(id, exercise_id, exam, domain, correct, selected_id, time_taken_ms, answered_at)`; helpers for record/aggregations/attempted-ids/last-seen. Best-effort writes never block grading. (Architecture rev 4.)

**AR-17:** Stats/readiness + unseen-first endpoints — `GET /api/stats` and `GET /api/readiness` aggregate the store; `GET /api/sessions` ordering reads the store for unseen-first; `POST /api/feedback` records the attempt (+`timeTakenMs`). Standard `{success,data,error}` wrapper. (Architecture rev 4.)

**AR-18:** Mock-Exam builder + frontend timer — backend `mode=mock` builder (domain-weighted, full-length, exam-scoped, ignores unseen-first, stamps `durationMinutes`); timer/countdown + per-question timing are client-side (send `timeTakenMs` with feedback); new FE components StatsDashboard, ReadinessIndicator, Timer/Countdown, MockExam. (Architecture rev 4.)

**AR-19:** Per-Certification config loader + `GET /api/certifications` — a file-based YAML registry (Providers→Certifications→{name, total_questions, duration_minutes, pass_bar, domains[{name,weight}]}) loaded at startup; a Pydantic `Certification` model. The `ExamType`/`Domain` enums and `MOCK_EXAM_CONFIGS` in `models.py`/`session.py` are derived from this registry instead of being literal; `exam` is retained as the Certification id (exam→certification semantics) so session/mock/unseen-first/stats keep keying on `(certification, domain)`. New `GET /api/certifications` serves the registry; `frontend/src/constants.js` `EXAMS`/`DOMAINS_BY_EXAM` become data fetched from it. (Architecture rev 6, addendum §G.)

**AR-20:** Container stack — `backend/Dockerfile` (Python base, install deps, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`), `frontend/Dockerfile` (multi-stage `npm ci && npm run build` → static serve of `dist/` with `/api/*` proxied to the backend service, replacing the Vite dev proxy), and a `docker-compose.yml` wiring the two services on a shared network with a mounted volume at `backend/data/` so `progress.db` survives restarts; bind-mounts of `exercises/` + config let colleagues add content without rebuilding. (Architecture rev 6, addendum §H.)

**AR-21:** Feedback sidecar + write path — new `backend/app/feedback_store.py` (read/write `exercises/feedback.yaml`, keyed by Exercise `id`: `add_note`, `notes_for`, `open_notes`, `mark_resolved`; create-if-absent, small lock) and a new `POST /api/exercise-feedback {exerciseId, note}` endpoint (server-stamps `created_at`, `resolved: false`; validates the id exists; standard `{success,data,error}` wrapper) — distinct from the MCQ-grading `POST /api/feedback`. The app's first content-write path; never modifies authored Exercise files. Writeback needs a writable content mount (ties OQ-8/OQ-9). (Architecture rev 8, addendum §I.)

### UX Design Requirements (EXPERIENCE.md)

Functional/quality-of-life behaviors layered on the existing MVP. Source: `ux-designs/ux-DataBricks-DE-cert-study-companion-2026-06-05/EXPERIENCE.md` (status final).

**UX-DR1:** Persistent **End-session** control on the Practice screen that exits to the Start screen; routes through an Exit-confirm unless zero questions are answered.

**UX-DR2:** **Exit-confirm modal** (focus-trapped, Esc = keep practicing) offering: *See results* (partial Summary) / *Discard & exit* / *Keep practicing*.

**UX-DR3:** **Clickable header title = Home** from any surface; on Practice it behaves like End-session (routes through Exit-confirm).

**UX-DR4:** **Restart same session** from Summary — replays the same exercise set via `POST /api/sessions {exerciseIds}` (fresh-sampled/shuffled, re-randomized order).

**UX-DR5:** **Visual progress bar + running correct count** on Practice, replacing the text-only "Question X of Y".

**UX-DR6:** **Back / Previous** navigation to revisit already-answered questions **read-only** (selection, correctness, explanation shown; options disabled).

**UX-DR7:** **Keyboard shortcuts** on Practice — `1`–`4`/`a`–`d` select, `Enter` submit then advance, `←`/`→` back/next, `Esc` open/close Exit-confirm. Pointer parity required.

**UX-DR8:** **Skip** the current question — records it as *unanswered* (not incorrect), revisitable via Back, surfaced in Summary as *Skipped*.

**UX-DR9:** **Live match count** on the Start screen ("{n} questions match") via `GET /api/exercises/count`, updating as filters change; before commit.

**UX-DR10:** **Review-incorrect** list on Summary (question + correct option + explanation per missed item) and **"Practice these N again"** → new session via `POST /api/sessions {exerciseIds}`.

**UX-DR11:** **Quit-to-partial-Summary** — early exit computes the Summary over the answered subset (skipped/unanswered surfaced as counts).

**UX-DR12:** **Accessibility floor** — full keyboard operability with visible focus, single-select radio-group semantics, focus-trapped labeled modal, `aria-live` for result/progress, color-independent feedback (✓/✗ + text alongside color).

### FR Coverage Map

| FR | Epic | Capability |
|----|------|------------|
| FR-1 | Epic 2 | Standardized exercise format |
| FR-2 | Epic 2 | App loads exercise files at startup |
| FR-3 | Epic 2 | Fail clearly on malformed content |
| FR-4 | Epic 2 | Blueprint-aligned domain tagging |
| FR-5 | Epic 3 | Start practice session with filters |
| FR-6 | Epic 3 | Present one MCQ at a time |
| FR-7 | Epic 3 → Epic 5 | Select one answer and submit (single-select; refactored in Epic 5) |
| FR-8 | Epic 3 | Immediate correctness feedback |
| FR-9 | — | ~~Multi-select scoring~~ removed (PRD rev 2) |
| FR-10 | Epic 3 | Show explanation after answering |
| FR-11 | Epic 3 | Advance through session |
| FR-12 | Epic 3 | End-of-session summary |
| FR-13 | Epic 4 | Present code-completion exercise (Phase 2) |
| FR-14 | Epic 4 | Accept attempt & give positional feedback (Phase 2) |
| FR-15 | Epic 4 | Limited guesses with reveal (Phase 2) |
| FR-16 | Epic 4 | Accept valid alternative answers (Phase 2) |
| FR-17 | Epic 4 | Show explanation after code exercise (Phase 2) |
| FR-18 | Epic 2 | Portable/exportable content |
| FR-19 | Epic 5 | MCQ Option Pool (≥1 correct / ≥3 incorrect) + validation |
| FR-20 | Epic 5 | Server-side option sampling + position shuffle |
| FR-21 | Epic 5 | Randomized order (superseded for ordering by FR-24) |
| FR-22 | Epic 7 | Persist attempt history (SQLite store) |
| FR-23 | Epic 7 | Stats dashboard (overall + per-domain) |
| FR-24 | Epic 7 | Unseen-first session prioritization |
| FR-25 | Epic 7 | Readiness indicator (vs ~70%) |
| FR-26 | Epic 8 | Optional session countdown + auto-end |
| FR-27 | Epic 8 | Mock-Exam mode (domain-weighted, exam-timed) |
| FR-28 | Epic 8 | Per-question timing (feeds stats) |
| FR-29 | Epic 9 | Per-Certification config (domains, weights, exam params) |
| FR-30 | Epic 9 | Multi-Certification content org + Provider/Certification selection |
| FR-31 | Epic 10 | One-command containerized run + persistence |
| FR-32 | Epic 11 | In-app question feedback → sidecar YAML |
| FR-33 | Epic 11 | write-mcq feedback-driven revision |

### UX-DR Coverage Map (Epic 6)

| UX-DR | Epic | Capability |
|-------|------|------------|
| UX-DR1, UX-DR2, UX-DR3 | Epic 6 | End-session control, Exit-confirm modal, clickable Home |
| UX-DR4, UX-DR10 | Epic 6 | Restart-same / Practice-incorrect-again (`POST /api/sessions {exerciseIds}`) |
| UX-DR5 | Epic 6 | Visual progress bar + running score |
| UX-DR6, UX-DR8 | Epic 6 | Back/Previous (read-only revisit) + Skip |
| UX-DR7 | Epic 6 | Keyboard shortcuts |
| UX-DR9 | Epic 6 | Start-screen match count (`GET /api/exercises/count`) |
| UX-DR10, UX-DR11 | Epic 6 | Review-incorrect + quit-to-partial-Summary |
| UX-DR12 | Epic 6 | Accessibility floor |

---

## Epic List

### Epic 1: Project Setup & Infrastructure
Establish the complete development environment with all necessary scaffolding, tooling, and infrastructure ready for feature development.

**What developers accomplish:** Local dev environment fully configured (React + Vite frontend, FastAPI backend, Tailwind CSS), all project structure in place, dev server running with hot reload, tests framework configured and runnable.

**FRs/ARs covered:** AR-1, AR-2, AR-3, AR-5, AR-10, AR-11, AR-12

### Epic 2: Exercise Content Management System
Implement the content loading, validation, and export system that powers everything.

**What users/developers accomplish:** Authors can create/edit YAML exercise files, app loads and validates exercises at startup with clear error reporting, content can be exported to Anki, domain filtering and tagging works.

**FRs/ARs covered:** FR-1, FR-2, FR-3, FR-4, FR-18, AR-4, AR-6

### Epic 3: MCQ Study Practice Interface
Implement the core exam-realistic MCQ practice experience.

**What users accomplish:** Filter exercises by domain/difficulty, practice one MCQ at a time, get immediate correctness feedback + explanations, see session summaries and scores, code snippets render correctly with syntax highlighting.

**FRs/ARs covered:** FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-12, NFR-1, NFR-2, NFR-3, AR-7, AR-8

### Epic 4: Code-Completion Practice (implemented 2026-06-09; runner in review)
Implement the Wordle-style code-completion exercises for syntax drilling.

**What users accomplish:** Practice code syntax with interactive feedback, see token-level green/yellow/grey feedback as they type, learn syntax through the playful guess-and-narrow loop, see explanations and canonical answers.

**FRs/ARs covered:** FR-13, FR-14, FR-15, FR-16, FR-17, NFR-1, AR-9; plus **Story 4.7** (exercise-type multiselect filter — discoverability) and **Story 4.6** (content bank + authoring skill, still `ready-for-dev`).

**Status (2026-06-10):** stories 4.1–4.5 + 4.7 implemented and code-reviewed (10 findings fixed; decision-log #41–46), in `review`. Story 4.6 (starter content + `write-code-completion` skill) is the only remaining `ready-for-dev` story.

### Epic 5: MCQ Variety & Randomization  🔝 TOP PRIORITY (next to implement)
Make every MCQ a fair single-select drawn from an Option Pool, with server-side sampling, option shuffle, and randomized session order so re-study feels fresh.

**What users accomplish:** Questions no longer replay identically — a re-seen question shows a different correct option and/or distractors in shuffled positions, and sessions are in randomized order. Single-select only; no leaked answers.

**FRs/ARs covered:** FR-7 (single-select), FR-19, FR-20, FR-21; AR-13 (session randomizer), AR-15 (Option Pool validation), AR-14 (GET /api/sessions + revised POST /api/feedback).

**Priority:** TOP — implement before Epic 4. Builds on the merged Epic 2/3 code (refactors `models.py`, the MCQ runner, and the session/feedback contract). Includes content migration of the legacy `multi_choice` items (`dbx-de-0009`, `dbx-de-0027`).

### Epic 6: Session Control & Study QoL
Give the learner control over the practice session: end/exit/restart, navigation (back, skip, keyboard, progress), right-sizing before start, and end-of-session review.

**What users accomplish:** End a session and return home (with a confirm and optional partial results), restart or re-drill missed questions, move back/skip/by-keyboard, see a progress bar + running score, and preview how many questions match before starting.

**FRs/ARs covered:** UX-DR1–UX-DR12; backend `GET /api/exercises/count` (G1) and `POST /api/sessions {exerciseIds}` (G2); frontend feedback-retention + reducer actions/states (G3); **exam filter / session scoping (Story 6.7 — added after Professional content landed so sessions don't mix exams).**

**Priority:** After Epic 5, before Epic 4. Builds on Epic 5's refactored single-select runner (clean dependency; Epic 5 stands alone). Source: EXPERIENCE.md (final).

### Epic 7: Answer & Stats Tracking
Persist the learner's answer history locally and turn it into study guidance.

**What users accomplish:** Their answers are remembered across sessions; they see overall + per-Domain accuracy, trends, and weak areas; they get served questions they haven't seen before first; and a readiness signal tells them how close they are to the ~70% pass bar per Domain.

**FRs/ARs covered:** FR-22, FR-23, FR-24, FR-25 (+FR-28 record hook); AR-16, AR-17; revises NFR-2/NFR-3.

**Priority:** Next after Epic 6, before Epic 8 and Epic 4. Introduces local SQLite persistence (reverses no-persistence). Source: PRD rev 3 §4.5, architecture rev 4, addendum §E.

### Epic 8: Timed Practice / Mock Exam
Add exam-realistic time pressure: an optional countdown for any session, and a full domain-weighted Mock-Exam mode at real exam timing.

**What users accomplish:** Run any practice session against a countdown that auto-ends; or take a full Mock Exam (Associate 45Q/90min, Pro 59Q/120min, domain-weighted) with an exam-style score; per-question timing feeds the stats.

**FRs/ARs covered:** FR-26, FR-27, FR-28; AR-18.

**Priority:** After Epic 7 (its mock-exam builder + per-question timing depend on Epic 7's store + feedback record hook), before Epic 4. Source: PRD rev 3 §4.6, architecture rev 4.

### Epic 9: Multi-Provider / Multi-Certification
Generalize the Databricks-only app into a provider-agnostic one by moving the canonical Domain list, Domain weights, and exam parameters out of code and into file-based config — so a new Certification is content + config with no code change.

**What users/developers accomplish:** A new glossary (Provider + Certification) replaces the Databricks-only framing; per-Certification config (canonical Domains, weights, total_questions/duration_minutes/pass_bar) loads from YAML at startup; the Start screen's exam taxonomy is fetched from the backend instead of hand-maintained; Databricks DE is fully preserved as the first bundled Certification (Associate + Professional become two Certifications under the Databricks Provider). The polished Provider→Certification switcher UI and a second bundled provider's content are deferred (this iteration: model + config + one provider).

**FRs/ARs covered:** FR-29, FR-30 (+FR-4 validation extended); AR-19 (config loader + `GET /api/certifications` + exam→certification semantics).

**Priority:** Before Epic 10 (Epic 10's compose bundles the generalized app). Both layer on shipped Epics 1–8 + Epic 4 — the `exam` field is retained (PRD §3) so Story 6.7's exam filter and the mock builder keep working; the change is "where the lists/weights come from," not a field rename. Guardrail: no Databricks DE regression. Source: PRD rev 5 §4.7, addendum §G.

### Epic 10: Containerization & Sharing
Package the whole app so one `docker compose up` runs it for a colleague who has only Docker installed, with their answer history persisting across restarts.

**What users/developers accomplish:** A colleague clones the repo, runs `docker compose up`, and opens a documented local URL — no host Node/Python/uv. Backend and frontend each ship a Dockerfile; compose wires them on a shared network; the SQLite store persists via a mounted volume; `exercises/` + config are bind-mounted so content can be added without rebuilding. Each colleague runs their own single-user instance (not hosted multi-user).

**FRs/ARs covered:** FR-31, NFR-5; AR-20 (Dockerfiles + docker-compose.yml + SQLite volume).

**Priority:** After Epic 9 (compose bundles the generalized app), and layers on shipped Epics 1–8 + Epic 4. Reverses the prior "no containerization for MVP" stance. Source: PRD rev 5 §4.8, addendum §H.

### Epic 11: Question Feedback & Content-Improvement Loop
Let learners flag a question in-app with a free-text note (saved to a sidecar file), and let the `write-mcq` skill revise flagged questions from that feedback.

**What users accomplish:** While practicing, the learner attaches a note to a bad/unclear question; it persists to a sidecar `exercises/feedback.yaml` (authored files untouched). Later, the author runs `write-mcq` against the open feedback to fix the questions in place and mark the notes resolved — study friction becomes a better content bank.

**FRs/ARs covered:** FR-32 (capture → sidecar), FR-33 (skill revision); AR-21 (`feedback_store.py` + `POST /api/exercise-feedback` write path — the app's first content-write path).

**Priority:** Active (PRD rev 6 §4.9, decision-log #47–53). Story 11.1 (capture + persistence) is the develop-now story; 11.2 (write-mcq revision) follows. Source: addendum §I.

---

## Stories

### Story 1.1: Initialize Project Structure

As a **developer**,
I want **project directories and configuration files set up**,
So that **I have a clean foundation to build on**.

**Acceptance Criteria:**

**Given** the project has just been cloned
**When** I examine the directory structure
**Then** I see: `exercises/`, `frontend/`, `backend/`, `docs/` directories created
**And** `.gitignore` is configured to exclude common files (node_modules, __pycache__, .venv, etc.)
**And** `README.md` exists with basic project overview and setup instructions

---

### Story 1.2: Set Up React + Vite Frontend

As a **developer**,
I want **React and Vite configured with hot reload**,
So that **I can develop the frontend with fast feedback**.

**Acceptance Criteria:**

**Given** the frontend directory exists
**When** I run `npm install` in the frontend directory
**Then** dependencies are installed (React, Vite, ESLint)
**And** `vite.config.js` is configured to proxy `/api/*` to the backend
**And** `npm run dev` starts the dev server on localhost:3000
**And** hot module reload works (code changes refresh instantly)

---

### Story 1.3: Set Up Python + FastAPI Backend

As a **developer**,
I want **FastAPI and Python environment configured**,
So that **I can develop the backend API**.

**Acceptance Criteria:**

**Given** the backend directory exists
**When** I run `pip install -r requirements.txt` (or `uv sync`)
**Then** dependencies are installed (FastAPI, Pydantic, pytest, uvicorn)
**And** `app/main.py` creates a FastAPI application
**And** `python -m uvicorn app.main:app --reload` starts the server on localhost:8000
**And** `GET /` returns a 200 with a simple health check response

---

### Story 1.4: Configure Tailwind CSS

As a **developer**,
I want **Tailwind CSS integrated into the React frontend**,
So that **I can style components with utility classes**.

**Acceptance Criteria:**

**Given** the frontend React app is set up
**When** I install Tailwind via `npm install tailwindcss postcss autoprefixer`
**Then** `tailwind.config.js` is configured
**And** `postcss.config.js` is configured
**And** `src/styles/global.css` imports Tailwind
**And** Tailwind classes work in React components (e.g., `className="p-4 bg-blue-500"`)

---

### Story 1.5: Configure Testing Infrastructure

As a **developer**,
I want **frontend and backend testing frameworks configured**,
So that **I can write and run tests**.

**Acceptance Criteria:**

**Given** the frontend and backend are set up
**When** I run `npm test` in the frontend
**Then** Jest or Vitest runs and can find test files (`.test.jsx`)
**And** test output is clear (pass/fail for each test)
**And** When I run `pytest` in the backend
**Then** pytest finds and runs test files (`test_*.py`)

---

### Story 2.1: Define Exercise Model & YAML Schema

As a **content author**,
I want **a clear YAML schema for exercises**,
So that **I can author exercises with confidence**.

**Acceptance Criteria:**

**Given** I want to create a YAML exercise file
**When** I write an MCQ following the defined schema
**Then** the file structure is: `id`, `type` (single_choice/multi_choice), `exam`, `domain`, `difficulty`, `question`, `options[]`, `answer[]`, `explanation`
**And** a Code-Completion template includes: `id`, `type`, `language`, `prompt`, `template`, `answer`, `accepted[]`
**And** Pydantic models in `backend/app/models.py` define Exercise, MCQ, CodeCompletion with validation

---

### Story 2.2: Implement Content Loader

As a **the app**,
I want **to load YAML exercise files from the exercises/ directory**,
So that **exercises are available at startup**.

**Acceptance Criteria:**

**Given** YAML exercise files exist in `exercises/associate/*.yaml`
**When** the FastAPI app starts
**Then** `app/content.py` scans the `exercises/` directory
**And** all valid YAML files are parsed and loaded into memory
**And** `GET /api/exercises` returns the loaded exercises
**And** `GET /api/exercises?domain=...&difficulty=...` filters the list

---

### Story 2.3: Implement Content Validation

As a **the app**,
I want **to validate exercise files and report errors clearly**,
So that **malformed content fails loudly with helpful messages**.

**Acceptance Criteria:**

**Given** an exercise YAML file has invalid syntax or schema
**When** the app tries to load it
**Then** loading fails with an error message naming the file and the problem
**And** other valid exercises still load
**And** the error includes the Exercise `id` if available

---

### Story 2.4: Implement Anki Export

As a **the app**,
I want **to export MCQ exercises to Anki format**,
So that **users can study with Anki while the app matures**.

**Acceptance Criteria:**

**Given** MCQ exercises are loaded in the app
**When** I run `python backend/scripts/export_anki.py`
**Then** an Anki deck file (`.apkg` or JSON) is created
**And** the deck contains question, options, correct answer, explanation
**And** `GET /api/export/anki` can serve the export (for convenience)

---

### Story 2.5: Implement Domain Tagging & Filtering

As a **a student**,
I want **to filter exercises by domain and difficulty**,
So that **I can practice weak areas**.

**Acceptance Criteria:**

**Given** exercises are loaded with domain tags (Incremental Data Processing, ELT, etc.)
**When** I call `GET /api/exercises?domain=Incremental%20Data%20Processing&difficulty=medium`
**Then** only exercises with that domain and difficulty are returned
**And** if domain doesn't match the canonical list, validation flags it

---

### Story 3.1: Create SessionSelect Page

As a **a student**,
I want **to filter exercises and start a practice session**,
So that **I can choose what to study**.

**Acceptance Criteria:**

**Given** I open the app in my browser
**When** I see the SessionSelect page
**Then** I can select a domain from a dropdown (all Associate domains listed)
**And** I can select difficulty (easy/medium/hard)
**And** a "Start Session" button creates a session and navigates to MCQPractice

---

### Story 3.2: Create Session Context

As a **the app**,
I want **to manage session state across pages**,
So that **exercises persist while navigating**.

**Acceptance Criteria:**

**Given** a session is started
**When** SessionContext is created
**Then** it holds: `exercises[]`, `currentIndex`, `selectedAnswers{}`, `feedback`
**And** React hooks can consume the context (`useSession()`)
**And** state updates are immutable (no direct mutations)

---

### Story 3.3: Create MCQPractice Page & Display Question

As a **a student**,
I want **to see one exercise at a time**,
So that **I can focus on answering**.

**Acceptance Criteria:**

**Given** a session is active
**When** I navigate to MCQPractice
**Then** I see the current exercise's question
**And** any code snippet in the question renders in monospace with syntax highlighting (Prism.js)
**And** the domain and difficulty are shown
**And** I see a progress indicator (e.g., "Question 3 of 10")

---

### Story 3.4: Implement Answer Selection & Submission

As a **a student**,
I want **to select answer(s) and submit**,
So that **the app can tell me if I'm right**.

**Acceptance Criteria:**

**Given** I'm viewing an MCQ
**When** it's single-select, I see radio buttons for each option
**And** it's multi-select, I see checkboxes
**And** I can change my selection before submitting
**When** I click "Submit", my answer is sent to the backend
**Then** the backend evaluates correctness (all-or-nothing for multi-select)

---

### Story 3.5: Implement Feedback Display

As a **a student**,
I want **to see whether my answer was correct + an explanation**,
So that **I learn why**.

**Acceptance Criteria:**

**Given** I've submitted an answer
**When** the backend returns correctness + explanation
**Then** I see "Correct! ✓" or "Incorrect ✗" in clear color
**And** the correct option(s) are highlighted
**And** the Explanation is shown below (why correct, why distractors are wrong)
**And** reference links open in a new tab when clicked

---

### Story 3.6: Implement Session Navigation & Summary

As a **a student**,
I want **to move to the next question and see my score**,
So that **I progress through the session**.

**Acceptance Criteria:**

**Given** I've reviewed feedback
**When** I click "Next", I advance to the next exercise
**And** after the last exercise, I see the session summary
**Then** the summary shows: total correct/total, and per-domain breakdown
**And** I can start a new session from there

---

### Story 3.7: Add Syntax Highlighting with Prism.js

As a **the app**,
I want **code snippets to be highlighted**,
So that **code is readable**.

**Acceptance Criteria:**

**Given** an exercise has a code snippet
**When** it's rendered
**Then** Prism.js highlights the syntax based on language (SQL, Python, etc.)
**And** whitespace and indentation are preserved

---

### Story 4.1: Create CodeCompletion Page & Template Display

As a **a student**,
I want **to see a code template with a blank to fill**,
So that **I can practice syntax**.

**Acceptance Criteria:**

**Given** I open a Code-Completion exercise
**When** the page loads
**Then** I see the prompt (e.g., "Configure Auto Loader to infer schema")
**And** the code template with the blank marked clearly (e.g., `___`)
**And** the target language is shown
**And** an input field is ready for me to type

---

### Story 4.2: Implement Code Tokenizer

As a **the app**,
I want **to tokenize code for feedback**,
So that **I can give per-token feedback**.

**Acceptance Criteria:**

**Given** a user types code into the input
**When** tokenization happens
**Then** the tokenizer splits the code into tokens (keywords, identifiers, operators, literals)
**And** tokenization is language-specific (SQL case-insensitive, PySpark case-sensitive)
**And** non-semantic whitespace is ignored

---

### Story 4.3: Implement Positional Feedback Algorithm

As a **the app**,
I want **to compute green/yellow/grey feedback**,
So that **users get Wordle-style hints**.

**Acceptance Criteria:**

**Given** the user types code and submits
**When** the feedback algorithm runs
**Then** each token is colored: green (correct position), yellow (in answer, wrong position), grey (not in answer)
**And** feedback is computed in < 100ms (client-side)
**And** alternative accepted answers are matched correctly

---

### Story 4.4: Implement FeedbackTokens Rendering

As a **a student**,
I want **to see colored feedback on my attempt**,
So that **I understand what's right and what's wrong**.

**Acceptance Criteria:**

**Given** I've submitted a code attempt
**When** feedback is computed
**Then** my code renders with tokens colored green/yellow/grey
**And** I can see the remaining attempts counter
**And** if I've exhausted attempts, the canonical answer is revealed

---

### Story 4.5: Implement Guess Limit & Answer Reveal

As a **a student**,
I want **a bounded number of attempts**,
So that **I'm motivated to think before typing**.

**Acceptance Criteria:**

**Given** I start a code-completion exercise
**When** I make an attempt
**Then** the remaining attempts counter decreases
**And** when attempts reach zero, the canonical answer is revealed
**And** the explanation is shown
**And** I can move to the next exercise

---

### Story 4.7: Exercise-Type Filter (multiselect, MCQ default)

As a **a student**,
I want **to choose which exercise type(s) a session includes — multiple choice, code completion, or both — with multiple choice selected by default**,
So that **I can drill the Wordle-style code-completion exercises directly instead of hunting for them interleaved among dozens of MCQs**.

(Added 2026-06-09; full story file: `_bmad-output/implementation-artifacts/4-7-exercise-type-filter.md`. Closes the code-completion discoverability gap — the runner is useless if users can't reach a drill.)

**Acceptance Criteria:**

**Given** the Start screen
**When** I view the filters
**Then** an **Exercise type** multiselect lists **Multiple choice** + **Code completion**, with **Multiple choice checked by default**
**And** I can scope a session to Code completion (and/or uncheck Multiple choice)
**When** I start a Code-completion-scoped session
**Then** it contains only code-completion exercises (routed to the `CodeCompletion` runner) and the live match count reflects the selected type(s)
**And** `GET /api/sessions` + `GET /api/exercises/count` accept a **repeatable** `exercise_type` param (any-of), validated against `ExerciseType`
**And** empty selection means "all types" (never blocks); pytest + vitest cover the default, type-scoped sessions/counts, multi-value any-of, and invalid-type rejection

**Status:** implemented + code-reviewed 2026-06-10, in `review`.

---

### Story 4.8: Character-Level Feedback + Skip

As a **a student**,
I want **per-letter (Wordle-style) feedback and a Skip button**,
So that **the code-completion drill actually narrows toward the answer and I'm never trapped exhausting attempts**.

(Added 2026-06-10 via correct-course; Sprint Change Proposal `sprint-change-proposal-2026-06-10.md`; decision-log #54/#55. **Reverses** the token-level feedback of stories 4.3/4.4 and extends 4.5's loop. Full story file: `_bmad-output/implementation-artifacts/4-8-character-level-feedback-and-skip.md`.)

**Acceptance Criteria:**

**Given** a code-completion exercise
**When** I submit a guess
**Then** feedback is rendered **per character** — green (right letter, right place) / yellow (letter in the answer, wrong place) / grey (not in the answer), with two-pass duplicate-letter handling, computed client-side < 100ms
**And** it honors `case_sensitive` (per-character compare) and `ignore_whitespace`, and scores against the best of `[canonical, ...accepted]` (FR-16)
**And** `FeedbackTokens` renders per-character tiles, color-independent (glyph/aria-label + a `role="status"` summary)
**When** I press **Skip**
**Then** the runner advances to the next exercise **without revealing** the answer or explanation (distinct from solve/exhaustion, which reveal)
**And** the **6-guess cap** (`CODE_COMPLETION_MAX_ATTEMPTS`) is retained, with auto-reveal on exhaustion and reveal on solve
**And** the regex `tokenizer.js` (+ its test) is **removed** (no longer used for feedback); `utils/language.js` stays
**And** `codeFeedback`/`FeedbackTokens`/`CodeCompletion` tests are updated for character-level + Skip; `tokenizer.test.js` is deleted; suites green

**FRs/ARs covered:** FR-14 (now character-level), FR-15 (+ Skip), FR-16, NFR-1; supersedes AR-9.

**Priority:** Lands before Epic 4 merges (improves the in-review runner). No backend change; no content change (answers are already single words).

---

<!-- ===================== EPIC 5: MCQ Variety & Randomization (TOP PRIORITY) ===================== -->

### Story 5.1: Option Pool Model & Validation

As a **content author**,
I want **the MCQ model to accept an Option Pool with at least 1 correct and at least 3 incorrect options (interchangeable correct alternatives allowed)**,
So that **I can author extra options for variety while guaranteeing a valid 1-correct + 3-distractor display**.

**Acceptance Criteria:**

**Given** a `single_choice` exercise in `backend/app/models.py`
**When** it is validated
**Then** validation passes only if it has ≥1 option with `correct: true` and ≥3 with `correct: false`
**And** more than one `correct: true` option is allowed and treated as interchangeable alternatives (the legacy "exactly one correct" rule is relaxed)
**And** `multi_choice` is rejected with a clear message
**And** a pool failing the ≥1/≥3 floor raises a validation error naming the rule and the exercise `id`
**And** existing single-correct exercises with ≥3 distractors still validate
**And** `pytest` tests in `backend/tests/` cover the new rules (managed via `uv`)

---

### Story 5.2: Migrate Legacy multi_choice Content

As a **content author**,
I want **the two legacy `multi_choice` items reworked into single-select pools**,
So that **the corpus is consistent with the single-select-only decision**.

**Acceptance Criteria:**

**Given** `dbx-de-0009` and `dbx-de-0027` in `exercises/associate/mcq-associate-batch-01.yaml`
**When** I rework them
**Then** each becomes `type: single_choice` with ≥1 correct and ≥3 incorrect options (jointly-correct sets rewritten as single-correct or pooled interchangeable alternatives)
**And** both load and pass the Story 5.1 validation
**And** no `multi_choice` items remain anywhere in `exercises/`
**And** the explanations are updated to match the reworked options

---

### Story 5.3: Server-Side Session Randomizer

As a **the app**,
I want **a session builder that samples 1 correct + 3 incorrect options per MCQ, shuffles their positions, and randomizes exercise order — emitting options without `correct` flags**,
So that **re-study feels fresh and answers are never leaked to the client**.

**Acceptance Criteria:**

**Given** a loaded MCQ Option Pool
**When** the randomizer builds a Displayed-Option set (in `backend/app/content.py` or `session.py`)
**Then** it returns exactly 4 options: exactly 1 sampled from the correct set and 3 sampled from the incorrect set
**And** the 4 options are in randomized position order (correct option not position-stable across calls)
**And** no `correct` field is present on the emitted options
**And** a list of exercises is returned in randomized order (FR-21)
**And** sampling is uniform-at-random with no seed / no anti-repeat memory
**And** `pytest` tests assert the 1-correct/3-incorrect composition, flag stripping, and that repeated calls vary

---

### Story 5.4: GET /api/sessions Endpoint

As a **the frontend**,
I want **`GET /api/sessions?domain&difficulty` to return an order-randomized session of flag-less Displayed Options**,
So that **the runner can present questions without ever receiving the answers**.

**Acceptance Criteria:**

**Given** the backend is running with loaded content
**When** I call `GET /api/sessions?domain=...&difficulty=...`
**Then** the response uses the standard `{success, data, error}` wrapper
**And** `data` is a list of `{exerciseId, domain, difficulty, question, codeContext?, displayedOptions:[{id,text}×4]}` in randomized order
**And** the options carry no `correct` flags (verified in the payload)
**And** filters are respected and an empty result returns an empty list (not an error)
**And** the endpoint uses the Story 5.3 randomizer

---

### Story 5.5: POST /api/feedback Single-Select Scoring

As a **the frontend**,
I want **to submit `{exerciseId, displayedOptionIds, selectedId}` and receive `{correct, correctOptionId, explanation, references}`**,
So that **correctness is graded server-side against exactly the options the user saw**.

**Acceptance Criteria:**

**Given** a submitted answer
**When** `POST /api/feedback` is called with the displayed option ids and the selected id
**Then** `correct` is true iff `selectedId` is the displayed correct option
**And** the response includes `correctOptionId`, `explanation`, and `references`
**And** the former multi-select all-or-nothing scoring path is removed (old FR-9)
**And** a request whose `displayedOptionIds` don't match a known sampling is rejected with a clear error
**And** `pytest` tests cover correct, incorrect, and malformed submissions

---

### Story 5.6: Single-Select MCQ Runner (Frontend Refactor)

As a **a student**,
I want **the practice screen to show the 4 server-supplied options as single-select and grade via the API**,
So that **I get fair single-select questions with fresh options each session**.

**Acceptance Criteria:**

**Given** an active session loaded from `GET /api/sessions`
**When** I view a question in `frontend/src/pages/MCQPractice.jsx`
**Then** the 4 Displayed Options render as a single-select radio group (no checkbox / multi-select path remains)
**And** selecting an option then submitting calls `POST /api/feedback` with `displayedOptionIds` + `selectedId`
**And** correctness, the correct option, and the explanation render from the API response (the client no longer grades locally and holds no `correct` flags)
**And** malformed/unsupported exercises still degrade gracefully (no white-screen)
**And** existing frontend tests are updated to the single-select + API-graded flow

---

<!-- ===================== EPIC 6: Session Control & Study QoL ===================== -->

### Story 6.1: Match Count Endpoint & Start-Screen Preview

As a **a student**,
I want **to see how many questions match my filters before I start**,
So that **I can right-size a session instead of starting blind**.

**Acceptance Criteria:**

**Given** the backend is running
**When** I call `GET /api/exercises/count?domain=...&difficulty=...`
**Then** it returns `{count}` only — no options, pools, or `correct` flags (leak-free)
**And** in `frontend/src/pages/SessionSelect.jsx` the count updates live as I change domain/difficulty ("{n} questions match")
**And** when the count is 0 the Start button is disabled with a clear empty-state message
**And** tests cover the endpoint and the live-count UI

---

### Story 6.2: Session-by-IDs Endpoint (Replay)

As a **the frontend**,
I want **`POST /api/sessions {exerciseIds}` to build a fresh session for a specific set of exercises**,
So that **"Restart" and "Practice these again" re-sample options and re-randomize order rather than replaying identical questions**.

**Acceptance Criteria:**

**Given** a list of exercise ids
**When** I call `POST /api/sessions` with `{exerciseIds:[...]}`
**Then** the response shape matches `GET /api/sessions` (flag-less Displayed Options, randomized order)
**And** the Displayed Options are freshly sampled/shuffled (can differ from a prior presentation of the same exercise)
**And** unknown ids are dropped and logged, not fatal
**And** it reuses the Story 5.3 randomizer
**And** tests cover a known id set, freshness across calls, and unknown-id handling

---

### Story 6.3: Session State — Feedback Retention, Back, Skip, End-to-Summary

As a **the app**,
I want **the session store to retain each feedback response and support back/skip/early-end**,
So that **revisit, review, and partial results work without re-grading**.

**Acceptance Criteria:**

**Given** the session reducer in `frontend/src/context/SessionContext.jsx`
**When** an answer is submitted
**Then** `feedback[exerciseId]` stores the full `{correct, correctOptionId, explanation, references}` response
**And** a `prev` action moves back to an earlier question shown read-only (no re-submit, no re-POST)
**And** a `skip` action advances without grading and records the question as *unanswered* (not incorrect)
**And** an `endToSummary` action ends the session early and computes the Summary over the answered subset
**And** per-question state is tracked as `unanswered | answered | skipped` and session state as `active | ended-early | completed`
**And** tests cover retention, back read-only, skip accounting, and partial summary

---

### Story 6.4: End Session, Exit Confirm & Home

As a **a student**,
I want **to end or leave a session at any time, with a confirmation and the option to see partial results**,
So that **I'm never trapped in a session and don't lose progress by accident**.

**Acceptance Criteria:**

**Given** I'm in an active practice session
**When** I activate the persistent "End session" control (or click the header title = Home)
**Then** an Exit-confirm modal appears offering *See results*, *Discard & exit*, *Keep practicing* (unless zero questions are answered, which exits straight to Start)
**And** *See results* routes to a partial Summary via `endToSummary` (Story 6.3)
**And** *Discard & exit* returns to the Start screen
**And** the modal is focus-trapped, labeled, Esc-dismissible (= Keep practicing), and restores focus to the trigger on close
**And** tests cover each action and the zero-answered shortcut

---

### Story 6.5: Progress Bar, Navigation Controls & Keyboard Shortcuts

As a **a student**,
I want **a progress bar with running score, back/skip controls, and keyboard shortcuts**,
So that **I can drill quickly and stay oriented**.

**Acceptance Criteria:**

**Given** an active session in `MCQPractice.jsx`
**When** I practice
**Then** a visual progress bar shows my position and a running correct count, updating on submit and navigation
**And** Back (read-only revisit) and Skip controls are available and wired to the Story 6.3 actions
**And** keyboard shortcuts work: `1`–`4`/`a`–`d` select, `Enter` submit-then-advance, `←`/`→` back/next, `Esc` opens/closes the Exit-confirm — all with pointer parity
**And** focus is visible on every control, and the result/progress are announced via `aria-live`
**And** progress-bar motion respects `prefers-reduced-motion`
**And** tests cover progress display, keyboard selection/submit/nav, and accessibility attributes

---

### Story 6.6: Summary Review & Replay

As a **a student**,
I want **to review the questions I missed and replay sets**,
So that **I can target my weak spots and re-drill**.

**Acceptance Criteria:**

**Given** I reach the Summary (complete or partial)
**When** the Summary renders in `frontend/src/pages/Summary.jsx`
**Then** a Review-incorrect list shows each missed question with its correct option and explanation (from the retained feedback, Story 6.3)
**And** "Practice these N again" starts a fresh session of just the missed exercises via `POST /api/sessions {exerciseIds}` (Story 6.2)
**And** "Restart this session" replays the full exercise set fresh via the same endpoint
**And** a partial Summary surfaces answered and skipped counts
**And** the existing "Start a new session" action is retained
**And** tests cover review-incorrect, practice-again, restart, and partial counts

---

### Story 6.7: Exam Filter & Session Scoping

As a **a student**,
I want **to choose which exam (Associate or Professional) I'm practicing and have domains scoped to it**,
So that **a session never mixes Associate and Professional questions now that both content sets exist**.

**Acceptance Criteria:**

**Given** the corpus now contains both Associate (72) and Professional (60) exercises
**When** I open the Start screen (`frontend/src/pages/SessionSelect.jsx`)
**Then** I can select an **exam** (Associate | Professional), and the Domain dropdown lists only that exam's domains
**And** `GET /api/sessions` and `GET /api/exercises/count` accept an `exam` query param that filters the corpus by exam
**And** starting a session with `exam=associate` yields only Associate exercises (and likewise for professional)
**And** with no exam selected the behavior is defined and documented (default to one exam rather than silently mixing)
**And** the match count (Story 6.1) reflects the selected exam
**And** backend filtering reuses the existing `filter_exercises` exam support; the frontend `DOMAINS` constant is organized per-exam
**And** tests cover exam filtering on both endpoints and the per-exam domain UI

---

<!-- ===================== EPIC 7: Answer & Stats Tracking ===================== -->

### Story 7.1: SQLite Attempt Store

As a **the app**,
I want **a local SQLite store for the learner's answer history**,
So that **progress persists across restarts and powers stats, readiness, and unseen-first**.

**Acceptance Criteria:**

**Given** the backend starts
**When** the app initializes (lifespan)
**Then** a new `backend/app/store.py` (using stdlib `sqlite3`, **no pip**) creates an `attempts` table if absent at a gitignored local path (`backend/data/progress.db`)
**And** the schema is `attempts(id INTEGER PK, exercise_id, exam, domain, correct, selected_id, time_taken_ms, answered_at)`
**And** `store.py` exposes helpers: `record_attempt(...)`, `attempted_ids(filters)`, `last_seen_map(filters)`, `overall_stats(...)`, `domain_accuracy(...)`
**And** `backend/data/` is added to `.gitignore`
**And** `pytest` tests (using a temp DB) cover create-if-absent, record, and each query helper

---

### Story 7.2: Record Attempts on Feedback

As a **a student**,
I want **every answer I submit to be recorded**,
So that **my history is captured automatically as I practice**.

**Acceptance Criteria:**

**Given** the SQLite store (Story 7.1) exists
**When** `POST /api/feedback` grades an answer
**Then** it records an attempt (`exercise_id`, `exam`, `domain`, `correct`, `selected_id`, `time_taken_ms`, `answered_at`) via `store.record_attempt`
**And** the request accepts an optional `timeTakenMs` field (FR-28) and stores it (null if absent)
**And** a store-write failure is logged and does **not** break grading (best-effort; the feedback response is unchanged)
**And** `pytest` tests assert an attempt row is written on feedback and that a store error still returns a normal feedback response

---

### Story 7.3: Unseen-First Session Ordering

As a **a student**,
I want **questions I haven't answered yet served before ones I've already done**,
So that **I cover new material before repeating myself**.

**Acceptance Criteria:**

**Given** a filtered set for `GET /api/sessions` and recorded history
**When** the session is built
**Then** not-yet-answered Exercises (within the filters) are ordered before seen ones; within the unseen group order is randomized
**And** when all matching Exercises are seen, the session still proceeds, ordered least-recently-seen first (no empty/blocked state)
**And** option sampling/position-shuffle (FR-20) remain random and unchanged
**And** this supersedes FR-21's pure-random ordering; `pytest` tests cover unseen-first, the all-seen fallback, and that sampling stays random

---

### Story 7.4: Stats & Readiness Endpoints

As a **the frontend**,
I want **stats and readiness endpoints over the attempt history**,
So that **the dashboard and readiness indicator have data**.

**Acceptance Criteria:**

**Given** recorded attempts
**When** I call `GET /api/stats`
**Then** it returns overall accuracy + attempt count, per-Domain accuracy/attempts, and a trend series, in the `{success,data,error}` wrapper (optional `exam` filter)
**When** I call `GET /api/readiness`
**Then** it returns rolling-window accuracy vs the ~70% bar, overall + per-Domain readiness
**And** both reflect only answered attempts and are leak-free (no `correct` flags from content)
**And** `pytest` tests cover both endpoints incl. the empty-history case

---

### Story 7.5: Stats Dashboard & Readiness Indicator (Frontend)

As a **a student**,
I want **to see my accuracy, weak areas, and readiness**,
So that **I know what to study next**.

**Acceptance Criteria:**

**Given** the stats/readiness endpoints (Story 7.4)
**When** I open the stats view
**Then** `frontend/src/pages/StatsDashboard.jsx` shows overall + per-Domain accuracy, attempts, and a trend, with weak Domains visually distinct
**And** a `ReadinessIndicator` component shows readiness vs ~70% overall and per-Domain (guidance, not a guarantee)
**And** `api.js` gains `getStats()` / `getReadiness()`; the view is reachable from the app shell
**And** vitest tests mock the api and cover the dashboard + indicator rendering (incl. empty state)

---

<!-- ===================== EPIC 8: Timed Practice / Mock Exam ===================== -->

### Story 8.1: Session Countdown Timer (Frontend)

As a **a student**,
I want **an optional countdown on a practice session**,
So that **I can train under time pressure**.

**Acceptance Criteria:**

**Given** the Start screen
**When** I enable a timer and start a session
**Then** a `Timer`/`Countdown` component shows remaining time and decrements; at zero the session auto-ends to the (partial) Summary via `endToSummary`
**And** with the timer off, behavior is unchanged from the untimed runner
**And** the timer respects `prefers-reduced-motion` and is announced accessibly
**And** vitest tests cover countdown display, auto-end at zero, and timer-off parity

---

### Story 8.2: Per-Question Timing

As a **the app**,
I want **to measure how long each answer takes**,
So that **timing feeds the stats and the timed experience**.

**Acceptance Criteria:**

**Given** an MCQ is presented
**When** the user submits
**Then** the client measures elapsed time for that question and sends `timeTakenMs` with `POST /api/feedback` (recorded by Story 7.2)
**And** timing is per-question (reset on advance), not whole-session
**And** vitest tests assert `submitFeedback` is called with a numeric `timeTakenMs`

---

### Story 8.3: Mock-Exam Builder (Backend)

As a **a student**,
I want **a full-length, domain-weighted exam scoped to one exam level**,
So that **I can rehearse the real test**.

**Acceptance Criteria:**

**Given** `GET /api/sessions?mode=mock&exam=...`
**When** a mock exam is built
**Then** it assembles a domain-weighted, full-length set scoped to that Exam (Associate ≈45Q/90min, Pro ≈59Q/120min per addendum §C weights), **ignoring** unseen-first (representative, may repeat seen)
**And** the response stamps the exam `durationMinutes` and otherwise matches the session shape (flag-less Displayed Options)
**And** it never mixes exams (respects the exam filter)
**And** `pytest` tests cover sizing/weighting per exam, duration stamping, exam-scoping, and that unseen-first is not applied

---

### Story 8.4: Mock-Exam Flow & Result (Frontend)

As a **a student**,
I want **to take a timed mock exam end-to-end and see an exam-style score**,
So that **I get a realistic readiness check**.

**Acceptance Criteria:**

**Given** the mock-exam builder (8.3) and timer (8.1)
**When** I choose "Mock Exam" for an Exam on the Start screen
**Then** `frontend/src/pages/MockExam.jsx` (or a SessionSelect mode) starts the domain-weighted set under the exam's countdown, auto-submitting at zero
**And** at the end an exam-style result shows overall score vs the ~70% bar plus the per-Domain breakdown (reusing Story 6.6 / Story 7 stats)
**And** the mock run records attempts like any session (Story 7.2)
**And** vitest tests cover starting a mock, the countdown/auto-submit, and the result screen

---

<!-- ===================== EPIC 9: Multi-Provider / Multi-Certification ===================== -->

### Story 9.1: Per-Certification Config Model & Loader

As a **content author / the app**,
I want **a file-based YAML registry of Providers and Certifications loaded and validated at startup**,
So that **each Certification's domains, weights, and exam parameters are configuration, not hardcoded enums**.

**Acceptance Criteria:**

**Given** a YAML config (e.g. `config/certifications.yaml` or one file per certification) authored as `providers[] → certifications[] → {id, name, total_questions, duration_minutes, pass_bar, domains:[{name, weight}]}`
**When** the FastAPI app starts
**Then** a Pydantic `Certification`/`Provider` model parses and validates the registry (weights sum to ~100 per certification; ids unique; required fields present), failing loudly with the offending file + certification id on malformed config
**And** the seed config re-expresses today's literals: Databricks Associate (`id: associate`, 45Q / 90min / pass_bar 0.70) and Professional (`id: professional`, 59Q / 120min / pass_bar 0.70) with their current per-domain weights (addendum §C / §G)
**And** the loaded registry is exposed to the rest of the backend (e.g. a `certifications` accessor keyed by certification id)
**And** `pytest` tests (via `uv`) cover successful load, validation failure cases, and that the seed config's domains/weights/exam params **match the current `MOCK_EXAM_CONFIGS` and `Domain` values verbatim**

---

### Story 9.2: Make Domains & Mock Params Config-Driven (Backend)

As a **the app**,
I want **the `ExamType`/`Domain` enums and `MOCK_EXAM_CONFIGS` to be derived from the loaded config registry instead of literal code**,
So that **a new Certification needs only content + config, with no Databricks DE regression**.

**Acceptance Criteria:**

**Given** the config registry from Story 9.1
**When** the backend resolves valid exams, valid domains, and mock parameters
**Then** the allowed `exam` values and the per-exam canonical Domain list are read from the registry (the `Domain` enum is replaced/backed by config-derived values), and `exam` is retained as the Certification id (no field rename)
**And** `backend/app/session.py`'s `MOCK_EXAM_CONFIGS` (`total_questions`, `duration_minutes`, `domain_weights`) is built from the registry rather than literals; the largest-remainder mock builder reads the derived config
**And** the session/mock builder, unseen-first ordering, and stats continue to key on `(certification, domain)` exactly as they keyed on `(exam, domain)` before
**And** **all existing backend tests stay green** (guardrail: no Databricks DE regression in sizing/weighting/timing/filtering)
**And** `pytest` tests cover config-driven mock sizing and domain-weighting per Certification (Associate 45 / Professional 59), driven from a test config

---

### Story 9.3: GET /api/certifications + Config-Driven Frontend

As a **the frontend**,
I want **a `GET /api/certifications` endpoint and a Start screen that reads its exam/domain taxonomy from it**,
So that **adding a Certification requires no frontend edit**.

**Acceptance Criteria:**

**Given** the backend is running with the loaded registry
**When** I call `GET /api/certifications`
**Then** it returns the Provider/Certification registry (providers → certifications → {id, name, exam params, domains}) in the standard `{success, data, error}` wrapper
**And** `frontend/src/constants.js` `EXAMS`/`DOMAINS_BY_EXAM` are no longer hand-maintained — the values are **fetched** from `GET /api/certifications` (e.g. via `api.js`)
**And** `SessionSelect`'s exam selector renders from the fetched config (keep the existing flat exam dropdown wired to the config this iteration; the polished Provider→Certification switcher UI is **deferred**), and the Domain dropdown scopes to the selected exam's configured domains
**And** vitest tests mock the api and cover fetched-config rendering plus the empty/error state (no certifications / fetch failure degrades gracefully, no white-screen)

---

### Story 9.4: Certification-Scoped Validation & Content Mapping

As a **content author / the app**,
I want **each Exercise's `domain` validated against its Certification's configured domain list, and the Databricks DE content mapped to its Certifications**,
So that **content stays blueprint-aligned per Certification (FR-4) as more Certifications are added**.

**Acceptance Criteria:**

**Given** the config-driven domain lists (Story 9.2) and loaded exercises
**When** content is validated at load
**Then** an Exercise whose `domain` is not in its Certification's configured domain list is flagged with a clear message naming the file, Exercise `id`, certification, and the offending domain (extends the current Domain-enum check; ties FR-4)
**And** the existing Databricks DE content maps correctly to the Associate and Professional Certifications (their `exam` values resolve to the configured Certifications)
**And** the content-path layout decision is documented (OQ-7): **keep the current `exercises/associate|professional/` paths this iteration** and map `exam` values to Certifications via config (no physical reorganization)
**And** `pytest` tests cover unknown-domain-for-certification flagging and that all bundled Databricks DE exercises pass certification-scoped validation

---

### Story 9.5: Rebranding to "Cert Study Companion"

As a **a user**,
I want **the user-facing product name to be the generic "Cert Study Companion" with Databricks DE shown as the bundled certification**,
So that **the app reads as provider-agnostic without disrupting the codebase**.

**Acceptance Criteria:**

**Given** the user-facing surfaces
**When** I view the app shell, the README, and the browser tab
**Then** the frontend app-shell title/headings, `README.md`, and `frontend/index.html` `<title>` use the generic product name "Cert Study Companion"
**And** Databricks DE is presented as the (currently the only) bundled Certification, not the product identity
**And** **no folder, path, or `project_name` renames** are made (the repo/dir names and artifact ids are unchanged this iteration)
**And** tests and snapshots that assert the old title/heading are updated to the new name

---

<!-- ===================== EPIC 10: Containerization & Sharing ===================== -->

### Story 10.1: Backend Dockerfile

As a **a colleague with only Docker installed**,
I want **a backend image that installs its own dependencies and serves the API**,
So that **the backend runs with no host Python**.

**Acceptance Criteria:**

**Given** `backend/Dockerfile`
**When** I build it
**Then** it uses a Python 3.10+ base, installs dependencies (via `uv` or `pip install -r requirements.txt`), copies `backend/`, and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
**And** a `.dockerignore` excludes `__pycache__`, `.venv`, `backend/data/`, and other non-build files
**And** the built image starts and serves `/api/*` (e.g. `GET /api/certifications` / `GET /api/exercises`) with no host Python toolchain present
**And** SQLite needs no service dependency (stdlib `store.py`)

---

### Story 10.2: Frontend Dockerfile & Static Serve

As a **a colleague with only Docker installed**,
I want **a frontend image that builds the React app and serves it, proxying API calls to the backend**,
So that **the UI runs with no host Node beyond the image's build stage**.

**Acceptance Criteria:**

**Given** `frontend/Dockerfile`
**When** I build it
**Then** it is multi-stage: a Node build stage runs `npm ci && npm run build`, and a final stage statically serves `dist/` (e.g. nginx or `vite preview`)
**And** `/api/*` requests are proxied to the backend service (replacing the Vite **dev** proxy from `vite.config.js`)
**And** the image builds and serves the app with no host Node beyond the build stage
**And** a `.dockerignore` excludes `node_modules` and build artifacts

---

### Story 10.3: docker-compose.yml & Persistence Volume

As a **a colleague**,
I want **`docker compose up` to bring up both services with my answer history persisting across restarts**,
So that **I can run and re-run the app without losing progress**.

**Acceptance Criteria:**

**Given** `docker-compose.yml` at the repo root
**When** I run `docker compose up`
**Then** it defines two services (`backend`, `frontend`) on a shared network, with `frontend` `depends_on` `backend`, and publishes a **documented local URL** (e.g. `http://localhost:3000`)
**And** a named or bind volume mounts the backend's `backend/data/` so `progress.db` lives outside the container layer
**And** answers recorded in one run **survive `docker compose down && docker compose up`** (a fresh volume simply starts empty via create-if-absent)
**And** the whole flow runs with **only Docker installed** (no host Node/Python/uv) — FR-31
**And** the acceptance explicitly verifies the persistence-across-restart and the only-Docker run path

---

### Story 10.4: Content Mount & README

As a **a colleague**,
I want **to add or edit content without rebuilding, and clear docs for the one-command flow**,
So that **the tool is self-serve for sharing**.

**Acceptance Criteria:**

**Given** the compose stack (Story 10.3)
**When** the backend service runs
**Then** `exercises/` and the §G certification config are **bind-mounted** into the backend so a colleague can add/edit content (drop YAML + config) and pick it up with a backend restart — no image rebuild (OQ-8)
**And** `README.md` documents the one-command flow: clone → `docker compose up` → open the URL, plus how to add content and where history is stored (the mounted volume)
**And** the README notes the out-of-scope items: TLS/reverse-proxy/hosting, accounts/auth, a shared backend DB, multi-user concurrency, and image-registry publishing
**And** the documented flow is verified end-to-end (clone-equivalent → compose up → reachable URL → add a content file → restart → it appears)

---

<!-- ===================== EPIC 11: Question Feedback & Content-Improvement Loop ===================== -->

### Story 11.1: In-App Question Feedback → Sidecar YAML

As a **a student**,
I want **to attach a free-text note to a question while I practice and have it saved**,
So that **bad/unclear questions get flagged for fixing without interrupting my study**.

(FR-32, AR-21 — PRD rev 6 §4.9, addendum §I. The develop-now story.)

**Acceptance Criteria:**

**Given** the practice surface (MCQ feedback panel and the Code-Completion conclusion)
**When** I open the "Flag / leave a note" affordance and submit a free-text note
**Then** the note is persisted to a sidecar `exercises/feedback.yaml`, keyed by the Exercise `id`, with a server-stamped `created_at` and `resolved: false`
**And** the authored Exercise YAML file is **byte-unchanged** (only the sidecar is written)
**And** submitting an empty/whitespace-only note is rejected (no entry written)
**And** a new `backend/app/feedback_store.py` exposes `add_note` / `notes_for` / `open_notes` / `mark_resolved` over the sidecar (create-if-absent), and a new `POST /api/exercise-feedback {exerciseId, note}` endpoint appends via it using the standard `{success, data, error}` wrapper and validates the `exerciseId` exists
**And** a feedback note survives an app restart (re-opening the Exercise's notes shows it)
**And** the new endpoint does NOT touch the MCQ `POST /api/feedback` grading path or the SQLite attempt store
**And** `pytest` covers add/list/open/resolve + the endpoint (incl. unknown-id and empty-note rejection); `vitest` covers the affordance calling the API and the empty-note guard

---

### Story 11.2: write-mcq Feedback-Driven Revision

As a **content author**,
I want **the write-mcq skill to revise flagged questions using their feedback and mark the feedback resolved**,
So that **real study friction turns into a steadily better content bank**.

(FR-33 — PRD rev 6 §4.9. Follows Story 11.1.)

**Acceptance Criteria:**

**Given** open (unresolved) feedback entries in `exercises/feedback.yaml`
**When** the `write-mcq` skill is run against an Exercise id (or sweeps `open_notes()`)
**Then** it reads the notes, edits the Exercise in its source YAML to fix the flagged issue, and re-validates against the Option Pool / domain rules (FR-1/FR-19)
**And** it marks the corresponding feedback entries `resolved` (or removes them) in the sidecar
**And** it only acts on Exercises with **open** feedback (resolved entries are skipped)
**And** the author reviews the change as a normal version-controlled diff (no approval UI)
**And** the skill is MCQ-first; a `write-code-completion` revision path is noted as a later extension

**Priority:** After Story 11.1 (needs the sidecar store it writes).

---
