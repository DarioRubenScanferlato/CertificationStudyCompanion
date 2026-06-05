# Brief ↔ PRD Reconciliation

**Input:** User's original brief for the Databricks DE certification practice app.
**Artifacts reviewed:** `prd.md`, `addendum.md` (same PRD folder, 2026-06-05).
**Date:** 2026-06-05.

## Method
Each element of the brief is traced to where it lives in the PRD or addendum, then checked for distortion of intent (especially qualitative/emotional intent the FR structure tends to flatten). The one deliberate change (per-letter → per-token feedback) is confirmed as intentional, not accidental loss.

## Brief element → coverage map

| # | Brief element | Captured? | Where | Notes |
|---|---------------|-----------|-------|-------|
| 1 | App to practice for Databricks DE cert exam | YES | prd §0, §1, §2 (UJ-1), SM-1 | Faithful; framed single-user/local, exam ~1–2 months out. |
| 2 | Generate exercises from official Databricks docs | YES (as optional/deferred) | prd §4.4, §6.2 | Correctly demoted to optional per brief (see element 6). |
| 3 | Multiple-choice exercises "like in the exam" | YES | prd §4.2 (FR-5–FR-12), UJ-1 | "Exam-like" experience preserved (one-at-a-time, single+multi-select, immediate feedback, explanations). Strong. |
| 4 | Code-completion exercise, Wordle-style positional feedback | YES | prd §4.3 (FR-13–FR-17), Glossary "Positional Feedback", addendum §B, §D | See deliberate change below. |
| 5 | Practice SQL **and** PySpark syntax | YES | prd §1 ("syntax fluency in Spark SQL and PySpark"), §2.1, FR-13 (language indicated), addendum §B (`language: pyspark|sql`), §C | Both languages explicitly carried. |
| 6 | Generation is optional; if too complex, author manually via agent skill, needing a standardized parseable format | YES | prd §4.1 (FR-1–FR-4), §4.4, §6.1, addendum §B (proposed schema) | Brief's conditional logic preserved: standardized format + agent-skill authoring is the committed path; generation optional. |
| 7 | MCQ is most important, implemented first | YES | prd §1, §4.2 header ("the priority — MVP"), §6.1, build-order in §4 | Faithful and emphasized. |
| 8 | Wordle exercise implemented later (Phase 2) | YES | prd §4.3 header ("Phase 2 — after MVP"), §6.2 | Faithful. |
| 9 | Suggestions for future exercise types | YES | prd Appendix A (8 ideas) | Brief explicitly asked for suggestions; delivered. |
| 10 | Frontend React or HTMX — investigate in architecture | YES | prd §0 (out of scope for PRD), addendum §A | Correctly deferred; addendum even flags the HTMX latency tension for Wordle feedback. |
| 11 | Backend Rust or Python (with uv) — investigate | YES | prd §0, addendum §A | Correctly deferred; `uv` named. |
| 12 | "This might be a tricky component to implement" (risk flag on Wordle) | YES | prd §4.3 Description + [NOTE FOR PM] ("riskiest feature", recommends design spike), SM-C2, §6.2 | Risk intent preserved and amplified appropriately. |

## Deliberate change — CONFIRMED correct
- Brief described **per-LETTER** green/yellow feedback ("a correct letter in the right position … wrong position").
- Decision (2026-06-05) changed this to **TOKEN-level green/yellow/grey** (Nerdle-style; token = keyword/identifier/operator/literal).
- PRD reflects the decision consistently and in the right places:
  - prd §1 (vision), Glossary "Positional Feedback" (per-token, with per-char noted as alternative), §4.3 "Design stance" marked **CONFIRMED**, OQ-3 marked **(resolved)**, §9 Assumptions Index ("Token-level … is a confirmed decision, not an assumption").
  - addendum §D pitfall 3 records the rationale (char-level "yellow" is misleading where code position is syntactically rigid) and the 2026-06-05 resolution.
  - Schema (addendum §B) carries `feedback_granularity: token | char (default token)`.
- Note: brief used only green/yellow (two states); PRD/decision adds **grey** (token absent). This is a sensible completion of the Wordle model, consistent with the user's stated "kind of like wordle" framing, not a distortion.

## Gaps / risks to flag

1. **"Wordle" emotional appeal slightly abstracted by the token decision.** The brief's draw was the playful, letter-by-letter Wordle feel. Token-level feedback is the right engineering call, but the PRD should ensure the *game-like, guess-and-narrow delight* survives — currently it reads as a syntax drill (FR-13–FR-17 are correct but clinical). The fun/novelty intent lives mainly in prose (§1 "novel", "differentiated"); no FR or success metric guards the *feel* of playfulness beyond SM-4's "feels instant." Minor, but the most easily-lost qualitative element.

2. **`char` granularity left as a live schema option contradicts the "resolved" decision.** addendum §B schema still exposes `feedback_granularity: token | char`. Since OQ-3 is resolved to token-level and per-char was explicitly rejected (§D pitfall 3), leaving `char` as a selectable field invites re-litigating a settled decision. Recommend removing `char` or annotating it as not-supported-in-v1.

3. **Brief's two-color model (green/yellow) vs PRD's three-color (green/yellow/grey)** is an intentional-looking expansion that is never explicitly called out to the user as a change. It is reasonable, but should be surfaced for confirmation alongside the letter→token change so it is not a silent addition.

4. **"Like in the exam" realism for MCQ is partially deferred.** Brief said MCQ should be "like in the exam." Flag-for-review and timed mode (both genuine exam-realism features, noted in addendum §D items 3 & 6) are deferred to later phases. Acceptable for MVP and §6.2 marks timed mode "emotionally load-bearing for exam realism," but the brief's "like in the exam" phrasing is only partly honored at MVP — worth an explicit user ack.

5. **Generation feature's "official Databricks documentation" source-grounding is preserved only as a deferred note.** Brief tied generation specifically to *official docs*; PRD §4.4 keeps this (provenance/`source` field, anti-braindump stance) but at note-depth only. No loss, but the "grounded in official docs" intent is thin and should not be dropped if/when generation is picked up.

## Verdict
All twelve brief elements are captured. No element is silently dropped. The one deliberate change (per-letter → per-token feedback) is correctly and consistently reflected and explicitly marked as a decision. Residual items are minor: protect the Wordle *playfulness*, reconcile the lingering `char` schema option with the resolved token decision, and surface the two-color → three-color expansion for user confirmation.
