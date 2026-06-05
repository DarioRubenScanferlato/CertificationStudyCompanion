# Adversarial Review — Databricks DE Cert Study Companion PRD

Reviewer stance: skeptical. Goal is to surface what will bite the builder, not to be balanced.
Reviewed: `prd.md` + `addendum.md` (both dated 2026-06-05). Exam ~1–2 months out, solo builder.

---

## Verdict

**This PRD will get the builder a nicely-engineered exercise platform and a failed (or un-taken) exam.** The document is well-written and the *sequencing instinct is correct* (MCQ before Wordle), but it has the classic builder-prep failure mode baked in: it treats the **app** as the deliverable and the **content** as a footnote (`[ASSUMPTION: ... exact count TBD]`, deferred to OQ-4). For a cert exam in 4–8 weeks, the content bank IS the product and the limiting reagent — and it is the single most under-specified thing in the document. The PRD also commits the builder to a custom file format + schema validator + actionable error reporting + dedup + alias layer + a full single-question session UI before a single real study session can happen. That is weeks of plumbing standing between the builder and studying.

The Wordle feature is correctly deferred, but the PRD has quietly *over-decided* it (declaring token-level green/yellow/grey "CONFIRMED" / "resolved") while the genuinely hard part — tokenizing arbitrary SQL/PySpark fragments and computing a sensible yellow — remains hand-waved. Several FRs are not testable as written, and there is real scope creep dressed as "foundational."

**Recommendation: cut the MVP roughly in half, reframe the content bank as the primary deliverable with a hard numeric target and a build-vs-study time budget, and demote the file-format/validator ambitions to "smallest thing that loads."**

---

## Findings

### [critical] The content bank is the real product and it is the least-specified thing in the PRD
**Location:** §6.1 ("Initial Exercise content seeded ... `[ASSUMPTION: order of tens of MCQs ... exact count TBD]`"), OQ-4, SM-2, SM-C1.
The whole document spends 4 features and 17 FRs on the *app* and relegates the content — the thing that actually determines whether the builder passes — to one assumption line and an open question with "exact count TBD." This is exactly backwards for a time-boxed cert prep. Authoring even ~45 MCQs that are (a) blueprint-aligned across 5 weighted domains, (b) have plausible distractors, (c) carry per-distractor rationale, (d) cite a real doc link, and (e) are original/non-braindump and *technically correct* is a multi-day-to-multi-week effort by itself — and it has to compete with the app build for the same scarce calendar.
The PRD even names the counter-metric (SM-C1: "a beautiful app with 12 questions fails the actual job") but does not act on its own warning: it sets no minimum viable content count, no per-domain quota tied to the published weights (24/29/22/16/9), and no author-time budget.
**Fix:** Promote content to a first-class deliverable with a hard target *now*, not via OQ-4. Concrete: minimum ~50–75 MCQs distributed by the addendum's domain weights (e.g. ~15 ELT, ~12 Lakehouse, ~11 Incremental, ~8 Production Pipelines, ~5 Governance) authored and *self-reviewed for correctness* before any optional app polish. Add an explicit time budget (e.g. "app build ≤ X days; if exceeded, freeze app and author content"). Make "agent-skill authoring" (OQ-5) a committed parallel workstream with its own definition of done, not an open question.

### [critical] MVP scope is too large to be useful in time — builder will be building instead of studying
**Location:** §6.1 In Scope; Features 4.1 (FR-1–FR-4) + 4.2 (FR-5–FR-12).
The "ships first, fast" MVP is: a custom YAML schema, runtime file discovery/loading, schema validation with file+id+field-level error messages, duplicate-id detection, unknown-domain validation, partial-load-with-report semantics, *plus* a full single-question session engine (filtering, single/multi-select, submit, feedback, per-distractor explanation rendering, monospace code rendering, session advance, end-of-session per-domain summary). For a solo builder with a deadline, that is not a "fast" MVP — it is the bulk of a real product. Every hour here is an hour not studying, and the app cannot return *any* study value until almost all of it is done (you can't run a session until loading + validation + the full session UI all work).
**Fix — leaner cut that delivers study value in days, not weeks:**
- Drop the custom schema-validation machinery (FR-3's actionable errors, FR-2's dedup, FR-4's unknown-domain flagging) from MVP. Use a dead-simple flat file (even a single YAML/JSON list) parsed with a library; a malformed file can just throw a stack trace — the builder is the only author and can fix it. "Actionable errors" is a feature for *other* authors who don't exist in v1 (see §5 Non-Goal: single-user).
- Collapse the session UI: a one-question-at-a-time loop with reveal-on-submit is fine; defer the per-domain breakdown summary (FR-12) and even backward navigation. A flat correct/total is enough to study.
- Seriously consider: do you even need a bespoke app for MVP? A static page that renders a JSON array, or an Anki deck / a single-file HTML quiz, could deliver MCQ-with-explanations study value in a day, leaving the 1–2 months for content + actual revision. The PRD never asks "build vs. buy/borrow" for the core loop, and for a deadline-driven solo learner that omission is itself the biggest risk. At minimum, record why a from-scratch build beats existing tools (Anki, a Quizlet, a markdown-driven static quiz).

### [high] "Token-level green/yellow/grey is CONFIRMED" papers over the actual hard problem: the tokenizer and the meaning of yellow
**Location:** §4.3 Design stance ("CONFIRMED"), OQ-3 ("resolved"), FR-14, addendum §D.3.
The PRD declares the *color model* decided and reduces the spike to "validate the tokenizer and rendering, not the color model." But the color model is the easy part; the landmines are exactly in the tokenizer and in what "yellow = token present but wrong slot" *means* for code:
- **Tokenizing arbitrary SQL/PySpark fragments is not free.** You need a real lexer per language (SQL keywords/operators/identifiers/string literals/numeric literals vs. PySpark method chains, dotted access `df.write.format`, quoted strings, kwargs). A naive whitespace/regex split will mis-tokenize `spark.read.format("delta")` and `WHEN NOT MATCHED THEN INSERT *`. This is a chunk of work the PRD assigns zero FR weight to.
- **"Yellow" is barely meaningful even at the token level.** The addendum (§D.3) admits position in code is "syntactically rigid" — so for a single-blank fill-in (the chosen scope), there is usually exactly one slot and yellow can't occur; for a multi-token blank, "right token, wrong slot" mostly means the user's syntax is simply wrong. The PRD keeps yellow anyway "Nerdle-style" without showing a single code example where yellow actually helps. Nerdle works because equations have many interchangeable-position symbols; a `MERGE` arm does not.
- **Duplicate tokens** (two `)`s, two string literals, repeated `option`) create the classic Wordle duplicate-letter coloring ambiguity — unaddressed.
- **FR-14's "< 100ms, computable client-side" + FR-16's accepted-alternatives** interact badly: if you tokenize and the user typed a valid alternative phrasing, per-token coloring against *which* canonical answer? Coloring vs. a chosen alternative can show a "correct" attempt as half-yellow. Undefined.
**Fix:** Re-open OQ-3 to "feedback *granularity and the role of yellow* are unproven; the spike must produce 3–4 worked code examples demonstrating yellow earns its keep, or drop to green/grey only (present-correct vs not)." Add an explicit FR (or spike deliverable) for "tokenizer per language" and state the dependency (a lexer library or hand-rolled). Define coloring-against-alternatives behavior. Given this is Phase 2 and the exam has *no live coding*, also challenge whether this feature should exist before the exam at all — it trains a skill the exam never tests (SM-4 is a "nice to recall" goal, not exam-load-bearing).

### [high] Several FRs are not testable as written
**Location:** FR-9, FR-14, §4.3 NFR, SM-4.
- **FR-9 "defined, predictable scoring rule"** with consequence "applied consistently and documented" is circular — it tests that a rule exists, not that the *right* rule is used. The actual decision (all-or-nothing) is buried in an `[ASSUMPTION]`. A test can't fail. **Fix:** State the rule in the FR ("multi-select is all-or-nothing: marked correct iff the selected set exactly equals the correct set") so the consequence becomes a real assertion.
- **FR-14 "without a server round-trip perceptible to the user (target < 100ms)"** — "perceptible" is unmeasurable and the 100ms is a "target," so no test can pass/fail it. Also it pre-supposes a client/server split that §A says is undecided (HTMX vs React). **Fix:** make it a hard NFR with a measurable bound on a defined machine, or drop the number to an aspiration and stop calling it a consequence.
- **SM-4 "feels instant and *teaches* syntax (Dario can recall a drilled snippet unaided afterward)"** — not measurable, n=1, post-hoc. Fine as a vibe goal, but it is listed as validating FR-13–FR-17, which it cannot.
- **FR-13 consequence "target language ... is indicated"** and **FR-6 "rendered legibly"** — "legibly" is subjective. Minor, but tighten to "monospace, whitespace preserved" (which FR-6 actually does say elsewhere — so the "legibly" adjective is redundant furniture).

### [medium] The DLT→Lakeflow "name-alias layer" is unscoped scope creep that can swallow days
**Location:** addendum §C ("Build a name-alias layer so both old and new naming are accepted in questions/snippets"), OQ-1.
This is stated as a build instruction in the addendum but has no FR, no schema support shown, and no owner. "Accept both old and new naming in questions/snippets" is ambiguous: is it a content-authoring convention (just write both), a display-time substitution, or matching logic in the Code-Completion checker? Each is a different amount of work, and the matching-logic interpretation interacts with FR-16's alternatives and the tokenizer. For a single author who controls all content, an alias *layer* is almost certainly over-engineering — you can simply author the current naming and note aliases in explanations.
**Fix:** Delete the "build a name-alias layer" instruction or demote it explicitly to "authoring guidance: prefer current Lakeflow naming, mention prior names in explanations." If any runtime aliasing is truly wanted, it needs its own FR and must wait until OQ-1 confirms the actual exam's current terminology (the addendum admits all naming is unverified).

### [medium] OQ-1 is marked "blocking content authoring" but content authoring is in the MVP — this is an unresolved hard dependency
**Location:** OQ-1 (blocking), §6.1 (content seeded in MVP), addendum caveat (all exam facts unverified, no live network at research time).
The PRD admits every domain list, weight, question count, passing score, and product name is provisional/model-derived, and that confirming them *blocks* authoring at volume — yet authoring the starter bank is in MVP scope. So the MVP has a hard, unresolved external dependency sitting in the open-questions section rather than in a "must do first" gate. If the builder authors 50 questions against the wrong/old blueprint, that's rework on the critical path to the exam.
**Fix:** Make OQ-1 a *gate*, not an open question: "Before authoring beyond ~5 probe questions, pull the live official PDF exam guide and lock domain list + weights." It is a 30-minute task with network access and it de-risks the entire content effort. Sequence it as step zero.

### [medium] FR-3 partial-load-with-report and FR-2 dedup are author-facing features in a single-author product
**Location:** FR-2 (duplicate-id detection/reporting), FR-3 (partial-load, actionable per-field errors), §5 Non-Goal (single-user, file-authored).
These requirements implicitly serve a multi-author / shared-content future (the deferred "share with peers" JTBD). In a strictly single-user MVP where the same person writes and consumes the files, robust validation/dedup/partial-load is gold-plating: a crash with a stack trace is an acceptable "error report" when you are the author. This is effort spent on the *deferred* sharing path, not the MVP exam goal.
**Fix:** Cut FR-3's partial-load and FR-2's dedup from MVP; keep only "fail loudly on bad file." Move robust validation to the same future phase as sharing, where multiple/untrusted authors actually create the need.

### [low] YAML-author / JSON-serve is a self-imposed extra pipeline for a single-user local app
**Location:** §4.1, OQ-2, addendum §A/§B.
The PRD itself flags doubt ("whether YAML-author/JSON-serve is worth the extra step for a single-user local app"). It is almost certainly not worth it for MVP — it adds a transform/build step and a second representation to keep in sync, for zero user-visible benefit at n=1.
**Fix:** Default MVP to a single format (YAML *or* JSON) read directly at runtime. Resolve OQ-2 toward "one format, no transform" unless/until generation or sharing forces JSON.

### [low] Appendix A (8 future exercise types) is furniture that risks anchoring the schema toward generality
**Location:** Appendix A.
Eight speculative exercise types are recorded "so the format ... stays open to them." Harmless as a parking lot, but it subtly pressures the FR-1 schema toward premature generality (the very "treat both types uniformly later" framing in FR-1's consequences). For a deadline build, designing the format to accommodate output-prediction, spot-the-bug, ordering, matching, config-fill, scenario, true/false, and flashcards is a trap.
**Fix:** Keep the appendix as ideas only; add a one-line explicit instruction: "Do NOT generalize the MVP schema for these — add fields when a type is actually built." Prevents the foundational format from absorbing speculative complexity.

### [low] "Foundational — built first, with 4.2" ordering hides a serial dependency that delays first study value
**Location:** §4.1 header, build order in §4.
Listing 4.1 as "built first" means the builder front-loads format + loader + validator before any MCQ can render. Combined with the content dependency (OQ-1) and the authoring effort, *nothing studyable exists* until format + validation + content + session UI all land. The "fast MVP" therefore has a long lead time to first value.
**Fix:** Re-sequence to reach a usable study loop ASAP: hardcode/inline 5 questions, build the minimal session view, confirm the loop *teaches*, then generalize loading and scale content. Optimize for "first real study session" as the earliest milestone, not "format is elegant."

---

## Summary of the leaner cut (what I'd actually ship)
1. **Lock the blueprint (OQ-1) today** — 30 min with network.
2. **Author content as the primary deliverable** — hard target ~50–75 MCQs by domain weight, self-checked for correctness, agent-skill as a committed parallel track.
3. **Smallest loader** — one format, read at runtime, fail loudly. Drop dedup/partial-load/actionable-error machinery.
4. **Minimal session loop** — filter by domain, one MCQ at a time, submit, reveal explanation, flat score. Defer per-domain summary and backward nav.
5. **Defer Wordle entirely** until after the exam — it drills a skill the exam doesn't test; and before any build, force a spike that proves "yellow" earns its place or drop to green/grey.
6. **Hard time-box the app build**; if exceeded, freeze and study.

---

*Report file:* `/Users/dariorubenscanferlato/Documents/Projects/DataBricks-DE-cert-study-companion/_bmad-output/planning-artifacts/prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/review-adversarial.md`
