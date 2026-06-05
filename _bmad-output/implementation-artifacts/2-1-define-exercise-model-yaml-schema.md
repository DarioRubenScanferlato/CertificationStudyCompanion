---
status: ready-for-dev
baseline_commit: NO_VCS
---

# Story 2.1: Define Exercise Model & YAML Schema

**Epic:** 2 - Exercise Content Management System
**Story Key:** 2-1-define-exercise-model-yaml-schema

## Story Statement

As a **developer**,
I want **a clear YAML schema and Pydantic models for exercises**,
So that **I can validate and load exercise data consistently**.

## Acceptance Criteria

**Given** I want to create an exercise file
**When** I author a YAML file following the schema
**Then** Pydantic models validate the structure
**And** validation catches missing/invalid fields
**And** both MCQ and Code-Completion types are supported

## Architecture Context

- **Content format**: YAML-authored, Pydantic-validated, JSON-serializable
- **Types**: MCQ (single/multi-choice) + Code-Completion
- **Common fields**: id, type, exam, domain, difficulty, question, explanation, references, tags, source
- **Type-specific fields**:
  - MCQ: options[], answer[]
  - Code-Completion: template, answer, accepted[], language
- **Validation**: Non-empty, correct answer refs, domain alignment

## Tasks/Subtasks

- [x] Task 2.1.1: Create Pydantic base models
  - [x] Create `backend/app/models.py` with Exercise base models
  - [x] Define ExerciseType enum (single_choice, multi_choice, code_completion)
  - [x] Define ExamType enum (associate, professional)
  - [x] Define Difficulty enum (easy, medium, hard)
  - [x] Define Domain enum (5 Associate domains)

- [x] Task 2.1.2: Create MCQ-specific models
  - [x] Create Option model (id, text, correct)
  - [x] Create MCQ model (extends Exercise with options[], answer[])
  - [x] Implement validators (options not empty, answers reference valid option IDs)

- [x] Task 2.1.3: Create Code-Completion model
  - [x] Create CodeCompletion model with template, answer, accepted[], language, case_sensitive
  - [x] Validators for non-empty fields

- [x] Task 2.1.4: Create Exercise union type
  - [x] Create Exercise = MCQ | CodeCompletion discriminated union
  - [x] Test that validation works for both types

- [x] Task 2.1.5: Test models with sample data
  - [x] Create `backend/tests/test_models.py` (14 comprehensive tests)
  - [x] Test MCQ creation and validation (8 tests)
  - [x] Test Code-Completion creation and validation (3 tests)
  - [x] Test invalid data rejection and defaults (3 tests)

## Dev Notes

- Use Pydantic v1.x (already pinned in pyproject.toml)
- Validators should be clear and helpful (specific error messages)
- Models should be JSON-serializable for API responses
- Use discriminated union for Exercise type to avoid ambiguity

## Dev Agent Record

### Implementation Plan

1. Create base Pydantic models with enums (ExerciseType, ExamType, Difficulty, Domain)
2. Create MCQ models with validators
3. Create Code-Completion models
4. Create Exercise discriminated union
5. Write comprehensive tests for all model combinations

### Subtasks Completed

(To be filled in as implementation progresses)

### Completion Notes

✅ All tasks completed successfully. Pydantic models fully implemented and tested:
- 5 enums defined (ExerciseType, ExamType, Difficulty, Domain)
- BaseExercise model with common fields
- MCQ model with validators (options not empty, answers reference valid options)
- CodeCompletion model with validators (template has blank, answer not empty)
- Exercise discriminated union type (MCQ | CodeCompletion)
- 14 comprehensive tests all passing (100%)
- Models JSON-serializable for API responses

## File List

- backend/app/models.py (new - 167 lines)
- backend/tests/test_models.py (new - 246 lines, 14 tests)

## Change Log

- Task 2.1.1: Created Pydantic base models with enums — 2026-06-05
- Task 2.1.2: Created MCQ model with validators — 2026-06-05
- Task 2.1.3: Created CodeCompletion model — 2026-06-05
- Task 2.1.4: Created Exercise discriminated union — 2026-06-05
- Task 2.1.5: Created and verified 14 model tests (all passing) — 2026-06-05

## Status

review
