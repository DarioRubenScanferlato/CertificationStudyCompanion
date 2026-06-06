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

**FR-21:** Randomize Exercise order per Practice Session — Exercises in a session are presented in randomized order, re-randomized fresh each session; no resume-in-order or SRS weighting in MVP. Computed server-side. *(New, PRD rev 2.)*

### Non-Functional Requirements

**NFR-1:** Code-Completion feedback latency — Positional Feedback must feel instant (target < 100ms from keystroke to rendered feedback); comparison is small and should be computable client-side.

**NFR-2:** Single-user, local, no persistence — Single-user local app with no accounts, no auth, no server-side user data; no persistence in MVP (session is ephemeral memory-only).

**NFR-3:** File-based content — No database; content is YAML files loaded at startup into memory.

**NFR-4:** Portable format — Exercise format is portable to Anki and other tools so studying is never blocked on app completion.

### Additional Requirements (Architecture & Technical)

**AR-1:** Frontend framework — React 18+ with Vite dev server for hot module reload and fast builds.

**AR-2:** Styling solution — Tailwind CSS for styling + custom React components (no heavy component library).

**AR-3:** Backend framework — Python 3.10+ with FastAPI for async, minimal, REST API.

**AR-4:** Content format — YAML-authored exercise files in `exercises/` directory at project root; optional JSON serving internally.

**AR-5:** API design — REST endpoints with standard response wrapper: `{success: bool, data: {...}, error: {...}}`.

**AR-6:** Error handling — Standard JSON error format with machine-readable error codes + user-friendly messages.

**AR-7:** State management — React Context + useState for session state (exercises list, current index, selected answers, feedback).

**AR-8:** Code rendering — Prism.js for syntax highlighting in exercise display.

**AR-9:** Code tokenization — Regex-based tokenizer (language-specific) for Code-Completion token-level feedback (Phase 2).

**AR-10:** Development workflow — Concurrent dev servers (frontend on 3000 proxying `/api/*` to backend on 8000).

**AR-11:** Testing — Tests co-located with source files (`.test.jsx`, `.test.py`); frontend: Vitest/Jest; backend: pytest.

**AR-12:** Naming conventions — PascalCase for React components, camelCase for JS functions/variables, lowercase plural for API endpoints, camelCase for JSON fields.

**AR-13:** Server-side session randomizer — A stateless, non-deterministic (per-request) component in `content.py`/`session.py` performs option-pool sampling, option-position shuffle, and exercise-order randomization; standard-library RNG, no seed/anti-repeat memory in MVP. (Architecture rev 2.)

**AR-14:** Session API contract — `GET /api/sessions` is the runner entry point, returning order-randomized exercises each with 4 flag-less Displayed Options (`{id, text}`); `GET /api/exercises` is demoted to admin/debug so pools/correct flags never reach the practice UI. `POST /api/feedback` takes `{exerciseId, displayedOptionIds, selectedId}` and returns `{correct, correctOptionId, explanation, references}`. (Architecture rev 2.)

**AR-15:** Pydantic Option Pool validation — `models.py` enforces ≥1 correct / ≥3 incorrect for `single_choice`; the legacy "single_choice ⇒ exactly one correct" rule is relaxed to allow interchangeable alternatives; `multi_choice` is rejected. (Architecture rev 2.)

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
| FR-21 | Epic 5 | Randomized Exercise order per session |

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

### Epic 4: Code-Completion Practice (Phase 2)
Implement the Wordle-style code-completion exercises for syntax drilling.

**What users accomplish:** Practice code syntax with interactive feedback, see token-level green/yellow/grey feedback as they type, learn syntax through the playful guess-and-narrow loop, see explanations and canonical answers.

**FRs/ARs covered:** FR-13, FR-14, FR-15, FR-16, FR-17, NFR-1, AR-9

**Priority:** Phase 2 — after the exam-critical work (Epic 5, Epic 6).

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
