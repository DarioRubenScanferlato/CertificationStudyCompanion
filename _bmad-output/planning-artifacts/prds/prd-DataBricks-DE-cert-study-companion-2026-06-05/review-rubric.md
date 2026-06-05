# PRD Quality Review — Databricks DE Cert Study Companion

## Overall verdict

This is a genuinely good PRD for what it is: a tight, self-aware capability spec for a single-operator study tool with a real deadline. It has an honest thesis (MCQ-first because the exam is all MCQ; Wordle-drill second because it carries design risk), testable consequences on nearly every FR, and disciplined scope sequencing that explicitly defers the risky and the nice-to-have. The one material soft spot is that the entire content side rests on exam facts the document itself flags as unverified (OQ-1), and OQ-1 is correctly called "blocking content authoring" — so the green-light is real for the *app shell* but conditional for the *content bank* that SM-1/SM-2 depend on. Nothing here is broken; the risks are surfaced rather than hidden.

## Decision-readiness — strong

A builder could act on this today. Decisions are stated as decisions, not smuggled in as considerations: MCQ-first is asserted and justified ("exam-realistic MCQ practice is the heart of the product and ships first", §1), Wordle is "sequenced after the MCQ core precisely because it carries the most design risk" (§1), and the token-level feedback model is recorded as a *closed* decision (OQ-3 "resolved", §8; design stance "CONFIRMED", §4.3) rather than left dangling. Trade-offs name what was given up — the addendum's frontend section (§A) frames React-vs-HTMX around the concrete <100ms Positional Feedback tension rather than generic pros/cons.

The `[NOTE FOR PM]` callouts land at real tensions, not safe checkpoints: the riskiest-feature spike recommendation (§4.3 notes), the "emotionally load-bearing" timed-mode deferral (§6.2), and the blocking domain-weight verification (FR-4 notes). Open Questions are actually open — OQ-1, OQ-2, OQ-4, OQ-5 have no buried answer, and OQ-3 is honestly marked resolved rather than posed rhetorically.

### Findings
- **medium** Green-light is conditional on OQ-1, but the PRD presents itself as build-ready (§0 "green-light-to-build", §8 OQ-1 "blocking content authoring") — The app/loop work is unblocked, but SM-1 (pass the exam) and SM-2 (cover all five Domains) depend on Domain lists/weights the document says are "provisional" and "model-knowledge-based" (§8, addendum caveat). *Fix:* state explicitly that the app build can start now but content authoring at volume is gated on OQ-1; name who verifies the exam guide and by when.

## Substance over theater — strong

Little furniture here. The differentiation claim (Wordle-for-code) is earned by Discovery, not template-filling: addendum §D names the closest structural analog (Nerdle), the adjacent tools (typing.io's skip-whitespace insight, SQLBolt fill-in-the-blank), and — credibly — labels the "no incumbent" claim "moderate-confidence" requiring manual verification rather than overclaiming novelty. The eight UX pitfalls in §D each trace to a specific §4.3 assumption, which is the opposite of innovation theater.

NFRs are product-specific, not boilerplate: the single feature-NFR (<100ms Positional Feedback, §4.3) has a real threshold tied to a real mechanic and even reasons about client-side computability. No "must be scalable/secure/reliable" padding. The Vision (§1) is specific to this product — it could not swap into another cert tool unchanged because the core-loop description and the Wordle bet are concrete. Personas are not inflated: a single named operator (Dario) with JTBD framing, appropriate for the shape.

## Strategic coherence — strong

There is a clear thesis and the features serve it. The arc — content format (4.1) is foundational because "value grows by adding content rather than code" (§1), MCQ (4.2) is the heart because it mirrors the all-MCQ exam, Wordle (4.3) is the differentiated bet sequenced after for risk reasons, generation (4.4) deferred — is a coherent problem-solving MVP, not a backlog with headings. Prioritization follows the thesis and the deadline, not "what's easy."

Success Metrics validate the thesis rather than measuring activity: SM-1 is the blunt real one (uses it and *passes*), SM-2/SM-3 validate the content-driven bet, and crucially the counter-metrics are well-chosen — SM-C1 ("a beautiful app with 12 questions fails the actual job") and SM-C2 (don't gold-plate Wordle at the expense of MCQ) name the exact failure modes a solo builder on a deadline is prone to. Counter-metrics present and pointed.

## Done-ness clarity — strong

This is the dimension a story-creation workflow leans on, and it holds up. Every FR (FR-1 through FR-17) carries a "Consequences (testable)" block with verifiable conditions: FR-1 "loads with zero code changes", FR-3 "surfaces a specific validation error naming the field and the offending Exercise", FR-6 "monospace with whitespace/indentation preserved", FR-12 "Score reflects the FR-9 scoring rule". The few adjective-risk phrases are defended: "render legibly" (FR-6) is immediately bounded to "monospace, preserved formatting", and "feel instant" (FR-14/NFR) is bounded to "<100ms". FR-9 explicitly demands the scoring rule be "documented", closing the usual multi-select ambiguity.

### Findings
- **low** FR-9 leaves the actual scoring rule to an assumption rather than deciding it inline (§4.2 FR-9) — The FR mandates a "defined, predictable" rule and documentation, but the rule itself ("all-or-nothing") lives in `[ASSUMPTION]` pending confirmation. Acceptable at this rigor, but a story author will need the decision resolved before implementing FR-12's score calc. *Fix:* promote the all-or-nothing choice to a decision (it matches typical exam scoring anyway) or flag it as story-blocking.

## Scope honesty — strong

Omissions are explicit and do real work. §5 Non-Goals is substantive (not a lab platform, not multi-user, not an authoring UI, not a braindump, not an LMS, not multi-cert) and each line carries a reason. §6.2 phases the deferrals with rationale ("Deferred because it is the highest-risk"). De-scoping is done out loud — generation (4.4) is explicitly recorded "so the format stays generation-friendly, not because v1 builds it."

Open-items density is appropriate for the stakes and, importantly, *not* alarming for a green-light PRD: ~9 assumptions, 5 Open Questions, a handful of `[NOTE FOR PM]`. The Assumptions Index (§9) does a clean roundtrip with the inline tags. The one thing that keeps this from being a frictionless green-light is that OQ-1 is load-bearing for the content half (already noted under Decision-readiness), but the PRD is honest about that rather than silent.

## Downstream usability — adequate

The PRD is chain-top (it explicitly "feeds the downstream architecture and implementation work", §0), so this matters. The Glossary (§3) is present, well-defined, and terms are used consistently (Exercise, Domain, MCQ, Practice Session, Positional Feedback, Option, Explanation appear verbatim across FRs/UJs/SMs). FR IDs are contiguous and unique (FR-1–FR-17, no gaps or dupes); UJ-1/UJ-2 and SM-1–SM-4 + SM-C1/SM-C2 are clean. Cross-references resolve (UJ-1 → FR-7–FR-12, UJ-2 → FR-13–FR-17, FRs → addendum schema).

### Findings
- **low** UJ-1's FR range is stated two different ways (§2.3 vs §4.2) — UJ-1 header says "Realizes FR-7 through FR-12" but §4.2 says the MCQ feature "Realizes UJ-1" while spanning FR-5–FR-12. The session-start/filter steps in UJ-1 ("picks a practice set filtered to that domain") actually exercise FR-5/FR-6, so the UJ→FR mapping under-counts by two. *Fix:* change UJ-1 to "Realizes FR-5 through FR-12" for a clean roundtrip.

## Shape fit — strong

The PRD correctly identifies its own shape and resists over-formalization. It states the calibration explicitly — "Single operator (the builder). Journeys kept light per scope; they exist to pin down the core loop, not to drive heavy UX" (§2.3) and "Hobby/personal scope — kept lean" (§7). Two UJs (one of them Phase 2) is exactly the right amount of journey for a single-operator capability spec; more would be the over-formalization the rubric warns against. SMs are appropriately a mix of operational (SM-2/SM-3) and the one user-facing outcome that actually matters (SM-1 = pass). No consumer-product UJ density forced onto a solo tool, and no missing UJs given the core loop is genuinely captured. Matches the agreed medium-low rigor.

## Mechanical notes

- **Glossary drift:** none material. Terms are capitalized and used consistently. Minor: "Exercise Type" values appear as prose ("MCQ", "Code-Completion") in the Glossary but as snake_case enums (`single_choice`, `code_completion`) in the addendum schema — expected author-vs-spec difference, worth a one-line note in OQ-2 if not already implied.
- **ID continuity:** FR-1–FR-17 contiguous/unique; UJ-1/UJ-2, SM-1–SM-4, SM-C1/SM-C2, OQ-1–OQ-5 all clean.
- **Assumptions Index roundtrip:** clean — every inline `[ASSUMPTION]` (§4.1 ×3, FR-6, FR-9, FR-10, §4.3 cluster, FR-16, §6.1) appears in §9 and vice versa. §9 correctly notes the token-level model is a *decision*, not an assumption.
- **UJ protagonist naming:** both UJs carry the named protagonist (Dario) with inline context. No floating UJs.
- **Cross-ref nit:** UJ-1 FR-range mismatch noted under Downstream usability (low).
- **Required sections:** all present for the stakes/shape (Vision, Target User/JTBD, Glossary, Features+FRs, Non-Goals, MVP Scope, Success Metrics, Open Questions, Assumptions Index).
