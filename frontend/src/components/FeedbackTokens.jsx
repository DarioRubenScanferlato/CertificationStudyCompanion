import CodeBlock from './CodeBlock'

/**
 * Presentational pieces for the Code-Completion ("Wordle") drill (Story 4.4).
 * All pure / off-props — no state, no API. Story 4.5 drives them with live data.
 *
 * Exports:
 *   - FeedbackTokens (default) — renders ONE attempt's tokens, colored
 *     green/yellow/grey, with a non-color cue per token (glyph + aria-label) and
 *     a role="status" summary. Color is NEVER the only signal (app-wide a11y floor).
 *   - AttemptsCounter — "Attempts left: N of M" (aria-live polite).
 *   - AnswerReveal — the canonical answer, shown only when concluded.
 */

// Per-color presentation. Each color is paired with a glyph + label so meaning
// survives without color (mirrors MCQ ✓/✗, ReadinessIndicator, Timer).
const COLOR_META = {
  green: { cls: 'bg-green-100 text-green-800 border border-green-300', glyph: '✓', label: 'correct' },
  yellow: {
    cls: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    glyph: '↔',
    label: 'wrong position',
  },
  grey: { cls: 'bg-gray-100 text-gray-600 border border-gray-300', glyph: '·', label: 'not in answer' },
}

function summarize(tokens) {
  const counts = { green: 0, yellow: 0, grey: 0 }
  for (const t of tokens) counts[t.color] = (counts[t.color] || 0) + 1
  return `${counts.green} correct, ${counts.yellow} misplaced, ${counts.grey} not in answer`
}

/**
 * Render one attempt's colored tokens.
 * @param {object} props
 * @param {Array<{token,color,position}>} props.tokens
 * @param {boolean} [props.showLegend] - show the color/glyph legend (e.g. on the latest row)
 */
export default function FeedbackTokens({ tokens, showLegend = false }) {
  if (!tokens || tokens.length === 0) return null

  return (
    <div className="my-1">
      <div className="flex flex-wrap gap-1 font-mono text-sm" role="group" aria-label="Attempt feedback">
        {tokens.map((t) => {
          const meta = COLOR_META[t.color] || COLOR_META.grey
          const label = `${t.token} — ${meta.label}`
          return (
            <span
              key={t.position}
              className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 ${meta.cls}`}
              title={label}
              aria-label={label}
            >
              <span aria-hidden="true" className="opacity-70">
                {meta.glyph}
              </span>
              {t.token}
            </span>
          )
        })}
      </div>

      <p role="status" className="sr-only">
        {summarize(tokens)}
      </p>

      {showLegend && (
        <ul className="mt-1 flex flex-wrap gap-3 text-xs text-gray-500" aria-label="Feedback legend">
          <li>
            <span aria-hidden="true">✓</span> correct spot
          </li>
          <li>
            <span aria-hidden="true">↔</span> present elsewhere
          </li>
          <li>
            <span aria-hidden="true">·</span> not in answer
          </li>
        </ul>
      )}
    </div>
  )
}

/**
 * "Attempts left" indicator. Presentational — the count is owned by Story 4.5.
 * @param {object} props
 * @param {number} props.attemptsLeft
 * @param {number} props.max
 */
export function AttemptsCounter({ attemptsLeft, max }) {
  return (
    <span
      className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700"
      aria-live="polite"
      data-testid="cc-attempts-counter"
    >
      Attempts left: {attemptsLeft}
      {typeof max === 'number' ? ` of ${max}` : ''}
    </span>
  )
}

/**
 * Canonical-answer reveal. Hidden until `revealed` is true (Story 4.5 decides when).
 * @param {object} props
 * @param {boolean} props.revealed
 * @param {string} props.answer
 * @param {string} [props.language]
 */
export function AnswerReveal({ revealed, answer, language }) {
  if (!revealed) return null
  return (
    <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4" data-testid="cc-answer-reveal">
      <h3 className="text-sm font-semibold text-gray-700 mb-1">Answer</h3>
      <CodeBlock code={answer} language={language} />
    </div>
  )
}
