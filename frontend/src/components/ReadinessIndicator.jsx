/**
 * Readiness guidance (FR-25). Shows overall readiness vs the ~70% threshold
 * over a rolling window, and per-Domain readiness. This is explicitly framed as
 * guidance — NOT a guarantee of passing the real certification.
 *
 * Consumes the shape returned by api.getReadiness():
 *   { overall: { accuracy, ready, window }, byDomain: { [d]: { accuracy, ready } },
 *     threshold, window }
 */

function pct(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return '0%'
  return `${Math.round(n * 100)}%`
}

function ReadyBadge({ ready }) {
  return (
    <span
      className={
        ready
          ? 'inline-flex items-center rounded-full bg-green-100 text-green-800 px-2.5 py-0.5 text-xs font-semibold'
          : 'inline-flex items-center rounded-full bg-red-100 text-red-800 px-2.5 py-0.5 text-xs font-semibold'
      }
    >
      {ready ? 'On track' : 'Keep practicing'}
    </span>
  )
}

export default function ReadinessIndicator({ readiness }) {
  const overall = readiness?.overall ?? { accuracy: 0, ready: false }
  const byDomain = readiness?.byDomain ?? {}
  // Threshold is reported as a fraction (e.g. 0.7); fall back to 0.7.
  const threshold =
    typeof readiness?.threshold === 'number' ? readiness.threshold : 0.7
  const window =
    typeof overall.window === 'number'
      ? overall.window
      : typeof readiness?.window === 'number'
        ? readiness.window
        : null

  const domainEntries = Object.entries(byDomain)

  return (
    <section
      aria-labelledby="readiness-heading"
      className="bg-white border border-gray-200 rounded-lg p-6"
    >
      <div className="flex items-center justify-between gap-4">
        <h3 id="readiness-heading" className="text-lg font-semibold text-gray-900">
          Readiness
        </h3>
        <ReadyBadge ready={Boolean(overall.ready)} />
      </div>

      <p className="mt-1 text-sm text-gray-600">
        Based on your last {window ?? 'few'} answers vs a {pct(threshold)} target
        {window ? '' : ' '}
        {' '}
        — this is study guidance, not a guarantee of passing the exam.
      </p>

      <div className="mt-4" data-testid="readiness-overall">
        <div className="flex items-baseline justify-between">
          <span className="text-sm font-medium text-gray-700">Overall accuracy</span>
          <span
            className={`text-2xl font-bold ${
              overall.ready ? 'text-green-700' : 'text-red-700'
            }`}
          >
            {pct(overall.accuracy)}
          </span>
        </div>
        {/* Track with a threshold marker so the user sees how far off the bar they are. */}
        <div className="relative mt-2 h-3 w-full rounded bg-gray-200">
          <div
            className={`h-3 rounded ${overall.ready ? 'bg-green-500' : 'bg-red-500'}`}
            style={{ width: pct(overall.accuracy) }}
          />
          <div
            className="absolute top-0 h-3 w-0.5 bg-gray-700"
            style={{ left: pct(threshold) }}
            aria-hidden="true"
            data-testid="readiness-threshold-marker"
          />
        </div>
        <p className="mt-1 text-xs text-gray-500">{pct(threshold)} target</p>
      </div>

      {domainEntries.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">By domain</h4>
          <ul className="divide-y divide-gray-100" data-testid="readiness-by-domain">
            {domainEntries.map(([domain, d]) => (
              <li
                key={domain}
                className="flex items-center justify-between gap-3 py-2"
                data-testid={`readiness-domain-${domain}`}
              >
                <span className="text-sm text-gray-800">{domain}</span>
                <span className="flex items-center gap-3">
                  <span
                    className={`text-sm font-semibold ${
                      d.ready ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    {pct(d.accuracy)}
                  </span>
                  <ReadyBadge ready={Boolean(d.ready)} />
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
