/**
 * Session progress bar.
 *
 * Shows the student's position across the session and a running count of
 * correct answers, e.g. "7/20 · 6 correct". The visual fill is proportional to
 * `current / total`.
 *
 * Props:
 * - current: number — 1-based position of the active question
 * - total: number — total questions in the session
 * - correct: number — running count of correct answers so far
 *
 * Accessibility:
 * - role="progressbar" with aria-valuenow / aria-valuemin / aria-valuemax and an
 *   aria-valuetext that conveys the running score (so the count isn't lost to
 *   AT users who only get the numeric progress).
 * - The visible text label ("Question {current} of {total}" + the running score)
 *   is also rendered so the information never depends on the bar's color/motion.
 * - The fill transition is gated behind prefers-reduced-motion via Tailwind's
 *   `motion-reduce:transition-none` variant.
 */
export default function ProgressBar({ current, total, correct }) {
  const safeTotal = Math.max(total, 1)
  const safeCurrent = Math.min(Math.max(current, 0), safeTotal)
  const pct = Math.round((safeCurrent / safeTotal) * 100)
  const scoreText = `${safeCurrent}/${safeTotal} · ${correct} correct`
  const valueText = `Question ${safeCurrent} of ${safeTotal}, ${correct} correct`

  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-500">
          Question {safeCurrent} of {safeTotal}
        </span>
        <span className="text-sm font-medium text-gray-700">{scoreText}</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={safeCurrent}
        aria-valuemin={1}
        aria-valuemax={safeTotal}
        aria-valuetext={valueText}
        aria-label="Session progress"
        className="h-2 w-full overflow-hidden rounded-full bg-gray-200"
      >
        <div
          className="h-full rounded-full bg-databricks-500 transition-[width] duration-300 ease-out motion-reduce:transition-none"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
