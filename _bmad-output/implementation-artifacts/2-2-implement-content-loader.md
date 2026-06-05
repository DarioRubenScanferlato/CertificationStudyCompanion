---
status: ready-for-dev
baseline_commit: NO_VCS
---

# Story 2.2: Implement Content Loader

**Epic:** 2 - Exercise Content Management System
**Story Key:** 2-2-implement-content-loader

## Story Statement

As a **developer**,
I want **to load YAML exercise files at startup**,
So that **exercises are available in memory for API queries**.

## Acceptance Criteria

**Given** YAML exercise files exist in `exercises/associate/`
**When** the FastAPI app starts
**Then** all valid YAML files are loaded into memory
**And** `GET /api/exercises` returns the loaded exercises
**And** `GET /api/exercises?domain=X&difficulty=Y` filters correctly

## Architecture Context

- **Content location**: `exercises/associate/*.yaml` (also `exercises/professional/` for future)
- **Startup loading**: Load at app startup, cache in memory (via Pydantic model)
- **API endpoint**: `GET /api/exercises` returns `{success, data: [exercises], error}`
- **Filtering**: By domain, difficulty, exam, exercise_set (query params)
- **Scalability**: ~100-500 exercises per category (in-memory is fine for MVP)

## Tasks/Subtasks

- [ ] Task 2.2.1: Create content loader module
  - [ ] Create `backend/app/content.py`
  - [ ] Implement `load_exercises_from_directory(path)` function
  - [ ] Scan `exercises/associate/` recursively for `.yaml` files
  - [ ] Parse YAML and validate against Pydantic models
  - [ ] Return list of Exercise objects

- [ ] Task 2.2.2: Integrate loader into FastAPI app startup
  - [ ] Create app lifespan context manager
  - [ ] Load exercises on app startup (before accepting requests)
  - [ ] Store exercises in app state: `app.state.exercises = [...]`
  - [ ] Ensure exercises are available to route handlers

- [ ] Task 2.2.3: Create GET /api/exercises endpoint
  - [ ] Accept query params: domain, difficulty, exam, exercise_type
  - [ ] Filter exercises based on params (all optional)
  - [ ] Return `{success: true, data: [exercises], error: null}`
  - [ ] Handle empty results gracefully

- [ ] Task 2.2.4: Implement filtering logic
  - [ ] Create `filter_exercises(exercises, domain=None, difficulty=None, ...)` function
  - [ ] Filter is case-insensitive for domain names
  - [ ] Return matching exercises (or all if no filters)

- [ ] Task 2.2.5: Test content loader
  - [ ] Create `backend/tests/test_content.py`
  - [ ] Test loading exercises from sample YAML
  - [ ] Test filtering by domain, difficulty, exam
  - [ ] Test endpoint response format

## Dev Notes

- YAML loading uses PyYAML (standard library compatible)
- Pydantic validation happens during parsing; invalid files should be logged but not crash startup (story 2.3)
- Filtering is case-insensitive for user-friendliness
- Use 72 validated MCQs from `exercises/associate/mcq-associate-batch-01.yaml` for testing

## Dev Agent Record

### Implementation Plan

1. Create `content.py` loader module with YAML scanning
2. Implement filtering logic
3. Integrate with FastAPI startup (lifespan context)
4. Create GET /api/exercises endpoint
5. Write tests covering load + filter scenarios

### Subtasks Completed

(To be filled in as implementation progresses)

### Completion Notes

(To be filled in upon task completion)

## File List

(Files will be listed here upon completion)

## Change Log

- Initial story creation — 2026-06-05

## Status

ready-for-dev
