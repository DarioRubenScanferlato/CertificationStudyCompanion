---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/addendum.md
  - /Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/architecture.md
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

**FR-7:** Select answer(s) and submit — User selects one (single-select) or multiple (multi-select) Options with clear UI affordance (radio vs checkbox).

**FR-8:** Immediate correctness feedback — On submit, app indicates whether answer was correct and which Option(s) were correct.

**FR-9:** Defined multi-select scoring — Multi-select MCQs are scored all-or-nothing (every correct Option selected and no incorrect Option selected = correct).

**FR-10:** Show Explanation after answering — After submit, app shows Explanation with why-correct and why-distractor-wrong rationale, plus reference link(s).

**FR-11:** Advance through the session — User can move to next Exercise after reviewing feedback until session is complete.

**FR-12:** End-of-session summary — Session end shows simple summary: number correct / total, and per-Domain breakdown when session spans multiple Domains.

**FR-13:** Present a Code-Completion Exercise — App presents prompt, code template with blank/slot clearly indicated, and input affordance. (Phase 2)

**FR-14:** Accept a typed attempt and give Positional Feedback — On attempt, app evaluates against canonical answer and renders Positional Feedback (< 100ms target). (Phase 2)

**FR-15:** Limited guesses with reveal — User has bounded number of attempts; on solving or exhausting attempts, canonical answer is revealed. (Phase 2)

**FR-16:** Accept valid alternative answers — Authored alternative correct phrasings are treated as correct. (Phase 2)

**FR-17:** Show Explanation after Code-Completion Exercise — Explanation and references shown once exercise concludes. (Phase 2)

**FR-18:** Portable / exportable content — Exercise format is portable enough that MCQ content can be consumed by existing study tool (Anki); conversion preserves question, options, correct answer(s), and Explanation.

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

### FR Coverage Map

| FR | Epic | Capability |
|----|------|------------|
| FR-1 | Epic 2 | Standardized exercise format |
| FR-2 | Epic 2 | App loads exercise files at startup |
| FR-3 | Epic 2 | Fail clearly on malformed content |
| FR-4 | Epic 2 | Blueprint-aligned domain tagging |
| FR-5 | Epic 3 | Start practice session with filters |
| FR-6 | Epic 3 | Present one MCQ at a time |
| FR-7 | Epic 3 | Select answer(s) and submit |
| FR-8 | Epic 3 | Immediate correctness feedback |
| FR-9 | Epic 3 | Multi-select scoring (all-or-nothing) |
| FR-10 | Epic 3 | Show explanation after answering |
| FR-11 | Epic 3 | Advance through session |
| FR-12 | Epic 3 | End-of-session summary |
| FR-13 | Epic 4 | Present code-completion exercise (Phase 2) |
| FR-14 | Epic 4 | Accept attempt & give positional feedback (Phase 2) |
| FR-15 | Epic 4 | Limited guesses with reveal (Phase 2) |
| FR-16 | Epic 4 | Accept valid alternative answers (Phase 2) |
| FR-17 | Epic 4 | Show explanation after code exercise (Phase 2) |
| FR-18 | Epic 2 | Portable/exportable content |

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
