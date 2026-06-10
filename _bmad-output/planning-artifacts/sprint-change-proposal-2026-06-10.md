# Sprint Change Proposal — Character-level Code-Completion feedback + Skip

**Date:** 2026-06-10
**Author:** Dario (via correct-course)
**Scope classification:** **Moderate** (reverses a logged design decision; updates PRD/architecture/decision-log/epics + a new dev story; no fundamental replan)
**Mode:** Batch

---

## 1. Issue Summary

The Code-Completion ("Wordle") drill experience is unpleasant. Two root causes:

1. **Feedback is token-level, but every answer is a single word.** Decision-log #11/#29 and PRD §4.3 deliberately chose **token-level** green/yellow/grey and rejected per-character feedback as "misleading in code where position is syntactically rigid." That rationale held for the originally-imagined *multi-token* snippets. But the shipped drill (and the entire authored bank) uses **single fill-in-the-blank, single-word answers** (`format`, `MATCHED`, `availableNow`, `checkpointLocation`, …). With one token, token-level feedback degenerates to **binary all-green or all-grey** — there is no guess-and-narrow loop, which is the whole point of Wordle. The "delight is load-bearing" goal (architecture cross-cutting concern) is unmet.
2. **No way out but to exhaust attempts.** A learner who is stuck must burn all `CODE_COMPLETION_MAX_ATTEMPTS` (6) guesses before they can move on — there is no Skip.

**Discovered:** during use of the Epic-4 runner (in review).

**Decision (this proposal):** adopt **character-level** Wordle feedback (true per-letter green/yellow/grey) and add a **Skip** button. This is a *justified reversal* of #11/#29 — the original concern (per-char misleading for rigid multi-token code) does not apply to single-word answers, where per-letter narrowing is exactly the desired feel.

---

## 2. Impact Analysis

**Epic impact:** Epic 4 only (Code-Completion). Epic 4 is in `review`; this is an in-flight correction, not a new epic.

**Story impact:**
- Stories **4.3** (positional-feedback algorithm) and **4.4** (FeedbackTokens rendering) shipped at *token* granularity — their ACs are now superseded for the feedback granularity.
- Story **4.5** (guess loop) shipped without Skip.
- **Recommended:** one new story **4.8 — Character-level feedback + Skip** that supersedes the token-granularity parts of 4.3/4.4 and adds Skip to the 4.5 loop. (We keep 4.3/4.4/4.5 as historical record rather than rewriting shipped ACs.)

**Artifact conflicts (need edits):**
- **PRD §4.3** — the CONFIRMED token-level design stance; **FR-14** ("token-level"); **FR-15** (add Skip); **§9** assumptions; **OQ-3** (was "resolved: token-level").
- **decision-log** — new entry reversing #11/#29.
- **architecture** — the "Code-Completion Tokenizer & Feedback Engine" decision (the **tokenizer becomes unused for feedback**; `codeFeedback` becomes character-based; `FeedbackTokens` renders per-character tiles), and **AR-9** (regex tokenizer); add Skip to the component boundary.
- **epics.md** — **AR-9** note + new **Story 4.8**.
- **UX** (EXPERIENCE.md/DESIGN.md) — light: code-completion now renders per-character tiles + a Skip affordance (subordinate to Submit). MCQ flows unchanged.

**Technical impact (code — handoff to dev-story under Story 4.8):**
- `frontend/src/utils/codeFeedback.js` — rewrite from token two-pass to **character two-pass** Wordle (compare answer-string chars; honor `case_sensitive` per-char and `ignore_whitespace`; score against best of `[canonical, ...accepted]`; `solved` = all-green AND equal length).
- `frontend/src/components/FeedbackTokens.jsx` — render **per-character** tiles (monospace), keep color-independence via the `role="status"` summary + per-tile `aria-label`; legend unchanged.
- `frontend/src/pages/CodeCompletion.jsx` — add a **Skip** button that advances via `useSession().next()` **without revealing** the answer; keep the 6-attempt cap (auto-reveal on exhaustion, reveal on solve).
- `frontend/src/utils/tokenizer.js` (+ `tokenizer.test.js`) — **no longer used for feedback** → remove. (`utils/language.js`/`LANGUAGE_ALIASES` stays — still used by `CodeBlock` for Prism + by `codeFeedback` for the per-language case rule.)
- Tests: rewrite `codeFeedback.test.js` for char-level; update `FeedbackTokens.test.jsx`; add a Skip test to `CodeCompletion.test.jsx`; delete `tokenizer.test.js`.
- **No backend change.** `<100ms` NFR still trivially met (char compare on one word).

---

## 3. Recommended Approach

**Direct Adjustment** — keep the Epic-4 runner architecture; change feedback granularity + add Skip, captured as a new **Story 4.8** plus artifact edits that record the reversal.

- **Effort:** small-to-moderate — one focused frontend story (feedback engine rewrite + rendering + Skip + tests), no backend, no new content. The hardest part (the guess-loop, retention, reveal, content) already exists.
- **Risk:** low. Char-level is simpler than the token two-pass it replaces. The reversal is well-reasoned and recorded. Existing content needs no change (answers are already single words).
- **Timeline:** does not block anything; improves the in-review Epic 4 before it merges.

---

## 4. Detailed Change Proposals

### 4.1 PRD §4.3 — design stance (token → character)

**OLD:**
> **CONFIRMED:** Positional Feedback uses **green / yellow / grey at the TOKEN level** (a token = keyword/identifier/operator/literal), not literal per-character. … Token-level is chosen because per-character "yellow" is misleading in code where position is syntactically rigid.

**NEW:**
> **CONFIRMED (revised 2026-06-10):** Positional Feedback uses **green / yellow / grey at the CHARACTER level** (true per-letter Wordle). The earlier token-level choice (decision #11/#29) is **reversed**: because each Code-Completion answer is a **single fill-in-the-blank word/token**, token-level feedback collapses to binary all-green/all-grey and kills the guess-and-narrow loop. Per-character feedback restores it. The original "per-char is misleading for rigid multi-token code" concern does not apply to single-word answers. Case follows the per-language `case_sensitive` flag (per-character compare); non-semantic whitespace is ignored (`ignore_whitespace`); duplicate letters use the standard two-pass Wordle rule.

### 4.2 PRD FR-14 (feedback) + FR-15 (skip)

- **FR-14:** "renders Positional Feedback … **per token**" → "**per character** (per-letter green/yellow/grey)."
- **FR-15:** add a consequence — "The user may **Skip** the current exercise at any time to advance to the next one **without** revealing the answer (distinct from solve/exhaustion, which do reveal). The bounded attempt count (6) is retained; Skip is the early bail."
- **§9 / OQ-3:** flip the "token-level" assumption to character-level; reopen OQ-3 as "resolved → character-level (2026-06-10)."

### 4.3 decision-log — new entries

> **#54 (2026-06-10) — Code-Completion feedback REVERSED token-level → CHARACTER-level.** Supersedes #11/#29. Rationale: all answers are single-word fill-in-the-blanks, so token-level is binary; per-letter Wordle restores guess-and-narrow. The #11 "per-char misleading for code" concern was about multi-token snippets and doesn't apply to one word. `tokenizer.js` is consequently removed (was only used for token feedback); `codeFeedback`/`FeedbackTokens` go character-based.
> **#55 (2026-06-10) — Skip added to the Code-Completion runner.** A Skip button advances to the next exercise without revealing the answer; the 6-guess cap is retained (Skip = early bail). Reveal still fires on solve/exhaustion.

### 4.4 architecture — feedback-engine decision + AR-9

- "Decision: Code-Completion Tokenizer & Feedback Engine" → **"Character-level Feedback Engine."** `computeFeedback` compares the attempt's characters to the answer's (two-pass green/yellow/grey, duplicate-safe), honoring `caseSensitive`/`ignoreWhitespace`, scored against the best of `[canonical, ...accepted]`. The **regex tokenizer (`tokenizer.js`) is removed** — feedback no longer tokenizes. `FeedbackTokens` renders per-character tiles. `<100ms` NFR unaffected.
- **AR-9** ("regex tokenizer") → mark **removed/superseded** by character-level comparison.
- Component boundary: `CodeCompletion` gains a **Skip → `next()`** path (no reveal).

### 4.5 epics.md — new Story 4.8 (ready-for-dev)

> **### Story 4.8: Character-Level Feedback + Skip**
> As a learner, I want per-letter Wordle feedback and a Skip button, so the drill actually narrows and I'm never trapped.
> **ACs:** char-level green/yellow/grey (two-pass duplicate rule) computed client-side <100ms; honors `case_sensitive`/`ignore_whitespace`; accepted alternatives scored best-candidate; `FeedbackTokens` renders per-character tiles (color-independent); a **Skip** control advances without revealing; 6-guess cap retained with reveal on solve/exhaustion; `tokenizer.js` removed; `codeFeedback`/`FeedbackTokens`/`CodeCompletion` tests updated; `tokenizer.test.js` deleted. Supersedes the token-granularity parts of 4.3/4.4 and extends 4.5.

### 4.6 Code (handoff to dev-story) — see §2 Technical impact for the file-by-file list.

---

## 5. Implementation Handoff

**Scope: Moderate.** No PM/architect escalation — the design call is made and recorded here.

**Plan:**
1. **Apply the planning-artifact edits** (PRD §4.3/FR-14/FR-15/§9/OQ-3, decision-log #54/#55, architecture feedback-engine + AR-9, epics AR-9 note) — done by correct-course on approval.
2. **Create Story 4.8** (`4-8-character-level-feedback-and-skip`, ready-for-dev) + add to sprint-status; mark AR-9/Story-4.3/4.4 superseded notes.
3. **Implement via dev-story** (Story 4.8): char-level `codeFeedback`, per-character `FeedbackTokens`, Skip in `CodeCompletion`, remove `tokenizer.js`, update/raze tests.

**Success criteria:** typing a partially-correct word shows per-letter green/yellow/grey; a Skip button advances without revealing; 6-guess cap + reveal-on-solve/exhaustion intact; suites green; `tokenizer.js` gone; PRD/architecture/decision-log reflect character-level + Skip.

**Note:** Story 4.6 is in `review` (its content needs no change — answers are already single words). Epic 4 remains in `review`/`in-progress`; 4.8 lands before the epic merges.
