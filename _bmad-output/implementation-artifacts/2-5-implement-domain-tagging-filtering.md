---
status: ready-for-dev
baseline_commit: NO_VCS
---

# Story 2.5: Implement Domain Tagging & Filtering

**Epic:** 2 - Exercise Content Management System
**Story Key:** 2-5-implement-domain-tagging-filtering

## Story Statement

As a **student**,
I want **to filter exercises by domain and difficulty**,
So that **I can practice weak areas**.

## Acceptance Criteria

**Given** exercises are tagged with domain and difficulty
**When** I request exercises filtered by domain
**Then** only matching exercises are returned
**And** filters can be combined (domain AND difficulty)
**And** domain names match the Databricks exam blueprint

## Architecture Context

- **Domains** (5 Associate):
  1. Databricks Lakehouse Platform
  2. ELT with Spark SQL and Python
  3. Incremental Data Processing
  4. Production Pipelines
  5. Data Governance
- **Difficulty**: easy, medium, hard
- **Exam**: associate, professional
- **Filtering**: Server-side (GET /api/exercises?domain=X&difficulty=Y)
- **Frontend usage**: SessionSelect page (story 3.1) will use these filters

## Tasks/Subtasks

- [ ] Task 2.5.1: Validate domain enum against exam blueprint
  - [ ] Verify 5 Associate domains match official Databricks guide
  - [ ] Add Professional domains (6 total) for future use
  - [ ] Document domain weights (for analytics later)

- [ ] Task 2.5.2: Create domain validation in Pydantic models
  - [ ] Ensure Exercise.domain is validated against Domain enum
  - [ ] Reject exercises with unknown domains during load
  - [ ] Log warnings for domain mismatches

- [ ] Task 2.5.3: Implement filtering API
  - [ ] Create `filter_exercises_by_domain(exercises, domain)` function
  - [ ] Create `filter_exercises_by_difficulty(exercises, difficulty)` function
  - [ ] Create combined filter function
  - [ ] Handle case-insensitive domain names

- [ ] Task 2.5.4: Enhance GET /api/exercises endpoint
  - [ ] Support query params: domain, difficulty, exam, exercise_type
  - [ ] All params optional; no params returns all exercises
  - [ ] Multiple filters combine with AND logic
  - [ ] Return `{success, data: [exercises], error}`

- [ ] Task 2.5.5: Test filtering
  - [ ] Create `backend/tests/test_filtering.py`
  - [ ] Test single-domain filter
  - [ ] Test single-difficulty filter
  - [ ] Test combined domain + difficulty
  - [ ] Test case-insensitive domain matching
  - [ ] Test with 72 MCQs to verify correct counts per domain

## Dev Notes

- Domain is required field on all exercises; validation catches mismatches
- Filtering happens in-memory (fast for ~100-500 exercises)
- Frontend will call `/api/exercises?domain=X&difficulty=Y` on page load
- Case-insensitive domain names improve usability (users might type "Lakehouse" vs "Databricks Lakehouse Platform")

## Dev Agent Record

### Implementation Plan

1. Validate domain enum against Databricks blueprint
2. Implement filtering functions (domain, difficulty, combined)
3. Enhance GET /api/exercises endpoint with query params
4. Add comprehensive filter tests
5. Verify filtering with 72 MCQs across 5 domains

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
