---
status: ready-for-dev
baseline_commit: NO_VCS
---

# Story 2.3: Implement Content Validation

**Epic:** 2 - Exercise Content Management System
**Story Key:** 2-3-implement-content-validation

## Story Statement

As a **developer**,
I want **clear error reporting when exercises are malformed**,
So that **content authors can fix issues quickly**.

## Acceptance Criteria

**Given** an exercise YAML file has invalid structure
**When** the app loads the file
**Then** loading continues (doesn't crash)
**And** an error is logged with: file path, exercise ID, field, issue

## Architecture Context

- **Strategy**: Validate during load (story 2.2), collect errors, log them
- **Error types**: Missing required field, invalid enum value, reference mismatch (answer → option)
- **Logging**: Use Python logging to stderr/logfile
- **Non-blocking**: Invalid exercises skip loading; valid ones load
- **Error clarity**: Help authors diagnose (e.g., "answer 'x' not in options ['a','b','c']")

## Tasks/Subtasks

- [ ] Task 2.3.1: Create validation error handling
  - [ ] Create `ValidationError` exception class with file, exercise_id, field, message
  - [ ] Catch Pydantic ValidationError during YAML parsing
  - [ ] Convert Pydantic errors to readable messages

- [ ] Task 2.3.2: Implement error logging
  - [ ] Configure Python logging (stderr or file)
  - [ ] Log each validation error with full context
  - [ ] Include file path, line number (if available), exercise ID, error detail

- [ ] Task 2.3.3: Update content loader to collect errors
  - [ ] Modify `load_exercises_from_directory()` to catch and log errors
  - [ ] Continue loading remaining files on error (non-blocking)
  - [ ] Return (valid_exercises, error_count)

- [ ] Task 2.3.4: Add startup validation summary
  - [ ] Log summary on app startup: "Loaded N exercises, M errors"
  - [ ] List all errors at startup for visibility

- [ ] Task 2.3.5: Test validation error handling
  - [ ] Create `backend/tests/test_validation.py`
  - [ ] Test missing required field (e.g., no answer)
  - [ ] Test invalid enum (e.g., domain="InvalidDomain")
  - [ ] Test answer reference mismatch (answer refs invalid option)
  - [ ] Test malformed YAML syntax
  - [ ] Verify errors are logged, loading continues

## Dev Notes

- Use Python's `logging` module (built-in)
- Pydantic v1 raises `ValidationError` with detailed info
- Error messages should be dev-friendly (not shown to users yet)
- Invalid exercises are silently skipped in production

## Dev Agent Record

### Implementation Plan

1. Create ValidationError exception class
2. Set up logging configuration
3. Update content loader to catch and log errors
4. Add startup summary
5. Write comprehensive validation tests

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
