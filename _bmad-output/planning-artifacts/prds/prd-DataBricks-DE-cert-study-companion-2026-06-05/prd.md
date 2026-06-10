---
title: Cert Study Companion
status: final
created: 2026-06-05
updated: 2026-06-10
revision: 6 (Question feedback & content-improvement loop — in-app feedback notes → sidecar YAML; write-mcq revises flagged questions)
---

# PRD: Cert Study Companion
*Generic working title (rev 5, 2026-06-09) — the renamed, provider-agnostic successor to the original "Databricks DE Cert Study Companion." Databricks DE remains the **first bundled certification**, fully intact.*

> **Rev 5 reframe (2026-06-09).** The product is being generalized from a Databricks-only tool into a **companion for any IT certification**, so courses from other providers (other cloud vendors, etc.) can be added. This revision (a) generalizes the data model and vocabulary — see the new **Provider** / **Certification** terms in §3 — so a new certification is **content + config, no code change**, and (b) makes the app **shareable with colleagues via a single `docker compose up`**, where each colleague runs their **own** instance (single-user per instance; local history; no accounts/hosting). The Databricks DE content, glossary detail, and all of Epics 1–8 + Epic 4 are preserved — Databricks DE Associate/Professional are simply the first two bundled Certifications. Renaming touches titles/README/UI only; folder/`project_name`/artifact paths are unchanged (decision-log #34).

## 0. Document Purpose

This PRD is for Dario as the builder, and for the downstream architecture and implementation work it feeds. It defines **what** the study companion must do — not how it is built. The app began as a personal tool to practice for the **Databricks Certified Data Engineer** exams; it is now being generalized into a **provider-agnostic IT-certification study companion** that can host any certification's content, with Databricks DE as the first bundled Certification and a near-term goal of **sharing it with colleagues** (each running their own instance via docker compose).

Structure: vocabulary is anchored in the Glossary (§3) and used verbatim throughout; features are grouped with globally-numbered Functional Requirements (FRs) nested under them; assumptions are tagged inline as `[ASSUMPTION: …]` and indexed in §9. Technology choices the user raised (React vs HTMX; Rust vs Python+uv) and the rev-5 **containerization + per-Certification config mechanisms** are **out of scope for this PRD** and are recorded in the companion `addendum.md` for the architecture phase. Discovery research (exam structure, comparable products, the "Wordle-for-code" design space, and a proposed exercise file schema) also lives in `addendum.md`.

## 1. Vision

A lightweight, locally-run study companion that turns **any IT certification's** prep into short, focused practice sessions. Its core loop mirrors the real exam: read a question (often with a code snippet), pick an answer, and immediately learn *why* — with a rationale tied to the certification's domain and a link back to the official docs. Because most cert exams are multiple-choice with no live coding, exam-realistic MCQ practice is the heart of the product. The companion is **provider-agnostic**: a new certification (from any cloud vendor or other IT-cert provider) is added as **content + configuration**, with no code change. **Databricks Certified Data Engineer (Associate & Professional)** is the first bundled Certification — the seed content the product was born from — and remains intact.

Beyond the exam itself, the app aims to build genuine **syntax fluency** in the certification's target language(s) — Spark SQL and PySpark for Databricks DE — through a second, novel exercise type: a "Wordle-style" code-completion drill that gives positional feedback as you type code. This is a deliberately differentiated, under-served idea — most cert tools stop at multiple choice — and the drill's target language is per-exercise, so it generalizes to any certification that has a code surface.

The companion is content-driven, and the **content bank is the durable product** — not the app shell. Exercises live in a simple, human-authorable, version-controlled, **portable** file format that the user (or a Claude agent skill) writes by hand. Because the format is portable, content can be studied immediately through an existing tool (e.g. exported to Anki) while the bespoke app matures. The app's value grows by adding content rather than code, and the same portability keeps the content provider-neutral.

This reframes the build: **borrow for the deadline, build for the novelty.** Exam-realistic MCQ practice is table-stakes and can be served immediately by a lean built-in runner *or* a borrowed tool; the genuinely under-served, worth-building-from-scratch piece is the Wordle-style code-completion drill. See §6's Build-vs-Borrow decision.

**Now shareable (rev 5).** With the app mature, the next step is **handing it to colleagues**: a single `docker compose up` brings the whole app up with no host toolchain to install. Each colleague runs their **own** instance — their practice history stays local to their machine — so sharing means distributing the tool + content, not standing up a hosted multi-user service.

## 2. Target User

### 2.1 Jobs To Be Done
- **As the builder/learner:** "I have an IT certification exam coming up and I want to drill exam-style questions and check my answers with explanations, so I walk in confident." (Started with Databricks DE — the primary, originating framing — now generalized to any certification I'm bundling.)
- **Practice syntax I keep fumbling:** "I want to rehearse the certification's syntax (for Databricks DE: MERGE, Auto Loader options, DLT/Lakeflow decorators, window functions) until it's automatic, not just recognizable."
- **Study in small chunks:** "I want to do a 10–15 minute session on a specific domain (e.g. Incremental Data Processing) when I have a gap, not commit to a whole mock exam."
- **Grow my own bank:** "I want to author or generate new questions cheaply — for any certification I add — and have them just show up in the app."
- **Add another provider's cert:** "When a colleague or I want to study a different certification (another cloud vendor, a different track), I want to drop in its content + a small config and have it work, without touching app code."
- **Share with colleagues (now committed — rev 5):** "I want to hand this to a colleague so they can study too — ideally one command (`docker compose up`) on their own machine, their own progress."

### 2.2 Non-Users (v1)
- Other learners as *end users on a single shared/hosted instance* — the app is single-user **per instance**; colleagues each run their **own** instance (decision-log #35). A hosted, multi-user, account-based service is still out of scope.
- ~~Candidates for non-Databricks-DE certs~~ — **no longer excluded (rev 5):** the product is now provider-agnostic by design (FR-29/FR-30). Databricks DE is simply the first bundled Certification; other certifications are added as content + config.
- Learners wanting hands-on lab/cluster execution — these exams have no live coding and neither does this app.

### 2.3 Key User Journeys
*Single operator (the builder). Journeys kept light per scope; they exist to pin down the core loop, not to drive heavy UX.*

- **UJ-1. Dario drills a weak domain over coffee.**
  Dario has ~15 minutes and knows Incremental Data Processing is his weak spot. He opens the app (running locally), picks a practice set filtered to that domain, and works through multiple-choice questions one at a time, in randomized order. For each, he sees four options (one correct, three distractors) in shuffled positions, selects an answer, submits, and immediately sees whether he was right, a rationale for the correct answer and why the distractors are wrong, and a link to the relevant Databricks doc. At the end he sees a simple score for the session. Realizes FR-5 through FR-12 and FR-20/FR-21. **Re-study behavior:** when Dario revisits this domain the next day, questions appear in a different order (FR-21), and a previously-seen question may show a different correct option and/or different distractors drawn from its Option Pool (FR-19/FR-20) — so it feels fresh rather than memorized-by-position.

- **UJ-2. Dario rehearses PySpark syntax he keeps forgetting.** *(Epic 4 — now active scope)*
  Dario can never remember the exact Auto Loader options. He opens a code-completion exercise: a short prompt ("Configure Auto Loader to infer and evolve schema") and a code template with a blank. He types his attempt; the app gives Wordle-style positional feedback (correct tokens highlighted) and lets him try again within a guess limit. When he solves it (or runs out of guesses), he sees the canonical answer and a short explanation. Realizes FR-13 through FR-17. **Edge case:** he types a *valid alternative* phrasing (`df.where` vs `df.filter`) — the exercise accepts it rather than marking it wrong (FR-16).

## 3. Glossary

*Downstream workflows and readers must use these terms exactly. No synonyms elsewhere in the PRD.*

- **Provider** *(new, rev 5)* — The organization that issues a certification (e.g. **Databricks**; other cloud vendors and IT-cert bodies in future). A Provider owns one or more Certifications. The first bundled Provider is Databricks.
- **Certification** *(new, rev 5)* — A specific certification exam offered by a Provider — e.g. **Databricks Certified Data Engineer Associate** and **…Professional** are two Certifications under the Databricks Provider. A Certification carries its own canonical Domain list, Domain weights, and exam parameters (question count, duration, pass-bar heuristic), all defined in **per-Certification configuration** (FR-29), not in app code.
- **Exam** — Retained as the historical term and as the **content/data field that identifies a Certification** (e.g. `exam: associate`). Generalized in rev 5: an "Exam" value now names a Certification within its Provider; the original two values (`associate`, `professional`) are the Databricks DE Certifications. *(Kept as the field name so the existing exam-filter — Story 6.7 — and content schema continue to work; "Exam" and "Certification" are interchangeable in this document, with "Certification" preferred for the generalized concept.)*
- **Domain** — An official certification-blueprint topic area with a weight (e.g. "Incremental Data Processing" for Databricks DE Associate). Every Exercise is tagged with exactly one Domain. The canonical Domain list and weights **per Certification** are defined by that Provider's current exam guide and recorded in the Certification's configuration (FR-29).
- **Subdomain** — An optional finer topic tag within a Domain (e.g. "Auto Loader" within "Incremental Data Processing").
- **Exercise** — A single practice item the user attempts. Two **Exercise Types** exist: **MCQ** and **Code-Completion**. Every Exercise has a stable `id`, a Domain, a difficulty, and an explanation.
- **MCQ (Multiple-Choice Question)** — An Exercise presenting a question (optionally with a code snippet) and an **Option Pool**; at each presentation the runner shows four **Displayed Options** (one correct, three incorrect) and the user selects one and submits. **Single-select only** — the multi-select ("select all that apply") variant is removed (decision 2026-06-05; see §4.2 and decision log).
- **Code-Completion Exercise** — The "Wordle-style" Exercise Type: a code template with a blank (or a prompt) that the user completes by typing, receiving positional feedback. (Epic 4 — active scope as of 2026-06-08.)
- **Option** — One selectable answer choice in an MCQ, with text, a `correct` flag, and optionally per-Option rationale.
- **Option Pool** — The full set of Options authored for an MCQ: **at least one** flagged correct and **at least three** flagged incorrect, with **no upper bound** on either. Extra correct alternatives and/or extra distractors are encouraged — they let the runner show a different combination each time so the Exercise feels new on re-view.
- **Displayed Options** — The four Options actually shown for one presentation of an MCQ: exactly **one** correct Option sampled from the pool's correct Options plus **three** incorrect Options sampled from the pool's incorrect Options, presented in **randomized positions**.
- **Explanation** — The teaching text shown after an Exercise is answered: why the correct answer is correct, why distractors are wrong, and reference link(s) to official docs.
- **Exercise Set** — A named, parseable file (or collection of files) containing Exercises, loaded by the app. The unit the user authors or generates.
- **Practice Session** — A single run-through of a selected group of Exercises (filtered by Domain / difficulty / type), presented in **randomized order**, ending in a summary.
- **Positional Feedback** — In a Code-Completion Exercise, per-token (or per-character) coloring indicating correct content in the correct place vs. correct content in the wrong place vs. absent — the Wordle mechanic, adapted for code.

## 4. Features

*Listed in build order. FR IDs are global and stable.*

### 4.1 Exercise Content Format & Loading *(foundational — built first, with 4.2)*

**Description:** The app is content-driven. Exercises live in a **standardized, human-authorable, version-controlled file format** that the user — or a Claude agent skill — can write by hand and drop into the project. The app loads these files, validates them against the schema, and makes them available as Practice Sessions. This feature is foundational: it is the contract between content authoring and the app, and it is what makes in-app generation *optional* rather than required. The exact schema is proposed in `addendum.md` (YAML for authoring; the app may serve/store JSON internally). `[ASSUMPTION: authoring format is YAML, one Exercise Set per file, loaded from a known content directory in the repo.]`

**Functional Requirements:**

#### FR-1: Standardized, parseable Exercise format
The format defines, for each Exercise: stable `id`, Exercise Type, Domain (and optional Subdomain), difficulty, the question/prompt, type-specific payload (Options for MCQ; template/answer for Code-Completion), Explanation, and optional reference link(s) and tags.

**Consequences (testable):**
- A hand-authored Exercise Set file conforming to the documented schema loads with zero code changes.
- An MCQ is authored as an **Option Pool** (FR-19): each Option carries a `correct` flag, with no fixed option count — the format permits more than the minimum of either correct or incorrect Options.
- MCQ and Code-Completion share common fields (`id`, `domain`, `difficulty`, `explanation`) so analytics/session logic can treat them uniformly later.

#### FR-2: App loads Exercise Sets from files
The app discovers and loads Exercise Set files from a designated content location at startup (or on demand).

**Consequences (testable):**
- Adding a new well-formed file makes its Exercises available without rebuilding/recompiling content into the app. `[ASSUMPTION: content is read from files at runtime, not compiled in.]`
- Exercises retain their authored `id`; duplicate `id`s across the corpus are detected and reported.

#### FR-3: Fail clearly on malformed content
A malformed Exercise file fails loudly with enough information to locate the problem (which file, ideally which Exercise) rather than failing silently. *(Deliberately minimal for v1 — single author; a clear error/stack trace is an acceptable "validation report." Elaborate per-field validation and partial-load are explicitly out of scope for MVP — see §6.)*

**Consequences (testable):**
- Loading a file with a syntax/schema error produces an error that names the file (and where possible the Exercise) — not a silent drop.

#### FR-4: Blueprint-aligned Domain tagging
Domains (and the per-Certification canonical Domain list) align with the **Certification's** official exam blueprint, so content can be filtered and — later — weighted to mirror the real exam. The canonical Domain list + weights for each Certification come from its configuration (FR-29), not hardcoded values. For the seed content this is Databricks DE's official blueprint.

**Consequences (testable):**
- Every Exercise resolves to exactly one Domain from the canonical list for its Certification.
- An Exercise tagged with an unknown Domain (for its Certification) is flagged in validation.

#### FR-19: MCQ Option Pool (≥1 correct, ≥3 incorrect)
Each MCQ is authored as an **Option Pool**: at least one Option flagged `correct` and at least three flagged incorrect, with **no upper bound** on either. Authors are encouraged to add extra correct alternatives and/or extra distractors beyond the minimum; the runner samples a four-Option display from the pool (FR-20), so a richer pool makes a question feel new on re-view without authoring a separate question. *(Decided 2026-06-05.)*

**Consequences (testable):**
- Validation rejects any MCQ with fewer than 1 correct or fewer than 3 incorrect Options (a pool must always be able to yield a 1-correct + 3-incorrect display).
- An MCQ may carry more than one correct Option and/or more than three incorrect Options; such pools load without error.
- `[ASSUMPTION: a pool's multiple correct Options are mutually-exclusive *alternatives* — any single one is a valid answer on its own — not a set that must be selected together. This is what makes single-select sampling sound; see FR-20 and the multi-select removal in §4.2.]`

#### FR-18: Portable / exportable content
The Exercise format is portable enough that MCQ content can be consumed by an existing study tool, so studying is not gated on the bespoke app being finished. *(This is what makes the Build-vs-Borrow decision in §6 viable.)*

**Consequences (testable):**
- The MCQ content can be converted/exported to at least one external tool's import format — Anki is the reference target. `[ASSUMPTION: Anki is the borrow target; a one-shot converter (script) is acceptable rather than live two-way sync.]`
- The conversion preserves question, options, correct answer(s), and Explanation.

**Notes:** `[NOTE FOR PM] The canonical Domain lists and their weights must be confirmed against the current Databricks PDF exam guides (see Open Question OQ-1) before authoring at volume.`

### 4.2 Multiple-Choice Practice *(lean built-in runner — or borrow; see §6)*

**Description:** Exam-realistic MCQ practice — the core study loop. The user selects a group of Exercises (a Practice Session); the session presents MCQs one at a time in **randomized order** (FR-21), exam-style. Each MCQ shows **four Displayed Options** — one correct, three distractors — sampled from the question's Option Pool and shown in **shuffled positions** (FR-20). The user selects one Option, submits, and gets immediate correctness feedback plus the Explanation. At session end they see a simple score summary. Realizes UJ-1.

*MCQ practice is **single-select only**. The earlier multi-select ("select all that apply") variant is removed (decision 2026-06-05): every display is exactly one correct Option plus three distractors. A question's Option Pool may still carry multiple correct Options, but they are treated as interchangeable alternatives (FR-19), only one of which is shown per display.*

*Build-vs-Borrow stance (see §6): this loop is **table-stakes, not novel** — every cert tool has it. The built-in runner is therefore deliberately **lean**, and a borrowed tool (Anki via FR-18) is an acceptable substitute for v1 studying. The FRs below specify the lean built-in runner if/when built; they are NOT a reason to delay studying.*

**Functional Requirements:**

#### FR-5: Start a Practice Session with filters
The user can start a Practice Session over a filtered subset of Exercises — at minimum by Domain and by difficulty; optionally by Exercise Set and by Exercise Type.

**Consequences (testable):**
- Selecting Domain = "Incremental Data Processing" yields a session containing only that Domain's Exercises.
- An empty filter result is communicated clearly (no crash, no empty silent screen).

#### FR-6: Present one MCQ at a time, exam-style
The session shows a single MCQ at a time: the question text, any associated code snippet rendered legibly (monospace, preserved formatting), and the four Displayed Options (FR-20).

**Consequences (testable):**
- Code snippets in questions render in monospace with whitespace/indentation preserved.
- Exactly four Options are shown per MCQ display (one correct, three distractors — see FR-20).
- The user can navigate forward through the session; `[ASSUMPTION: backward navigation within a session is allowed but not required for MVP — confirm.]`

#### FR-7: Select one answer and submit
The user selects exactly one Option (single-select) and submits. The UI uses a single-choice affordance (radio).

**Consequences (testable):**
- Exactly one Option can be selected at a time; selecting another replaces the prior selection.
- Submission is an explicit action (the user can change selection before submitting).

#### FR-8: Immediate correctness feedback
On submit, the app immediately indicates whether the answer was correct and which Option(s) were correct.

**Consequences (testable):**
- Correct/incorrect state is shown without navigating away.
- The correct Option(s) are visually identifiable after submit, including when the user was wrong.

#### FR-9: ~~Defined multi-select scoring~~ — REMOVED
*Superseded 2026-06-05. The multi-select MCQ variant (and its all-or-nothing scoring) is removed; MCQ practice is single-select only (see FR-7 and §4.2). An answer is correct iff the single selected Option is the Displayed Options' correct Option. ID retained as a tombstone so downstream references don't dangle.*

`[NOTE FOR PM] Existing authored content includes a few genuine "select all that apply" items (jointly-correct sets, not interchangeable alternatives). Under the single-select decision these must be reworked — rewrite as single-correct questions or convert their correct set into pooled alternatives — or excluded from the runner. Validation should flag any MCQ whose correct Options are not interchangeable. Tracked as a content-migration follow-up.]`

#### FR-10: Show Explanation after answering
After submit, the app shows the Explanation: why the correct answer is correct, ideally why distractors are wrong, and any reference link(s).

**Consequences (testable):**
- Explanation and reference link(s), when present in the Exercise, are displayed post-submit.
- Reference links open the official doc (in browser). `[ASSUMPTION: links open externally.]`

#### FR-11: Advance through the session
The user can move to the next Exercise after reviewing feedback, until the session is complete.

**Consequences (testable):**
- After the last Exercise, the user is taken to the session summary (FR-12).

#### FR-12: End-of-session summary
At session end, the app shows a simple summary: number correct / total, and a per-Domain breakdown when the session spans multiple Domains.

**Consequences (testable):**
- Score reflects single-select correctness (one selected Option vs. the Displayed Options' correct Option; see FR-7).
- A single-Domain session still shows a meaningful summary.

#### FR-20: Sample and shuffle Displayed Options per presentation
When presenting an MCQ, the runner builds the four Displayed Options by sampling **one** correct Option from the question's Option Pool and **three** incorrect Options from the pool, then renders them in **randomized positions**.

**Consequences (testable):**
- Every MCQ display shows exactly four Options: one correct, three incorrect.
- For a pool with extra correct alternatives and/or extra distractors, two presentations of the same question can show a different correct Option and/or a different distractor set.
- The correct Option does not occupy a fixed slot across presentations (position is shuffled).
- `[ASSUMPTION: sampling is uniform-at-random per presentation, with no memory of prior presentations in MVP (no guaranteed distractor rotation / no anti-repeat). Sampling is independent of FR-21's question-order shuffle.]`

#### FR-21: Randomize Exercise order within a Practice Session
The Exercises in a Practice Session are presented in randomized order, so starting a session on the same filter does not surface the same questions in the same sequence each time.

**Consequences (testable):**
- Two sessions over the same filtered set present the Exercises in (generally) different orders.
- Randomization spans the full filtered set, not just a fixed first page.
- `[ASSUMPTION: order is re-randomized fresh each session; no seed/resume-in-order guarantee, and no spaced-repetition weighting in MVP — that's the later SRS phase (§6.2).]`

**Out of Scope (this feature, MVP):**
- Persisting session history across runs — *was* deferred; **now in scope** as §4.5 (Epic 7).
- Timed/countdown mode — *was* deferred; **now in scope** as §4.6 (Epic 8).

### 4.3 Code-Completion ("Wordle-style") Practice *(active scope — promoted from Phase 2; decided 2026-06-08; Epic 4)*

**Description:** A novel syntax-drilling Exercise Type and the product's key differentiator. The *feel* is load-bearing, not incidental: the playful, Wordle-like **guess-and-narrow** loop — attempt, see colored feedback, refine — is the reason this is more engaging than a flashcard, and the design should preserve that delight rather than reduce it to a correctness check. The user is given a short prompt and a code template containing a blank (e.g. a `MERGE` statement with the `WHEN NOT MATCHED` arm blanked, or an Auto Loader `.option(...)`), types an attempt, and receives **Positional Feedback** in the Wordle spirit. Discovery research surfaced real design hazards in porting Wordle literally to code; the FRs below encode the research-recommended shape rather than a naive per-character clone. The detailed feedback algorithm and rendering approach belong to architecture/design and are captured in `addendum.md`.

**Design stance — all CONFIRMED and locked in the `CodeCompletion` model + Epic 4 stories (2026-06-08):**
- **CONFIRMED (revised 2026-06-10 — reverses decision #11/#29; see decision-log #54):** Positional Feedback uses **green / yellow / grey at the CHARACTER level** (true per-letter Wordle). Green = correct letter in the correct slot; yellow = letter present in the answer but in the wrong slot; grey = letter not in the answer. **The earlier token-level choice is reversed:** because each Code-Completion answer is a **single fill-in-the-blank word/token**, token-level feedback collapses to binary all-green/all-grey and kills the guess-and-narrow loop. Per-character restores it. The original "per-char is misleading for rigid *multi-token* code" concern does not apply to a single word. Case follows the per-language `case_sensitive` flag (per-character compare); non-semantic whitespace is ignored (`ignore_whitespace`); duplicate letters use the standard two-pass Wordle rule. *(Mechanism in addendum §F; the regex tokenizer is no longer used for feedback.)*
- **CONFIRMED:** each exercise is scoped to a **single line / single fill-in-the-blank slot** (the `template` carries one `___` blank), not a multi-line snippet, to keep feedback legible.
- **CONFIRMED:** non-semantic whitespace is **ignored** in matching (model `ignore_whitespace`, default true); the user is not penalized for indentation/spacing.
- **CONFIRMED:** case policy is **explicit per language** (SQL keywords case-insensitive; PySpark/Python identifiers case-sensitive), carried by the model `case_sensitive` flag (default false).
- **CONFIRMED:** multiple valid answers are accepted via the model's authored **`accepted` alternatives** set.
- **CONFIRMED (2026-06-08): feedback is computed CLIENT-SIDE** — the tokenizer + comparison run in the browser to meet the < 100ms target (NFR below). There is **no** server-side code-completion feedback endpoint. As a consequence, the canonical answer + accepted alternatives are delivered to the client for the *active* exercise (see FR-14 and the §9 assumption). Mechanism in addendum §F.

**Functional Requirements:**

#### FR-13: Present a Code-Completion Exercise
The app presents the prompt, the code template with its blank/slot clearly indicated, and the input affordance. Realizes UJ-2.

**Consequences (testable):**
- The template renders in monospace with the blank visibly marked.
- The target language (SQL or PySpark) is indicated.

#### FR-14: Accept a typed attempt and give Positional Feedback
On an attempt, the app evaluates it against the canonical answer and renders **per-character** Positional Feedback (true per-letter Wordle): letter correct and in the right place vs. correct letter in the wrong place vs. letter not in the answer. *(Revised 2026-06-10 — character-level, not token-level; see §4.3 and decision-log #54.)*

**Consequences (testable):**
- Feedback is computed **client-side** and shown without a server round-trip (target < 100ms; see NFR). No `POST /api/feedback/code-completion` call is made.
- Feedback is **per character**: each letter of the attempt is colored green/yellow/grey vs. the answer, with two-pass duplicate-letter handling.
- Whitespace handling follows the ignore-non-semantic-whitespace rule (model `ignore_whitespace`); case follows the per-language `case_sensitive` flag (per-character compare).
- Because grading is client-side, the active Code-Completion Exercise's canonical answer + accepted alternatives are present on the client. This is acceptable for the Wordle drill (the guess-and-narrow loop reveals the answer through feedback regardless; there is no multiple-choice gaming surface) and does **not** relax the MCQ non-leakage rule (FR-20 Displayed Options still never carry `correct` flags) — the two Exercise types have different leakage models.

#### FR-15: Limited guesses with reveal, plus Skip
The user has a bounded number of attempts; on solving or exhausting attempts, the canonical answer is revealed. The user may also **Skip** the exercise at any time to advance to the next one. *(Skip added 2026-06-10; see decision-log #55.)*

**Consequences (testable):**
- The remaining-attempts count is visible.
- On the final failed attempt, the canonical answer and Explanation are shown.
- A **Skip** control advances to the next exercise **without revealing** the answer/Explanation (distinct from solve/exhaustion, which do reveal) — the user is never forced to exhaust attempts. The 6-guess cap is retained as the auto-reveal backstop.

#### FR-16: Accept valid alternative answers
Authored alternative correct phrasings are treated as correct.

**Consequences (testable):**
- An attempt matching any entry in the Exercise's accepted-alternatives set is marked solved.
- `[ASSUMPTION: matching is against an authored alternatives list in MVP of this feature; AST/execution-equivalence validation is explicitly out of scope.]`

#### FR-17: Show Explanation after a Code-Completion Exercise
As with MCQs, the Explanation (and references) is shown once the Exercise concludes.

**Consequences (testable):**
- Explanation displays on solve or on exhausting attempts.

**Feature-specific NFRs:**
- Positional Feedback must feel instant (target < 100ms from keystroke/submit to render); the comparison is small and should be computable client-side.

**Notes:** *(2026-06-08)* The throwaway-design-spike recommendation is **superseded** — the FR set is committed directly. De-risking is handled by (a) the shipped `CodeCompletion` model, (b) a **client-side, pure, unit-tested tokenizer + feedback engine** split into their own stories (Epic 4: 4.2 tokenizer, 4.3 `computeFeedback`) so the algorithm is validated in isolation before it touches the UI (4.4) and the guess loop (4.5), and (c) a starter content bank + authoring skill (4.6). Feedback semantics were token-level green/yellow/grey at 2026-06-08; **revised 2026-06-10 to character-level (per-letter) and the regex tokenizer removed** (Story 4.8, decision-log #54).

### 4.4 Exercise Generation *(optional — deferred)*

**Description:** Optionally, the app could generate Exercises from official Databricks documentation rather than relying solely on hand/agent authoring. Per the user's direction this is **explicitly optional** and **not in the MVP**: the standardized format (4.1) plus a Claude agent skill that authors into it is the committed path. Generation is recorded here so the format stays generation-friendly, not because v1 builds it.

**Functional Requirements:** *(deferred — not specified at FR depth in v1)*
- `[NOTE FOR PM] If/when pursued: define source-doc ingestion, generation quality controls (no hallucinated APIs, correct answers verifiable), and dedup against existing Exercises. The 4.1 format already carries a `source`/provenance field to support an anti-braindump / "original, verified" stance.]`

### 4.5 Answer & Stats Tracking *(post-MVP scope expansion — decided 2026-06-07; promoted from §6.2 deferred)*

**Description:** With the MCQ core working, the app now **remembers** what you've practiced across sessions and turns that history into study guidance. Every answered question is persisted locally; the app surfaces accuracy and weak areas, serves questions you haven't seen before *first*, and gives an at-a-glance sense of whether you're ready. This deliberately **reverses the prior no-persistence stance** (see §6) — it remains single-user and local (no accounts, no server-side user data, no sync); persistence is a local store on the user's machine. Technical mechanism (SQLite, schema) lives in `addendum.md`.

**Functional Requirements:**

#### FR-22: Persist attempt history
Each answered Exercise is recorded to a durable local store: at minimum the Exercise `id`, correct/incorrect, a timestamp, and the time taken (per FR-28). History survives app restarts.

**Consequences (testable):**
- Answering a question, restarting the app, and viewing stats reflects the prior answer.
- The store is local and single-user; no network/account is involved. `[ASSUMPTION: recorded at answer time via the existing grade step (POST /api/feedback); displayed-but-unanswered questions are not counted as attempts.]`

#### FR-23: Stats dashboard
The user can view study statistics: overall accuracy and total attempts, **per-Domain** accuracy, a trend over time, and highlighting of weak Domains.

**Consequences (testable):**
- Per-Domain accuracy is shown for every Domain the user has attempted.
- The weakest Domain(s) are visually distinguishable from strong ones.

#### FR-24: Unseen-first prioritization
When building a Practice Session, the runner serves Exercises the user has **not answered before** ahead of already-seen ones (within the active filters). When the unseen pool for the filter is exhausted, it falls back to seen Exercises, preferring least-recently-seen.

**Consequences (testable):**
- With unseen Exercises available for the filter, a session draws from them before any seen Exercise appears.
- When all matching Exercises are seen, the session still proceeds (no empty/blocked state), ordered least-recently-seen first.
- *Supersedes the FR-21 "uniform-random, no anti-repeat memory" assumption for ordering: order is now history-aware (unseen-first), while option sampling/shuffle (FR-20) remains random.*

#### FR-25: Readiness indicator
The app shows a simple "am I ready?" signal — rolling accuracy against the **~70% pass bar**, with per-Domain readiness so the user can see which Domains still need work.

**Consequences (testable):**
- The indicator reflects recent performance (a rolling window, not just lifetime average). `[ASSUMPTION: ~70% is a planning heuristic, not an official per-domain cut — see addendum §C; surface it as guidance, not a guarantee.]`
- Per-Domain readiness is derivable from FR-23's per-Domain accuracy.

**Out of scope (this feature):** Spaced repetition / due-scheduling (SRS) — still deferred (§6.2); FR-24 unseen-first is prioritization, not SRS.

### 4.6 Timed Practice / Mock Exam *(post-MVP scope expansion — decided 2026-06-07; promoted from §6.2 deferred)*

**Description:** Adds exam-realistic time pressure, the part Anki can't replicate. Two flavors: a **lightweight countdown** the user can switch on for any practice session, and a dedicated **Mock-Exam mode** that mirrors the real exam — a domain-weighted, full-length set under the real clock with a single end-of-exam score.

**Functional Requirements:**

#### FR-26: Optional session countdown
Any Practice Session can run with an optional countdown timer: the user sets (or accepts a default) a duration; remaining time is visible; at zero the session auto-ends to the summary.

**Consequences (testable):**
- With the timer on, remaining time is displayed and decrements; reaching zero ends the session and shows the summary over what was answered (partial summary).
- With the timer off, behavior is unchanged from the untimed runner.

#### FR-27: Mock-Exam mode
A distinct mode that assembles a **domain-weighted, full-length** Exercise set for the selected Exam and runs it under the real exam clock, then shows an exam-style final score. Real parameters: **Associate ≈ 45 questions / 90 minutes; Professional ≈ 59 questions / 120 minutes** (per addendum §C), with the per-Exam domain weights.

**Consequences (testable):**
- Starting a Mock Exam for an Exam builds a set sized to that Exam, weighted by its Domain split, scoped to that Exam (never mixing Associate/Professional — see FR-7.x exam filter).
- The countdown uses the Exam's real duration and auto-submits at zero; the result is an exam-style overall score (with the §4.5 per-Domain breakdown).

#### FR-28: Per-question timing
The app records time taken per answered question, feeding both the timed experience and the stats (FR-22/FR-23).

**Consequences (testable):**
- A per-question elapsed time is captured on answer and stored with the attempt (FR-22).

### 4.7 Multi-Provider / Multi-Certification Support *(rev 5 — active scope; Epic 9)*

**Description:** The pivot from a Databricks-only tool to a **provider-agnostic** companion. The data model and vocabulary gain **Provider** and **Certification** (§3); each Certification's blueprint (canonical Domain list, Domain weights, exam parameters — question count, duration, pass-bar heuristic) is declared in **configuration** rather than hardcoded. Adding a new certification — from any provider — becomes a **content + config** task with **no app code change**. Databricks DE Associate/Professional are preserved as the first bundled Certifications. This iteration delivers the model + config + the existing one provider; a provider/cert *switcher UI* and a bundled *second* provider's real content are deferred (decision-log #40).

**Functional Requirements:**

#### FR-29: Per-Certification configuration
Each Certification declares, in configuration (not code): its Provider, display name, canonical Domain list, per-Domain weights, and exam parameters (question count, duration in minutes, pass-bar heuristic). The app reads these to drive Domain filtering, mock-exam weighting/sizing/timing, and readiness. The Databricks DE Associate/Professional values currently embedded in code (e.g. the 45Q/90min, 59Q/120min mock parameters and the per-Exam domain lists) are migrated into this configuration.

**Consequences (testable):**
- The canonical Domain list, weights, and exam parameters for a Certification are sourced from configuration; changing them requires no code edit.
- Mock-exam sizing/timing (FR-27) and the per-Exam domain UI (Story 6.7) read from the configuration rather than hardcoded Databricks values.
- A Certification whose Exercises reference a Domain absent from its configured list is flagged in validation (ties to FR-4).
- `[ASSUMPTION: configuration is a file-based, version-controlled, human-authorable artifact (e.g. YAML), loaded at startup like content. Exact location/format → addendum §G.]`

#### FR-30: Multi-Certification content organization & selection
The content corpus is organized so multiple Providers/Certifications coexist, and the learner can choose which Certification to study. This **generalizes** the existing Associate/Professional exam filter (Story 6.7): the selector becomes Provider → Certification, and a session is always scoped to one Certification (never mixing across Certifications, as it already never mixes Associate/Professional).

**Consequences (testable):**
- A session/start screen scopes practice to a single chosen Certification; its Domain options are that Certification's Domains only.
- Adding a new Certification's content files + config makes it selectable without code changes (with the seed corpus, Databricks DE remains fully available).
- `GET /api/sessions`, `GET /api/exercises/count`, and stats/readiness respect the chosen Certification (generalizing the existing `exam` filter param).

### 4.8 Shareable via Docker Compose *(rev 5 — active scope; Epic 10)*

**Description:** Make the app trivially shareable with colleagues. A single `docker compose up` from a clone of the repo brings the whole app (frontend + backend + bundled content) up locally, with **no host toolchain required** (no local Node, Python, or `uv` install). Each colleague runs their **own** instance; their practice history persists locally (a mounted volume holds the SQLite store). This is **not** a hosted multi-user service — it is one-command local packaging (decision-log #35). Containerization mechanics (Dockerfiles, compose file, ports, the SQLite volume) live in `addendum.md` §H.

**Functional Requirements:**

#### FR-31: One-command containerized run
The app runs end-to-end via a single `docker compose up` against a checked-out repo: the compose stack builds/starts the backend and frontend, serves the bundled content, and exposes the app at a documented local URL. Practice history persists across `docker compose down`/`up` via a mounted volume.

**Consequences (testable):**
- On a machine with only Docker installed (no Node/Python/uv), `docker compose up` yields a working app reachable at the documented local URL.
- Answer history written in one run is still present after `docker compose down` then `docker compose up` (volume-backed SQLite store survives container recreation).
- The README documents the one-command flow so a colleague can self-serve.
- `[ASSUMPTION: a single compose project serves both services; production hardening/hosting is out of scope — this is local distribution. Build-time vs. runtime content mounting → addendum §H.]`

**Feature-specific NFR:**
- **NFR-5 (shareability):** the app runs with **only Docker** on the host — no local Node, Python, or `uv` install required. This is what makes "share with a colleague" a one-command reality rather than a setup ordeal.

### 4.9 Question Feedback & Content-Improvement Loop *(rev 6 — active scope; Epic 11)*

**Description:** Close the loop between *studying* and *improving the content*. While practicing, the learner can flag a question with a quick **free-text note** ("the explanation is wrong", "two options are basically the same", "outdated — Lakeflow not DLT"). Notes are **persisted to a sidecar feedback file** (a separate YAML keyed by Exercise `id`), leaving the hand-authored Exercise files pristine. Later, the **`write-mcq` authoring skill** reads that accumulated feedback and **revises the flagged questions in place** in their source YAML, then marks the feedback **resolved** — turning real study friction into a steadily better content bank.

This adds the **first in-app write path** and is a **narrow, deliberate reversal** of the "Not a content authoring UI" non-goal (§5): the app may now *capture feedback notes*, but it still does **not** edit questions, options, explanations, or config in-app — that remains file/skill-authored. Mechanism (sidecar schema, write endpoint, the docker writable-mount implication) lives in `addendum.md` §I.

**Functional Requirements:**

#### FR-32: Capture question feedback in-app, persisted to a sidecar file
From the practice surface, the learner can attach a free-text feedback note to the current Exercise. The note is saved to a **sidecar feedback file** (YAML, keyed by Exercise `id`), surviving app restarts, **without modifying the authored Exercise file**.

**Consequences (testable):**
- Submitting a note on an Exercise, restarting the app, and re-opening that Exercise's feedback shows the prior note.
- The authored Exercise YAML is **byte-unchanged** by feedback submission (only the sidecar file is written).
- Each feedback entry records at least the Exercise `id`, the note text, a timestamp, and a `resolved` flag (default false).
- A feedback note is available on any Exercise type (keyed by `id`); acting on it via the skill is MCQ-first (FR-33).
- `[ASSUMPTION: a new write endpoint appends to the sidecar; the sidecar lives alongside content (e.g. exercises/feedback.yaml). Whether feedback is committed (travels with content) or kept local-per-instance is OQ-9. Mechanism → addendum §I.]`

#### FR-33: Skill-driven revision of flagged questions from feedback
The `write-mcq` authoring skill can take an Exercise's accumulated feedback into account to **revise the question in place** in its source YAML (fixing the flagged issue), and then **mark the corresponding feedback entries resolved**. The author reviews the change before it lands (it is a normal file edit under version control).

**Consequences (testable):**
- Given a sidecar feedback entry for an Exercise, running the skill produces a revised Exercise (corrected per the note) and the feedback entry is marked `resolved` (or removed).
- The skill only touches Exercises that have **open** (unresolved) feedback; resolved entries are skipped.
- The revised Exercise still passes content validation (Option Pool rules, domain, etc. — FR-1/FR-19).
- `[ASSUMPTION: revision is MCQ-first via write-mcq; a parallel write-code-completion revision path is a later extension. The skill edits in place and the author reviews the diff — no separate approval UI.]`

## 5. Non-Goals (Explicit)

- **Not a hands-on lab platform.** No cluster execution, no running real Spark/SQL against data. These exams have no live coding; neither does this app.
- **Not a hosted, multi-user service.** *(Retained, rev 5.)* Sharing is **per-own-instance** (decision-log #35): each colleague runs their own `docker compose up` with their own local SQLite history. No accounts, no auth, no multi-user/server-side user data, no sync, no shared deployment. The local single-user answer store (§4.5) is local-only persistence, per instance.
- **Not a content authoring UI — except for capturing feedback notes.** *(Narrowed, rev 6.)* Exercises (and per-Certification config) are still authored as files (by hand or agent skill); the app does **not** edit questions, options, explanations, or config in-app. The one exception (§4.9, FR-32): the app may capture **learner feedback notes** to a sidecar file. That is a write path, but not an editor — revising the actual content stays file/skill-authored (FR-33).
- **Not a braindump of real exam questions.** Content is original and blueprint-aligned; provenance is tracked. (Credibility + avoids candidate exam-bans.) Applies to every bundled Certification, not just Databricks DE.
- **~~Not multi-cert beyond Databricks DE~~ — REVERSED (rev 5).** Multi-Provider / multi-Certification is now the explicit direction (§4.7, FR-29/FR-30). Databricks DE is the first bundled Certification, not the only supported one.
- **Not a general LMS / course platform.** No videos, no curriculum sequencing, no certificates. (Generalizing across certifications does not make this an LMS — it remains a practice-drill companion.)
- **Not a full provider/certification switcher UI or a second bundled provider's content — this iteration.** *(Deferred, rev 5, decision-log #40.)* The model + config + one bundled provider (Databricks) ship now; a polished in-app provider/cert switcher and shipping another provider's real content bank are future work.

## 6. MVP Scope

### 6.0 Build-vs-Borrow decision *(decided 2026-06-05)*

With an exam ~1–2 months out and a solo builder, **time spent building is time not studying.** The MCQ practice loop is table-stakes (every cert tool has it), while the content bank and the Wordle-style drill are the parts worth owning. The decision:

- **Borrow / go-lean for MCQ study now.** The content bank (§6.1) is authored in the portable format and studied immediately — via Anki (FR-18) or a deliberately lean built-in runner — whichever is faster to get in front of the learner. Studying must never block on app polish.
- **Build for the novelty later.** The bespoke app's justified, from-scratch investment is the **Wordle-style Code-Completion drill** (§4.3) — genuinely under-served, no real incumbent. It was sequenced last (originally "Phase 2"), after the exam-critical content + study path; **promoted to active scope as Epic 4 on 2026-06-08** (§6.4).

This makes the **content bank the primary MVP deliverable** and the app shell secondary.

### 6.1 In Scope (MVP — the exam-critical core)
- **Content bank — the primary deliverable.** A committed starter bank of **~50–75 original, blueprint-aligned MCQs**, distributed across the 5 **Associate** Domains roughly by their official weights (per addendum §C). Each authored as an **Option Pool** (FR-19: ≥1 correct, ≥3 incorrect, extra alternatives/distractors encouraged), with per-distractor Explanation and a reference link.
- **Committed agent-skill authoring track.** A lightweight Claude agent skill that authors Exercises into the standardized format (4.1) is a committed parallel workstream, runnable independent of app progress (resolves former OQ-5). `[ASSUMPTION: the authoring skill is specced/built as its own small workstream; exact spec TBD.]`
- **Portable, parseable Exercise format** (4.1: FR-1, FR-2, FR-3-lean, FR-4, **FR-18 export to Anki**) — enough that the content above is studiable *today*.
- **A study path that works now:** either Anki import (FR-18) **or** the lean built-in MCQ runner (4.2: FR-5–FR-12, plus the freshness features FR-20 option sampling/shuffle and FR-21 randomized question order). At least one must be usable well before the exam; the lean runner is not a prerequisite for studying. `[NOTE FOR PM] FR-20 (per-display option sampling/shuffle) and FR-21 (randomized order) are **runner** behaviors and do not survive a one-shot Anki export — Anki provides its own shuffle/scheduling, and the export flattens each pool to a single correct Option + distractors. The Option Pool's full freshness benefit (FR-19/FR-20) is realized only in the built-in runner.]`

### 6.2 Out of Scope for MVP (phased)
- ~~**Code-Completion ("Wordle") Practice (4.3)** — Phase 2~~ → **PROMOTED to active scope (§4.3, FR-13–FR-17; Epic 4)** — 2026-06-08. The build-worthy novel feature, sequenced last (after the exam-critical content + study path and the Epic 7/8 richer-MCQ experience). The throwaway-spike plan was dropped in favor of committing the FR set directly (model + per-concern stories — see §4.3 Notes).
- **Heavyweight content validation / partial-load** (the elaborated form of FR-3) — *cut for v1.* Single author; a clear failure is enough.
- ~~**Timed mock-exam mode**~~ → **PROMOTED to active scope (§4.6, FR-26/27/28; Epic 8)** — 2026-06-07.
- ~~**Weak-area analytics & readiness**~~ → **PROMOTED to active scope (§4.5, FR-22–FR-25; Epic 7)** — 2026-06-07. Brings in **local persistence** (reverses the prior no-persistence stance).
- **Spaced repetition (SRS)** — *still deferred.* (FR-24 unseen-first is prioritization, not SRS; borrowing Anki gives SRS in the interim.)
- **In-app Exercise generation from docs (4.4)** — *optional/deferred.* Agent-skill authoring is the committed path.
- **Sharing / hosting / multi-user** — *future, not committed.* Portable format keeps the door open.

### 6.3 Post-MVP scope expansion *(decided 2026-06-07)*
The exam-critical MVP shipped (Epics 1–6: content system, MCQ runner, variety/randomization, session QoL, both Associate + Professional content). With that working, two phases previously deferred in §6.2 are promoted to active scope — **building a richer MCQ study experience before the Code-Completion drill**:
- **Epic 7 — Answer & Stats Tracking** (§4.5): local SQLite persistence, attempt history, stats dashboard, unseen-first prioritization, readiness indicator.
- **Epic 8 — Timed Practice / Mock Exam** (§4.6): optional session countdown + full Mock-Exam mode.

This reverses **NFR: no persistence** (the runner is no longer stateless — it reads/writes a local history store) and supersedes the FR-21 uniform-random ordering assumption (now history-aware, FR-24). Single-user/local is retained. Architecture impact (SQLite layer, schema, record-on-feedback hook, mock-exam session builder) is captured in `addendum.md` for the architecture phase.

### 6.4 Final scope promotion: Code-Completion *(decided 2026-06-08)*
Epics 7 & 8 complete (stats tracking, timed practice / mock exam — verified). The last deferred feature, the **Code-Completion ("Wordle") drill (§4.3)**, is now promoted to active scope as **Epic 4 — the final epic**. It was always the build-worthy differentiator; it is built last because the exam-critical MCQ path and the richer-study experience came first (§6.0 Build-vs-Borrow).

**Scope of Epic 4 (FR-13–FR-17, NFR-1):**
- **Runner & feedback (stories 4.1–4.5):** the `CodeCompletion` page + template display (4.1, which also stops the session builder from skipping code-completion and routes the `practice` view by exercise type); a pure client-side **tokenizer** (4.2) and **positional-feedback engine** (4.3); **FeedbackTokens** rendering with color-independence (4.4); and the **guess-limit + reveal + explanation** loop (4.5).
- **Content & authoring (story 4.6 — committed 2026-06-08):** a **starter Code-Completion bank** (SQL + PySpark, current Databricks terminology) **and a `write-code-completion` authoring skill**, mirroring the committed MCQ authoring track (§6.1). This closes the content gap — no Code-Completion content exists today, and the `write-mcq` skill is MCQ-only — so SM-4 ("the drill teaches syntax") is actually achievable.

**Key decisions (2026-06-08):**
- **Feedback is client-side** (NFR-1); **no `POST /api/feedback/code-completion`** endpoint (resolves a stale architecture-doc reference that contradicted the < 100ms client-side target). The active exercise's answer is delivered to the client — a documented trade-off that does not relax MCQ non-leakage (§4.3, FR-14).
- **Code-Completion attempts are NOT recorded** in the SQLite attempt store (it is MCQ-scoped, Epic 7) and do not feed the stats/readiness signals or per-question timing (FR-28 is MCQ-scoped). Recorded as a known gap; closing it would be a future story.
- Architecture impact (session-builder code-completion delivery, client-side tokenizer/feedback modules, the removed server endpoint, attempt-budget constant) is captured in `addendum.md` §F for the architecture realignment (architecture rev 5).

### 6.5 Current iteration: Generalization + Shareability *(decided 2026-06-09, rev 5)*
With Epics 1–8 + Epic 4 shipped (full MCQ + stats + timed/mock + code-completion, both Databricks DE Certifications), the next step is **sharing the app with colleagues** and **opening it to other providers' certifications**. Two new active-scope workstreams:
- **Epic 9 — Multi-Provider / Multi-Certification** (§4.7, FR-29/FR-30): introduce **Provider** + **Certification**, move per-Certification Domain lists/weights/exam params from hardcoded values into **configuration**, generalize the `exam` filter to a Provider→Certification selection. **Preserve all Databricks DE content** — it becomes the first bundled Certification(s). Architecture impact (config schema/loader, `exam`→certification semantics) → `addendum.md` §G.
- **Epic 10 — Containerization & Sharing** (§4.8, FR-31): Dockerfiles for frontend + backend, a `docker-compose.yml`, and a mounted volume for the SQLite store, so a colleague runs the whole app with one `docker compose up` and no host toolchain. **Reverses the "no containerization for MVP" stance.** Mechanism → `addendum.md` §H.

**In scope this iteration:** the provider-agnostic data model + per-Certification config + one bundled Provider (Databricks) + one-command docker-compose run.
**Deferred (decision-log #40):** a polished in-app Provider/Certification switcher UI; bundling a *second* provider's real content; per-provider blueprint-source validation. The model is built so these are additive later.

## 7. Success Metrics

*Hobby/personal scope — kept lean.*

**Primary**
- **SM-1 (the real one):** Dario studies regularly through to exam day and **passes** the Databricks DE Associate exam. Validates the product's reason to exist.
- **SM-2:** The committed content bank exists and is studiable — **~50–75 MCQs across all five Associate Domains**, weighted roughly by the official split, consumable via Anki or the lean runner — **well before** exam day. Validates FR-1, FR-4, FR-18, and §6.1.

**Secondary**
- **SM-3:** Authoring a new Exercise and getting it into the study path takes only writing a file (+ a one-shot export) — **no app code changes**. Validates FR-1–FR-3, FR-18.
- **SM-4 (Epic 4):** The Code-Completion feedback feels instant (client-side, < 100ms) and *teaches* syntax (Dario can recall a drilled snippet unaided afterward), backed by a real starter bank (story 4.6, not just seed items). Validates FR-13–FR-17 + NFR-1.
- **SM-5 (stats):** History persists across sessions and the dashboard shows per-Domain accuracy + a readiness signal Dario actually uses to decide what to drill next; unseen-first means he isn't re-served questions he's already done while fresh ones remain. Validates FR-22–FR-25.
- **SM-6 (timed):** Dario can take a full domain-weighted Mock Exam under the real clock (Associate 45Q/90min, Pro 59Q/120min) and gets an exam-style score — the timed-exam feel Anki can't give. Validates FR-26–FR-28.
- **SM-7 (generalization, rev 5):** A new Certification can be made selectable and practiced by adding **only** content files + a per-Certification config entry — **no app code change** — while all Databricks DE content keeps working unchanged. Validates FR-29/FR-30.
- **SM-8 (shareability, rev 5):** A colleague with only Docker installed runs `docker compose up` against a clone and is studying within minutes, on their own instance, with history that survives a restart. Validates FR-31.

**Counter-metrics (do not optimize)**
- **SM-C1:** Don't optimize for **app features / polish** at the expense of **content volume and exam readiness**. Counterbalances SM-1; a beautiful app with 12 questions fails the actual job. This is the whole point of the Build-vs-Borrow decision (§6.0) — borrow the runner, invest the hours in content.
- **SM-C2:** Don't optimize the Wordle feature's cleverness at the expense of shipping the MCQ core. Counterbalances SM-4.
- **SM-C3 (rev 5):** Don't let generalization regress Databricks DE. The provider-agnostic refactor must not break or dilute the existing, working Databricks DE study experience — generality is worthless if it costs the one Certification that actually exists. Counterbalances SM-7.
- **SM-C4 (rev 5):** Don't let "shareable" drift into "hosted." Resist adding accounts/auth/shared-DB/networked-multi-user under the banner of sharing — the goal is one-command local distribution, not operating a service. Counterbalances SM-8.

## 8. Open Questions

1. **OQ-1 (confirm before authoring):** Verify the **Associate exam domain list and their weights** against the live official Databricks PDF exam guide. The original MCQs will be authored to the current official documentation (Lakeflow Pipelines, not DLT; etc.), not reverse-engineered from real exam questions (which are proprietary). Domain list + weights are the only gate — they shape the content prioritization. Discovery research was model-knowledge-based (no live network); the addendum domains/weights are provisional. Other facts (question counts, passing score, price) are nice-to-know but not blocking content authoring.
2. **OQ-2:** Final Exercise schema details — file granularity (one Set per file vs. many), content directory location, and whether YAML-author/JSON-serve is worth the extra step for a single-user local app.
3. **OQ-3 (resolved → revised 2026-06-10):** Code-Completion feedback semantics = **character-level green/yellow/grey** (per-letter Wordle), computed **client-side**. This **reverses** the 2026-06-05 token-level resolution (#11/#29) — single-word answers made token-level binary. Char-level engine + per-character rendering + Skip are spec'd in **Story 4.8**; the regex tokenizer is removed. See decision-log #54/#55, addendum §F.
4. **OQ-4 (resolved):** Starter content target = **~50–75 Associate MCQs weighted by domain split** (decided 2026-06-05, §6.1). Open sub-question: confirm this is enough for *your* confidence as exam day nears (top up if weak domains emerge).
5. **OQ-5 (resolved → committed):** The agent-skill authoring path **is** a committed parallel workstream (§6.1). Open sub-question: its exact spec (input prompts, output validation, dedup) — small follow-up, not a blocker.
6. **OQ-6 (rev 5 — config schema):** Final shape/location of the per-Certification configuration (FR-29) — one file per Certification vs. a single registry; how Providers nest; whether config lives beside `exercises/` or in its own directory. Proposed in addendum §G; confirm during architecture rev 6. Not blocking the decision to generalize, only the file layout.
7. **OQ-7 (rev 5 — content reorg):** How far to reorganize the existing `exercises/associate/` + `professional/` tree to reflect Provider→Certification (e.g. `exercises/databricks/de-associate/…`) vs. leaving the current layout and expressing Provider/Certification purely via the `exam`/config mapping. Trade-off: cleaner tree vs. churn to existing content paths. Decide in Epic 9 story breakdown.
8. **OQ-8 (rev 5 — content mount):** Whether the docker-compose stack **bakes content into the image** (simplest to share a fixed snapshot) or **mounts the repo `exercises/`** (lets a colleague edit/add content without rebuilding). Likely support the mount for authoring convenience; confirm in addendum §H / architecture. *(Note: FR-32's feedback writeback requires a **writable** content mount — reinforces the mount option.)*
9. **OQ-9 (rev 6 — feedback lifecycle) — RESOLVED 2026-06-11: local-per-instance (gitignored).** `exercises/feedback.yaml` is **gitignored**, not committed — like the SQLite history store, each instance's feedback stays on its own machine, avoiding cross-writing when the app is shared (Epic 10). The `write-mcq` revision skill reads whatever feedback is local when the author sits down to fix questions. (Decision-log #57.)

## 9. Assumptions Index

*Every `[ASSUMPTION]` in the document, surfaced for confirmation:*

- §4.1 — Authoring format is YAML, one Exercise Set per file, loaded from a known content directory.
- §4.1 / FR-2 — Content is read from files at runtime, not compiled into the app.
- §4.1 / FR-19 — Multiple correct Options in an Option Pool are interchangeable *alternatives* (any one is valid alone), not a jointly-required set.
- §4.2 / FR-20 — Displayed-Option sampling is uniform-at-random per presentation, with no anti-repeat memory in MVP.
- §4.2 / FR-21 — Exercise order is re-randomized fresh each session; no resume-in-order weighting. *(Superseded for ordering by FR-24 unseen-first as of 2026-06-07; option sampling/shuffle remains random.)*
- §4.5 / FR-22 — Attempts are recorded at grade time (POST /api/feedback); displayed-but-unanswered questions don't count as attempts. Store is local, single-user.
- §4.5 / FR-25 — ~70% pass bar is a planning heuristic (addendum §C), surfaced as guidance not a guarantee; readiness uses a rolling window.
- §4.6 / FR-27 — Mock-Exam sizing/timing uses the verified per-Exam parameters (Associate 45Q/90min, Professional 59Q/120min) and per-Exam domain weights (addendum §C).
- §4.1 / FR-18 — Anki is the borrow/export target; a one-shot converter (script) is acceptable rather than live two-way sync.
- §4.2 / FR-6 — Backward navigation within a session is allowed but not required for MVP.
- §4.2 / FR-10 — Reference links open externally in the browser.
- §4.3 — Code-Completion design stance is **CONFIRMED** (2026-06-08; feedback granularity revised 2026-06-10): single-line/fill-in-blank scope, whitespace-insensitive (`ignore_whitespace`), explicit per-language case policy (`case_sensitive`), **character-level (per-letter) green/yellow/grey** (was token-level — reversed per #54), authored `accepted` alternatives, plus a **Skip** control (#55) — locked in the `CodeCompletion` model + Epic 4 stories (4.8 for char-level + Skip).
- §4.3 / FR-14 — **Feedback is client-side; no server endpoint.** Consequence: the active exercise's canonical answer + accepted alternatives are delivered to the client. Acceptable for the Wordle drill (no gaming surface; the loop reveals the answer anyway); does **not** relax MCQ non-leakage (FR-20).
- §4.3 — Code-Completion attempts are **not** persisted to the (MCQ-scoped) attempt store and do not feed stats/readiness/per-question timing. Known gap; future story if wanted.
- §4.3 / FR-16 — Alternative-answer matching is against an authored alternatives list; AST/execution equivalence is out of scope.
- §6.4 — Code-Completion content is authored as its own committed workstream (starter bank + `write-code-completion` skill, story 4.6), mirroring the MCQ authoring track.
- §6.1 — The agent-skill authoring path is specced/built as its own small workstream; exact spec TBD.
- §4.7 / FR-29 — Per-Certification configuration is a file-based, version-controlled, human-authorable artifact (e.g. YAML) loaded at startup; exact location/format → addendum §G (OQ-6).
- §3 — "Exam" is retained as the data field identifying a Certification (semantics generalized); `associate`/`professional` are the Databricks DE Certifications. Generalizing the field rather than renaming it keeps the existing exam filter (Story 6.7) and content schema working.
- §4.8 / FR-31 — A single docker-compose project serves both services for **local** distribution; production hardening/hosting is out of scope. Content is likely **mounted** (not only baked) so colleagues can author without rebuilding (OQ-8); addendum §H.
- §4.8 — Each colleague runs their **own** instance; the SQLite store persists via a mounted volume per instance. No shared/networked state (reinforces the retained "not hosted multi-user" non-goal).
- §4.9 / FR-32 — Feedback notes are free-text, written to a **sidecar** YAML (`exercises/feedback.yaml`) keyed by Exercise `id` via a new write endpoint; the authored Exercise files are never modified by feedback capture. The sidecar is **gitignored / local-per-instance** (OQ-9 resolved 2026-06-11, decision-log #57). Mechanism in addendum §I.
- §4.9 / FR-33 — Feedback-driven revision is **MCQ-first** via `write-mcq` (edits in place, marks resolved, author reviews the diff); a code-completion revision path is a later extension.

---

## Appendix A. Future Exercise Type Ideas
*Requested by the user for post-Wordle expansion. Not committed; recorded so the format and architecture stay open to them. Each reuses the shared `id`/`domain`/`difficulty`/`explanation` fields.*

- **Output / result prediction** — "Given this PySpark/SQL, what does it return (rows, schema, or error)?" Multiple-choice or short-answer.
- **Spot-the-bug** — present a snippet with a subtle error (wrong trigger mode, missing `checkpointLocation`, bad `MERGE` clause); user identifies/fixes it.
- **Ordering / sequencing** — drag to order steps (medallion bronze→silver→gold, job task dependencies, streaming setup steps).
- **Match terms to definitions** — pair Glossary-style Databricks concepts with definitions (good SRS fodder).
- **Config fill-in** — complete a cluster/job/DLT pipeline config to meet a stated requirement.
- **Scenario / "best approach"** — exam-realistic scenario MCQs ("which ingestion approach fits these constraints?"), heavier for Professional.
- **Rapid-fire true/false** — quick recall warm-ups.
- **Flashcards** — term→definition cards that feed a future SRS, unifying with the analytics/SRS phase.
