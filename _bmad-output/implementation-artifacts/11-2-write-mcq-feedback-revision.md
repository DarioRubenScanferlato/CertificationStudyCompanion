---
status: done
baseline_commit: 247164b
---

# Story 11.2: write-mcq Feedback-Driven Revision

**Epic:** 11 - Question Feedback & Content-Improvement Loop
**Story Key:** 11-2-write-mcq-feedback-revision

## Story Statement

As **a content author**,
I want **the `write-mcq` skill to revise flagged questions using their feedback and mark the feedback resolved**,
So that **real study friction turns into a steadily better content bank**.

(FR-33 — PRD rev 6 §4.9. Depends on Story 11.1's sidecar store.)

## Acceptance Criteria

**Given** open (unresolved) feedback entries in `exercises/feedback.yaml`
**When** the `write-mcq` skill is run against an Exercise `id` (or sweeps `open_notes()`)
**Then** it reads the notes, edits the Exercise in its **source YAML** to fix the flagged issue, and re-validates against the Option Pool / domain rules (FR-1/FR-19)
**And** it marks the corresponding feedback entries `resolved` (or removes them) in the sidecar
**And** it only acts on Exercises with **open** feedback (resolved entries are skipped)
**And** the author reviews the change as a normal version-controlled diff (no approval UI)
**And** the skill is **MCQ-first**; a `write-code-completion` revision path is noted as a later extension

## Architecture Context

- Builds on Story 11.1's `feedback_store.py` (`open_notes()` / `notes_for()` / `mark_resolved()`) and the sidecar `exercises/feedback.yaml`.
- The existing `write-mcq` skill lives at `.claude/skills/write-mcq/SKILL.md` and authors MCQs into the YAML schema (Option Pool: ≥1 correct / ≥3 incorrect). This story adds a **feedback-aware revision mode** to that skill: locate the Exercise's source file, apply the fix implied by the note, preserve the Option-Pool structure + provenance, re-validate, and mark the note resolved.
- Edits are in place under version control; the author reviews the diff. No new endpoint or UI.

## Tasks / Subtasks

- [x] **Task 11.2.1 — Skill revision mode** (`.claude/skills/write-mcq/SKILL.md`, UPDATE)
  - [x] Add a "revise from feedback" flow: input = an Exercise id or "sweep open feedback"; read notes via the sidecar; edit the Exercise's source YAML to address the note; preserve schema/provenance; re-validate (Option Pool / domain); mark the entry resolved in `exercises/feedback.yaml`.
  - [x] Only touch Exercises with open feedback; skip resolved.
  - [x] Document the MCQ-first scope and the author-reviews-the-diff workflow.
- [x] **Task 11.2.2 — Validation + dry-run safety**
  - [x] After editing, the revised Exercise must still load + validate (no broken Option Pool, valid domain for its Certification). Surface a clear failure if a fix would invalidate the Exercise rather than writing bad content.
  - [x] Marking resolved happens only after a successful, validated edit.

### Review Findings (code review 2026-06-10)

- [x] [Review][Patch] Guardrail gap: if a feedback note's exercise `id` no longer exists in the content (renamed/removed), the skill could `mark_resolved` it and silently retire the note without fixing anything. Add a guardrail: when the id isn't found in content, surface it and leave the feedback open [.claude/skills/write-mcq/SKILL.md — Revise-from-feedback steps 2 & 6]

## Dev Notes

### UPDATE files
- `.claude/skills/write-mcq/SKILL.md` — feedback-aware revision mode.

### Dependencies / non-goals
- **Depends on Story 11.1** (the sidecar + `feedback_store.py` helpers it reads/marks).
- Code-completion revision (a `write-code-completion` parallel) is a later extension — out of scope.
- No approval UI; no automatic commit (author reviews + commits).

### References
- [Source: PRD §4.9 FR-33; §9 assumptions]
- [Source: addendum §I — skill revision loop]
- [Source: decision-log #50]
- [Source: `.claude/skills/write-mcq/SKILL.md`] — existing authoring flow + schema to extend.
- Story 11.1 — sidecar store + `open_notes`/`mark_resolved` consumed here.

## Dev Agent Record

### Agent Model Used
claude-opus-4-8 (dev-story workflow, 2026-06-10).

### Completion Notes List
- Added a **"Revise from feedback (FR-33)"** section to `write-mcq` `SKILL.md`: read open notes (`feedback_store.open_notes()` or the sidecar directly), locate the Exercise, re-research the docs, do a **surgical in-place edit** to address the note (preserving `id` / provenance / Option-Pool structure), **re-validate**, and only then **`feedback_store.mark_resolved(id)`**. Reports the diff for the author to review; no auto-commit, no approval UI.
- Guardrails documented: only act on **open** feedback; never change an Exercise `id`; mark-resolved strictly after a validated edit; **if a fix would invalidate the Exercise, leave the feedback open and surface it** rather than writing bad content; **MCQ-first** — code-completion exercises with feedback are flagged and skipped (a `write-code-completion` revision path is a later extension).
- Extended the skill's frontmatter `description` so it triggers on "fix/address feedback on bad questions", not only on authoring.
- This story is a **skill (prompt) enhancement** — no application code and no automated test (a skill is instructions, not code). It reuses Story 11.1's `feedback_store` helpers and the existing Workflow-step-5 validation. Verified the referenced helpers (`open_notes`, `mark_resolved`) exist and behave as documented (Story 11.1 tests).

### File List
- .claude/skills/write-mcq/SKILL.md (M — "Revise from feedback" mode + description)

### Change Log
- 2026-06-10 — Added feedback-driven revision mode to the write-mcq skill: edits flagged questions in place from the sidecar feedback and marks them resolved (Story 11.2).
- 2026-06-10 — Code review (bmad-code-review): applied 1 patch — added a guardrail so a feedback note whose exercise `id` no longer exists in content is surfaced and left OPEN (never silently `mark_resolved`'d). Status → done.
