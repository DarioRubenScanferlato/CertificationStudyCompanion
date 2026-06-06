---
title: DataBricks DE Cert Study Companion — Experience Spec
status: final
created: 2026-06-05
updated: 2026-06-05
design: ./DESIGN.md
sources:
  - ../../prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md
  - ../../architecture.md
  - ../../epics.md
---

# DataBricks DE Cert Study Companion — Experience Spec

> **Scope of this pass:** quality-of-life behavior on top of the working MVP (`SessionSelect → MCQPractice → Summary`). Visual identity is inherited from [DESIGN.md](./DESIGN.md); this doc owns *how it works*. Behaviors here assume the PRD rev 2 model: **single-select** MCQs drawn from server-sampled Displayed Options, randomized session order.

## Foundation

- **Form-factor:** local web app, **desktop browser primary** (laptop study). Layout already uses centered content columns; no mobile redesign this pass, but nothing here precludes it.
- **UI system:** React + Tailwind (existing). State lives in `SessionContext` (`useReducer`). No router today — navigation is a `view` flag; this spec adds states/actions to that reducer rather than introducing routing.
- **No persistence (MVP):** sessions are ephemeral (memory only). Ending or reloading discards a session by definition — hence the confirm patterns below.

## Information Architecture

Three surfaces, plus modal and review states layered on them:

```
Start (SessionSelect)
  └─ filters: domain, difficulty  +  live match count
  └─ [Start Session] → Practice
Practice (MCQPractice)            ← always offers End-session
  └─ one question at a time, single-select
  └─ progress bar + running score
  └─ Back / Skip / Submit / Next
  └─ End session → (confirm) → Start | Partial Summary
Summary
  └─ score + per-domain breakdown
  └─ Review incorrect (inline) → Practice-those-again → Practice
  └─ Restart same session → Practice
  └─ Start new session → Start
```

**IA closure:** every stated need has a surface — exit (End-session control, on Practice), orientation (progress bar, on Practice), recovery (confirm + partial summary), and review (Summary's review-incorrect). The header title is a persistent Home affordance from any surface.

## Voice and Tone

Plain, encouraging, exam-calm. No gamified hype, no shaming on wrong answers.

- End-session confirm: **"End this session? You've answered {n} of {total}."** Actions: *"See results"* · *"Discard & exit"* · *"Keep practicing"*.
- Skip control label: **"Skip"**; skipped state in summary: **"Skipped"** (neutral, not "failed").
- Match count: **"{n} questions match"** / **"No questions match these filters"**.
- Restart: **"Restart this session"**; Practice-again: **"Practice these {n} again"**.
- Wrong-answer feedback stays factual: **"Incorrect"** + explanation; never "Wrong!" or streak-breaking language.

## Component Patterns (behavioral)

Visual specs inherit from DESIGN.md › Components. Behavior:

- **End-session control** — persistent on the Practice surface (e.g. top-right of the question header row, secondary/neutral styling so it never competes with Submit `{colors.brand.databricks-500}`). Triggers the **Exit confirm** unless the session has zero answered questions (then exits straight to Start).
- **Home affordance (header title)** — clickable on every surface; on Practice it behaves identically to End-session (routes through Exit confirm); on Summary/Start it goes to Start directly.
- **Exit confirm (modal)** — blocking dialog with three actions (see Voice). Dismissible via Esc = *Keep practicing*. Focus trapped; focus returns to the trigger on dismiss.
- **Progress bar** — replaces the text-only "Question X of Y". Shows position across the session and a **running correct count** (e.g. "12/20 · 9 correct"). Updates on submit and on navigation.
- **Back / Previous** — revisits already-visited questions. An **answered** question shown via Back is **read-only**: its selection, correctness, and explanation are displayed; options are disabled. Forward returns to the furthest-reached question. Back is hidden/disabled on the first question.
- **Skip** — advances without grading; the question is recorded as **unanswered** (not incorrect) and remains reachable via Back. Available only before submit.
- **Review-incorrect list (Summary)** — expandable list of the questions answered incorrectly, each showing the question, the correct option, and the explanation. A **"Practice these {n} again"** action starts a fresh session containing only those exercises.

## State Patterns

Per-question states (Practice):
- **Unanswered–unselected** → Submit disabled; Skip available; Back available (if not first).
- **Unanswered–selected** → Submit enabled.
- **Submitted** → options locked; correctness + explanation shown; primary action becomes **Next** (or **See results** on last).
- **Revisited (read-only)** → as Submitted but reached via Back; no re-answer; **Skipped** items revisited show as still-answerable only if the session hasn't ended.

Session states:
- **Active** → Practice view.
- **Ended-early** → user chose *See results* → Summary computed over **answered subset** (skipped/unanswered excluded from the denominator shown, but surfaced as a count).
- **Completed** → advanced past the last question → full Summary.

Start-screen states:
- **Filtering** → match count updates live as domain/difficulty change.
- **Empty match** → Start disabled; "No questions match these filters" guidance (existing behavior, surfaced *before* clicking).
- **Loading / error** → existing patterns retained (spinner on Start; backend-down error message).

Empty/edge:
- **All questions skipped, then End** → Summary shows 0 answered with an encouraging "Nothing graded yet — jump back in?" and a Start action.
- **Single-question session** → progress bar + Summary still coherent.

## Interaction Primitives

- **Keyboard (Practice):**
  - `1`–`4` (and `a`–`d`) select the corresponding option.
  - `Enter` = **Submit** when an option is selected and not yet submitted; after submit, `Enter` = **Next / See results**.
  - `←` / `→` = Back / Next (Next only enabled after submit or via Skip semantics — `→` on an unanswered question acts as Skip with the same unanswered recording).
  - `Esc` = open End-session confirm (and dismiss it = Keep practicing).
  - All shortcuts are discoverable via a small "keyboard hints" affordance; none are the *only* way to do anything (pointer parity).
- **Selection feedback:** selecting an option highlights with accent border `{colors.brand.databricks-500}` pre-submit; post-submit uses `{colors.feedback}` semantics.
- **Confirm dialogs** are the only blocking interaction; everything else is inline.

## Accessibility Floor

- **Keyboard:** full operability — every action (select, submit, next, back, skip, end, review) reachable and operable by keyboard; visible focus ring on all interactive elements.
- **Single-select semantics:** options are a radio group (`role="radiogroup"`, arrow-key roving per native radios); the existing checkbox path is removed with multi-select.
- **Live regions:** correctness result and progress changes announced via `aria-live="polite"` (the result banner already uses `role="status"`); the progress bar exposes `aria-valuenow/max` or equivalent text.
- **Modal:** Exit confirm traps focus, is labeled (`aria-modal`, labelled title), Esc-dismissible, restores focus on close.
- **Color independence:** correctness never conveyed by color alone — keep the ✓/✗ glyph + text label alongside `{colors.feedback}`.
- **Targets & motion:** comfortable click targets; progress-bar transitions respect `prefers-reduced-motion`.

## Key Flows

**Flow 1 — Dario bails out of a long set without losing face (the stated gap).**
Dario starts an "all domains / any difficulty" session, expecting ~20 questions but it loads 60. Ten in, he's out of time. He hits **End session** (top-right, always there). The **Exit confirm** appears: *"End this session? You've answered 10 of 60."* He picks **See results** → lands on a **partial Summary**: 10 answered, 7 correct, per-domain breakdown, plus the **Review incorrect** list for the 3 he missed. He clicks **Practice these 3 again** tomorrow. *Climax beat:* the moment he realizes quitting doesn't throw away the 10 he did — it banks them into a usable result. (Closes decisions #3, #5.)

**Flow 2 — Fast keyboard drilling.**
Mary, prepping over lunch, never touches the mouse: reads the question, presses `2`, presses `Enter` (submit), reads the explanation, presses `Enter` (next). The **progress bar** ticks "7/20 · 6 correct". She mis-clicks momentum and presses `←` to **Back** and re-read question 6 (read-only, shows she got it right), then `→` to return. *Climax beat:* a full 20-question set cleared in one unbroken keyboard rhythm. (Closes decision #4.)

**Flow 3 — Right-sizing before starting.**
On the Start screen Dario sets Domain = "Incremental Data Processing"; the **match count** updates to "16 questions match". He sets Difficulty = hard → "5 questions match" — enough for a focused 5-minute drill, so he starts knowing exactly what he's getting. *Climax beat:* no more starting blind and discovering the set's size mid-session. (Closes decision #5.)

## Open Items / Notes

- ✅ **Resolved** — "Restart same session" and "Practice these N again" replay a specific exercise set with **freshly sampled/shuffled options and re-randomized order**, via `POST /api/sessions {exerciseIds}` (architecture rev 3, gap G2). Replays keep FR-20/21 freshness.
- `[ASSUMPTION accepted]` Skip leaves a question answerable on revisit *within the active session*; once the session ends it's frozen as unanswered. (Reasonable default for a drilling tool; revisit if it feels surprising in use.)
- `[ASSUMPTION accepted]` Session length stays "full filtered set" this pass (choose-length deferred per decision #5); the live match count gives the size signal instead.
- **Mock coverage:** per the user's direction (functional/QoL pass, not a visual redesign), all surfaces are **spine-only** — no key-screen HTML mocks rendered. Build from EXPERIENCE.md + the inherited DESIGN.md tokens; add visual references in a later UX pass if desired.
