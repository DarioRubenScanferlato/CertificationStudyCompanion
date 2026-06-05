---
review_date: 2026-06-05
scope: Epic 3 — MCQ Study Practice Interface (Stories 3.1–3.7)
commit: 3f84b02 "frontend mcq display"
reviewer: bmad-code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor)
files_reviewed: 18 frontend files (~1200 diff lines)
---

# Epic 3 — Code Review Findings

## Summary

- **0** decision-needed
- **9** patch → **all 9 applied** (2026-06-05)
- **6** defer
- **8** dismissed as noise

All three review layers completed (none failed). No Critical findings; the two HIGH
items are defensive crash-guards (malformed/empty data white-screens the app).

**Resolution:** All 9 patches applied. 32 frontend tests pass (added 2 for the new
graceful-degradation guards), ESLint clean, production build succeeds.

Note: two Epic 2 backend fixes pre-empt would-be findings here — `single_choice` is
validated to have exactly one correct option, and `domain` must be a valid enum — so
"unanswerable single-choice" and "undefined domain bucket" cannot occur from real data.

## Patch (all applied)

- [x] [Review][Patch] HIGH — `MCQPractice` `exercise.options.map` guarded; malformed/optionless exercise now shows a "malformed" message + Skip instead of white-screening [pages/MCQPractice.jsx] (blind+edge)
- [x] [Review][Patch] HIGH — `CodeBlock` now passes `code ?? ''` to `Prism.highlight`, preventing the undefined-code crash [components/CodeBlock.jsx] (edge)
- [x] [Review][Patch] MED — `fetchExercises` returns `Array.isArray(data) ? data : []` and throws with `null` status (not `200`) on failure [api.js] (edge+blind)
- [x] [Review][Patch] MED — `gradeAnswer` returns `false` for an empty correct set; test updated to assert answer-less questions are never correct [utils/grading.js, utils/grading.test.js] (blind+edge)
- [x] [Review][Patch] MED — Summary now shows `correct/total` (session size) per AC 3.6 [pages/Summary.jsx] (auditor+blind)
- [x] [Review][Patch] LOW — `parseQuestion` handles CRLF (`\r?\n`) and coerces `String(input ?? '')` [components/QuestionContent.jsx] (blind+edge)
- [x] [Review][Patch] LOW — Reducer `SUBMIT_ANSWER` is now idempotent and ignores empty selections [context/SessionContext.jsx] (edge+blind)
- [x] [Review][Patch] LOW — Decorative `✓`/`✗` marked `aria-hidden`; reference `<li>` key uses `${ref}-${i}` [pages/MCQPractice.jsx] (blind+edge)
- [x] [Review][Patch] LOW — `code_completion` exercises render a graceful "arrives later" skip card instead of a broken MCQ [pages/MCQPractice.jsx] (blind+edge)

### Deferred

- [x] [Review][Defer] CodeCompletion practice UI not implemented — Epic 4 scope (crash prevented by options guard) [MCQPractice.jsx] (blind+edge)
- [x] [Review][Defer] `dangerouslySetInnerHTML` in CodeBlock — acceptable: Prism escapes token text and content is trusted local YAML; revisit if content becomes untrusted [components/CodeBlock.jsx] (blind+edge)
- [x] [Review][Defer] `role="status"` feedback region is mounted with its content; may not announce reliably (a11y polish — use a persistent live region) [pages/MCQPractice.jsx] (blind)
- [x] [Review][Defer] Context action callbacks recreated each state change; `useCallback` would stabilize identity (minor perf) [context/SessionContext.jsx] (blind)
- [x] [Review][Defer] Prism CSS/grammar imports are module-level side effects with no SSR/test-env guard — safe under current jsdom/Vite setup [components/CodeBlock.jsx] (edge)
- [x] [Review][Defer] `SessionSelect` has no in-flight/AbortController guard against rapid double-click or unmount-mid-fetch (button disables on next paint) [pages/SessionSelect.jsx] (edge)

### Dismissed (noise / false positives / pre-empted by backend)

- single_choice with multiple correct → unanswerable — backend now validates exactly one correct option
- `byDomain` undefined-domain bucket / non-string question crash — backend validates domain enum + string fields
- Empty code fence renders an empty `<pre>` — cosmetic
- Prose `.trim()` on text segments — intended boundary trimming; intra-text newlines preserved by `whitespace-pre-wrap`
- `App.test.jsx` doesn't mock api — only asserts initial render; no network call occurs
- String-fragment test selectors — acceptable
- SessionSelect allows "All domains"/"Any difficulty" — deliberate UX; AC lists capabilities not constraints
- Multi-select with single checkbox enabled — spec-consistent (graded incorrect by all-or-nothing)
