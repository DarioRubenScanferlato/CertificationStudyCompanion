---
title: Databricks DE Cert Study Companion
status: final
created: 2026-06-05
updated: 2026-06-07
revision: 3 (scope expansion — stats tracking + timed practice)
---

# PRD: Databricks DE Cert Study Companion
*Working title — confirm.*

## 0. Document Purpose

This PRD is for Dario as the builder, and for the downstream architecture and implementation work it feeds. It defines **what** the study companion must do — not how it is built. The app is being created to help one person (initially) practice for the **Databricks Certified Data Engineer** exams, with an exam ~1–2 months out, so MVP scope is deliberately tight: get exam-realistic multiple-choice practice working first, defer everything else.

Structure: vocabulary is anchored in the Glossary (§3) and used verbatim throughout; features are grouped with globally-numbered Functional Requirements (FRs) nested under them; assumptions are tagged inline as `[ASSUMPTION: …]` and indexed in §9. Technology choices the user raised (React vs HTMX; Rust vs Python+uv) are **out of scope for this PRD** and are recorded in the companion `addendum.md` for the architecture phase. Discovery research (exam structure, comparable products, the "Wordle-for-code" design space, and a proposed exercise file schema) also lives in `addendum.md`.

## 1. Vision

A lightweight, locally-run study companion that turns Databricks Data Engineer exam prep into short, focused practice sessions. Its core loop mirrors the real exam: read a question (often with a code snippet), pick an answer, and immediately learn *why* — with a rationale tied to the exam domain and a link back to the official docs. Because the exam is entirely multiple-choice with no live coding, exam-realistic MCQ practice is the heart of the product and ships first.

Beyond the exam itself, the app aims to build genuine **syntax fluency** in Spark SQL and PySpark through a second, novel exercise type: a "Wordle-style" code-completion drill that gives positional feedback as you type code. This is a deliberately differentiated, under-served idea — most cert tools stop at multiple choice — and it is sequenced after the MCQ core precisely because it carries the most design risk.

The companion is content-driven, and the **content bank is the durable product** — not the app shell. Exercises live in a simple, human-authorable, version-controlled, **portable** file format that the user (or a Claude agent skill) writes by hand. Because the format is portable, the content can be studied immediately through an existing tool (e.g. exported to Anki) while the bespoke app matures — so passing the exam is never blocked on finishing the build. The app's value grows by adding content rather than code, and the same portability keeps a future "share it with other candidates" path open without committing to it now.

This reframes the build: **borrow for the deadline, build for the novelty.** Exam-realistic MCQ practice is table-stakes and can be served immediately by a lean built-in runner *or* a borrowed tool; the genuinely under-served, worth-building-from-scratch piece is the Wordle-style code-completion drill. See §6's Build-vs-Borrow decision.

## 2. Target User

### 2.1 Jobs To Be Done
- **As the builder/learner:** "I have a Databricks DE certification exam in ~1–2 months and I want to drill exam-style questions and check my answers with explanations, so I walk in confident." (This is for me first — a valid and primary framing.)
- **Practice syntax I keep fumbling:** "I want to rehearse Spark SQL / PySpark syntax (MERGE, Auto Loader options, DLT decorators, window functions) until it's automatic, not just recognizable."
- **Study in small chunks:** "I want to do a 10–15 minute session on a specific domain (e.g. Incremental Data Processing) when I have a gap, not commit to a whole mock exam."
- **Grow my own bank:** "I want to author or generate new questions cheaply and have them just show up in the app."
- *(Latent, deferred)* **Share with peers:** "If this turns out useful, I'd like to hand it to other candidates without a painful rewrite."

### 2.2 Non-Users (v1)
- Other cert candidates as *end users on shared/hosted infrastructure* — v1 is single-user and local; sharing is a future consideration, not a v1 audience.
- Candidates for non-Data-Engineer Databricks certs (ML, Data Analyst, etc.) — out of scope, though the format could extend later.
- Learners wanting hands-on lab/cluster execution — the exam has no live coding and neither does this app.

### 2.3 Key User Journeys
*Single operator (the builder). Journeys kept light per scope; they exist to pin down the core loop, not to drive heavy UX.*

- **UJ-1. Dario drills a weak domain over coffee.**
  Dario has ~15 minutes and knows Incremental Data Processing is his weak spot. He opens the app (running locally), picks a practice set filtered to that domain, and works through multiple-choice questions one at a time, in randomized order. For each, he sees four options (one correct, three distractors) in shuffled positions, selects an answer, submits, and immediately sees whether he was right, a rationale for the correct answer and why the distractors are wrong, and a link to the relevant Databricks doc. At the end he sees a simple score for the session. Realizes FR-5 through FR-12 and FR-20/FR-21. **Re-study behavior:** when Dario revisits this domain the next day, questions appear in a different order (FR-21), and a previously-seen question may show a different correct option and/or different distractors drawn from its Option Pool (FR-19/FR-20) — so it feels fresh rather than memorized-by-position.

- **UJ-2. Dario rehearses PySpark syntax he keeps forgetting.** *(Phase 2)*
  Dario can never remember the exact Auto Loader options. He opens a code-completion exercise: a short prompt ("Configure Auto Loader to infer and evolve schema") and a code template with a blank. He types his attempt; the app gives Wordle-style positional feedback (correct tokens highlighted) and lets him try again within a guess limit. When he solves it (or runs out of guesses), he sees the canonical answer and a short explanation. Realizes FR-13 through FR-17. **Edge case:** he types a *valid alternative* phrasing (`df.where` vs `df.filter`) — the exercise accepts it rather than marking it wrong (FR-16).

## 3. Glossary

*Downstream workflows and readers must use these terms exactly. No synonyms elsewhere in the PRD.*

- **Exam** — A Databricks Certified Data Engineer certification exam. Two exist: **Associate** and **Professional**. v1 content seeds Associate; the taxonomy supports both.
- **Domain** — An official exam-blueprint topic area with a weight (e.g. "Incremental Data Processing"). Every Exercise is tagged with exactly one Domain. The canonical Domain list per Exam is defined by Databricks' current exam guide.
- **Subdomain** — An optional finer topic tag within a Domain (e.g. "Auto Loader" within "Incremental Data Processing").
- **Exercise** — A single practice item the user attempts. Two **Exercise Types** exist: **MCQ** and **Code-Completion**. Every Exercise has a stable `id`, a Domain, a difficulty, and an explanation.
- **MCQ (Multiple-Choice Question)** — An Exercise presenting a question (optionally with a code snippet) and an **Option Pool**; at each presentation the runner shows four **Displayed Options** (one correct, three incorrect) and the user selects one and submits. **Single-select only** — the multi-select ("select all that apply") variant is removed (decision 2026-06-05; see §4.2 and decision log).
- **Code-Completion Exercise** — The "Wordle-style" Exercise Type: a code template with a blank (or a prompt) that the user completes by typing, receiving positional feedback. (Phase 2.)
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
Domains (and the per-Exam canonical Domain list) align with Databricks' official exam blueprint, so content can be filtered and — later — weighted to mirror the real exam.

**Consequences (testable):**
- Every Exercise resolves to exactly one Domain from the canonical list for its Exam.
- An Exercise tagged with an unknown Domain is flagged in validation.

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
- Persisting session history across runs (that's the analytics phase — see §6.2).
- Timed/countdown mode (deferred — §6.2).

### 4.3 Code-Completion ("Wordle-style") Practice *(Phase 2 — after MVP)*

**Description:** A novel syntax-drilling Exercise Type and the product's key differentiator. The *feel* is load-bearing, not incidental: the playful, Wordle-like **guess-and-narrow** loop — attempt, see colored feedback, refine — is the reason this is more engaging than a flashcard, and the design should preserve that delight rather than reduce it to a correctness check. The user is given a short prompt and a code template containing a blank (e.g. a `MERGE` statement with the `WHEN NOT MATCHED` arm blanked, or an Auto Loader `.option(...)`), types an attempt, and receives **Positional Feedback** in the Wordle spirit. Discovery research surfaced real design hazards in porting Wordle literally to code; the FRs below encode the research-recommended shape rather than a naive per-character clone. The detailed feedback algorithm and rendering approach belong to architecture/design and are captured in `addendum.md`.

**Design stance (from research, carried as assumptions to confirm):**
- **CONFIRMED:** Positional Feedback uses **green / yellow / grey at the TOKEN level** (a token = keyword/identifier/operator/literal), not literal per-character. Green = correct token in the correct slot; yellow = token present in the answer but in the wrong slot; grey = token not in the answer. Token-level is chosen because per-character "yellow" is misleading in code where position is syntactically rigid.
- `[ASSUMPTION: each exercise is scoped to a SINGLE line or a single fill-in-the-blank slot, not a whole multi-line snippet, to keep feedback legible.]`
- `[ASSUMPTION: non-semantic whitespace is ignored in matching; the user is not penalized for indentation/spacing.]`
- `[ASSUMPTION: a case policy is explicit per language (SQL keywords case-insensitive; PySpark identifiers case-sensitive).]`
- `[ASSUMPTION: multiple valid answers are accepted via an authored "accepted alternatives" set.]`

**Functional Requirements:**

#### FR-13: Present a Code-Completion Exercise
The app presents the prompt, the code template with its blank/slot clearly indicated, and the input affordance. Realizes UJ-2.

**Consequences (testable):**
- The template renders in monospace with the blank visibly marked.
- The target language (SQL or PySpark) is indicated.

#### FR-14: Accept a typed attempt and give Positional Feedback
On an attempt, the app evaluates it against the canonical answer and renders Positional Feedback: content correct and in the right place vs. correct content in the wrong place vs. content not in the answer.

**Consequences (testable):**
- Feedback is computed and shown without a server round-trip perceptible to the user (target < 100ms; see NFR).
- Whitespace handling follows the ignore-non-semantic-whitespace assumption.

#### FR-15: Limited guesses with reveal
The user has a bounded number of attempts; on solving or exhausting attempts, the canonical answer is revealed.

**Consequences (testable):**
- The remaining-attempts count is visible.
- On the final failed attempt, the canonical answer and Explanation are shown.

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

**Notes:** `[NOTE FOR PM] This is the riskiest feature. Recommend a throwaway design spike on the token-level feedback algorithm + rendering before committing the full FR set. Feedback semantics are decided (token-level green/yellow/grey); the spike validates the tokenizer and rendering, not the color model.]`

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

## 5. Non-Goals (Explicit)

- **Not a hands-on lab platform.** No cluster execution, no running real Spark/SQL against data. The exam has no live coding; neither does this app.
- **Not a hosted, multi-user service in v1.** Single-user, local. No accounts, no auth, no multi-user/server-side user data, no sync. *(As of 2026-06-07, a **local** single-user store for the user's own answer history is in scope — §4.5; this is local-only persistence, not hosted user data.)*
- **Not a content authoring UI.** Exercises are authored as files (by hand or agent skill); the app consumes them. No in-app exercise editor in v1.
- **Not a braindump of real exam questions.** Content is original and blueprint-aligned; provenance is tracked. (Credibility + avoids candidate exam-bans.)
- **Not a general LMS / course platform.** No videos, no curriculum sequencing, no certificates.
- **Not multi-cert beyond Databricks DE** in v1 (no ML/Analyst certs), though the format is designed not to preclude it.

## 6. MVP Scope

### 6.0 Build-vs-Borrow decision *(decided 2026-06-05)*

With an exam ~1–2 months out and a solo builder, **time spent building is time not studying.** The MCQ practice loop is table-stakes (every cert tool has it), while the content bank and the Wordle-style drill are the parts worth owning. The decision:

- **Borrow / go-lean for MCQ study now.** The content bank (§6.1) is authored in the portable format and studied immediately — via Anki (FR-18) or a deliberately lean built-in runner — whichever is faster to get in front of the learner. Studying must never block on app polish.
- **Build for the novelty later.** The bespoke app's justified, from-scratch investment is the **Wordle-style Code-Completion drill** (§4.3) — genuinely under-served, no real incumbent. It is Phase 2, after the exam-critical content + study path exist.

This makes the **content bank the primary MVP deliverable** and the app shell secondary.

### 6.1 In Scope (MVP — the exam-critical core)
- **Content bank — the primary deliverable.** A committed starter bank of **~50–75 original, blueprint-aligned MCQs**, distributed across the 5 **Associate** Domains roughly by their official weights (per addendum §C). Each authored as an **Option Pool** (FR-19: ≥1 correct, ≥3 incorrect, extra alternatives/distractors encouraged), with per-distractor Explanation and a reference link.
- **Committed agent-skill authoring track.** A lightweight Claude agent skill that authors Exercises into the standardized format (4.1) is a committed parallel workstream, runnable independent of app progress (resolves former OQ-5). `[ASSUMPTION: the authoring skill is specced/built as its own small workstream; exact spec TBD.]`
- **Portable, parseable Exercise format** (4.1: FR-1, FR-2, FR-3-lean, FR-4, **FR-18 export to Anki**) — enough that the content above is studiable *today*.
- **A study path that works now:** either Anki import (FR-18) **or** the lean built-in MCQ runner (4.2: FR-5–FR-12, plus the freshness features FR-20 option sampling/shuffle and FR-21 randomized question order). At least one must be usable well before the exam; the lean runner is not a prerequisite for studying. `[NOTE FOR PM] FR-20 (per-display option sampling/shuffle) and FR-21 (randomized order) are **runner** behaviors and do not survive a one-shot Anki export — Anki provides its own shuffle/scheduling, and the export flattens each pool to a single correct Option + distractors. The Option Pool's full freshness benefit (FR-19/FR-20) is realized only in the built-in runner.]`

### 6.2 Out of Scope for MVP (phased)
- **Code-Completion ("Wordle") Practice (4.3)** — *Phase 2.* The build-worthy novel feature, but sequenced after the exam-critical content + study path. Begin with a throwaway design spike (tokenizer + rendering).
- **Heavyweight content validation / partial-load** (the elaborated form of FR-3) — *cut for v1.* Single author; a clear failure is enough.
- ~~**Timed mock-exam mode**~~ → **PROMOTED to active scope (§4.6, FR-26/27/28; Epic 8)** — 2026-06-07.
- ~~**Weak-area analytics & readiness**~~ → **PROMOTED to active scope (§4.5, FR-22–FR-25; Epic 7)** — 2026-06-07. Brings in **local persistence** (reverses the prior no-persistence stance).
- **Spaced repetition (SRS)** — *still deferred.* (FR-24 unseen-first is prioritization, not SRS; borrowing Anki gives SRS in the interim.)
- **In-app Exercise generation from docs (4.4)** — *optional/deferred.* Agent-skill authoring is the committed path.
- **Sharing / hosting / multi-user** — *future, not committed.* Portable format keeps the door open.

### 6.3 Post-MVP scope expansion *(decided 2026-06-07)*
The exam-critical MVP shipped (Epics 1–6: content system, MCQ runner, variety/randomization, session QoL, both Associate + Professional content). With that working, two phases previously deferred in §6.2 are promoted to active scope — **building a richer MCQ study experience before the Code-Completion drill (Epic 4, still Phase 2)**:
- **Epic 7 — Answer & Stats Tracking** (§4.5): local SQLite persistence, attempt history, stats dashboard, unseen-first prioritization, readiness indicator.
- **Epic 8 — Timed Practice / Mock Exam** (§4.6): optional session countdown + full Mock-Exam mode.

This reverses **NFR: no persistence** (the runner is no longer stateless — it reads/writes a local history store) and supersedes the FR-21 uniform-random ordering assumption (now history-aware, FR-24). Single-user/local is retained. Architecture impact (SQLite layer, schema, record-on-feedback hook, mock-exam session builder) is captured in `addendum.md` for the architecture phase.

## 7. Success Metrics

*Hobby/personal scope — kept lean.*

**Primary**
- **SM-1 (the real one):** Dario studies regularly through to exam day and **passes** the Databricks DE Associate exam. Validates the product's reason to exist.
- **SM-2:** The committed content bank exists and is studiable — **~50–75 MCQs across all five Associate Domains**, weighted roughly by the official split, consumable via Anki or the lean runner — **well before** exam day. Validates FR-1, FR-4, FR-18, and §6.1.

**Secondary**
- **SM-3:** Authoring a new Exercise and getting it into the study path takes only writing a file (+ a one-shot export) — **no app code changes**. Validates FR-1–FR-3, FR-18.
- **SM-4 (Phase 2):** The Code-Completion feedback feels instant and *teaches* syntax (Dario can recall a drilled snippet unaided afterward). Validates FR-13–FR-17.
- **SM-5 (stats):** History persists across sessions and the dashboard shows per-Domain accuracy + a readiness signal Dario actually uses to decide what to drill next; unseen-first means he isn't re-served questions he's already done while fresh ones remain. Validates FR-22–FR-25.
- **SM-6 (timed):** Dario can take a full domain-weighted Mock Exam under the real clock (Associate 45Q/90min, Pro 59Q/120min) and gets an exam-style score — the timed-exam feel Anki can't give. Validates FR-26–FR-28.

**Counter-metrics (do not optimize)**
- **SM-C1:** Don't optimize for **app features / polish** at the expense of **content volume and exam readiness**. Counterbalances SM-1; a beautiful app with 12 questions fails the actual job. This is the whole point of the Build-vs-Borrow decision (§6.0) — borrow the runner, invest the hours in content.
- **SM-C2:** Don't optimize the Wordle feature's cleverness at the expense of shipping the MCQ core. Counterbalances SM-4.

## 8. Open Questions

1. **OQ-1 (confirm before authoring):** Verify the **Associate exam domain list and their weights** against the live official Databricks PDF exam guide. The original MCQs will be authored to the current official documentation (Lakeflow Pipelines, not DLT; etc.), not reverse-engineered from real exam questions (which are proprietary). Domain list + weights are the only gate — they shape the content prioritization. Discovery research was model-knowledge-based (no live network); the addendum domains/weights are provisional. Other facts (question counts, passing score, price) are nice-to-know but not blocking content authoring.
2. **OQ-2:** Final Exercise schema details — file granularity (one Set per file vs. many), content directory location, and whether YAML-author/JSON-serve is worth the extra step for a single-user local app.
3. **OQ-3 (resolved):** Code-Completion feedback semantics = **token-level green/yellow/grey** (decided 2026-06-05). Remaining design-spike work is the tokenizer + rendering, not the color model.
4. **OQ-4 (resolved):** Starter content target = **~50–75 Associate MCQs weighted by domain split** (decided 2026-06-05, §6.1). Open sub-question: confirm this is enough for *your* confidence as exam day nears (top up if weak domains emerge).
5. **OQ-5 (resolved → committed):** The agent-skill authoring path **is** a committed parallel workstream (§6.1). Open sub-question: its exact spec (input prompts, output validation, dedup) — small follow-up, not a blocker.

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
- §4.3 — Code-Completion is single-line/fill-in-blank scope, whitespace-insensitive, with an explicit per-language case policy. *(Token-level green/yellow/grey is a confirmed decision, not an assumption.)*
- §4.3 / FR-16 — Alternative-answer matching is against an authored alternatives list; AST/execution equivalence is out of scope.
- §6.1 — The agent-skill authoring path is specced/built as its own small workstream; exact spec TBD.

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
