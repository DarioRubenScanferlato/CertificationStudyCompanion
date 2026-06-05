---
status: ready-for-dev
baseline_commit: NO_VCS
---

# Story 2.4: Implement Anki Export

**Epic:** 2 - Exercise Content Management System
**Story Key:** 2-4-implement-anki-export

## Story Statement

As a **student**,
I want **to export MCQ exercises to Anki format**,
So that **I can study with Anki on my mobile device**.

## Acceptance Criteria

**Given** MCQ exercises are loaded in the app
**When** I request an Anki export
**Then** a `.apkg` file (or JSON deck) is created
**And** the deck contains: question, options, correct answer, explanation
**And** exports can be downloaded via API endpoint

## Architecture Context

- **Format**: Anki `.apkg` (SQLite-based) or JSON/genanki format
- **Content mapping**:
  - Front: Question + options
  - Back: Correct answer + explanation
  - Tags: domain, difficulty, source
- **Scope**: MCQ exercises only (Code-Completion deferred)
- **Export location**: `/api/export/anki` endpoint or script
- **Tool options**: `genanki` library (pip install) or manual `.apkg` creation

## Tasks/Subtasks

- [ ] Task 2.4.1: Create Anki deck model
  - [ ] Install `genanki` library (add to pyproject.toml optional dependencies)
  - [ ] Define Anki note model (fields: question, options, answer, explanation, tags)
  - [ ] Create deck template

- [ ] Task 2.4.2: Implement exercise-to-note conversion
  - [ ] Create `convert_mcq_to_note(exercise)` function
  - [ ] Format question as front (with options A/B/C/D)
  - [ ] Format back (correct answer + explanation)
  - [ ] Add tags (domain, difficulty)

- [ ] Task 2.4.3: Create export function
  - [ ] Create `export_exercises_to_anki(exercises, output_path)` function
  - [ ] Create Anki deck
  - [ ] Add notes from exercises
  - [ ] Write `.apkg` file

- [ ] Task 2.4.4: Create API endpoint for export
  - [ ] Create `GET /api/export/anki` endpoint
  - [ ] Filter exercises (optional: by domain/difficulty)
  - [ ] Generate `.apkg` file
  - [ ] Return file as download (Content-Disposition: attachment)

- [ ] Task 2.4.5: Test Anki export
  - [ ] Create `backend/tests/test_export.py`
  - [ ] Test note conversion from MCQ
  - [ ] Test deck creation with multiple exercises
  - [ ] Test API endpoint returns downloadable file

## Dev Notes

- `genanki` is the most straightforward way to create `.apkg` files
- Alternative: use `anki2apkg` if genanki has issues
- Ensure exported deck is importable in standard Anki client
- Code-Completion exercises excluded from export (text rendering tricky)

## Dev Agent Record

### Implementation Plan

1. Install and configure genanki
2. Create Anki note model and conversion function
3. Implement export function
4. Create API endpoint
5. Test with 72 MCQs to verify Anki compatibility

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
