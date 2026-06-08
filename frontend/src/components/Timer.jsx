import { useEffect, useRef, useState } from 'react'

/**
 * Reusable, accessible countdown timer.
 *
 * Counts down from `durationSeconds` once per second while `running` is true and
 * calls `onExpire` exactly once when the remaining time reaches zero. The
 * component owns no session/business logic — it only counts down and reports
 * expiry — so it can be reused by both the optional session timer (Story 8.1)
 * and Mock-Exam mode (Story 8.4).
 *
 * Props:
 * - durationSeconds: number — total countdown length, in seconds
 * - running: boolean — whether the clock advances (default true)
 * - onExpire: () => void — called once when remaining hits 0
 * - onTick?: (remainingSeconds: number) => void — optional per-second callback
 *
 * Drift resistance:
 * - Elapsed time is computed off a captured wall-clock start timestamp, so a
 *   backgrounded/throttled tab doesn't accumulate drift; the interval is only a
 *   nudge to recompute. Remaining is clamped at 0.
 *
 * Accessibility:
 * - An `aria-live="polite"` region announces the remaining time at coarse
 *   intervals (every ~30s, plus the final 10s and at expiry) so AT users are
 *   kept informed without per-second spam.
 * - The per-second visual ticker is `aria-hidden="true"`.
 * - The low-time state adds a glyph + text ("⏳ Time low"), never color alone.
 * - Any visual emphasis transition is suppressed under prefers-reduced-motion
 *   via Tailwind's `motion-reduce:*` variant (mirrors ProgressBar).
 */
function formatTime(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(s / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  const seconds = s % 60
  const pad = (n) => String(n).padStart(2, '0')
  if (hours > 0) {
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
  }
  return `${pad(minutes)}:${pad(seconds)}`
}

// Spoken form for the live region, e.g. "1 minute 30 seconds remaining".
function spokenTime(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(s / 60)
  const seconds = s % 60
  const parts = []
  if (minutes > 0) parts.push(`${minutes} minute${minutes === 1 ? '' : 's'}`)
  if (seconds > 0 || minutes === 0) parts.push(`${seconds} second${seconds === 1 ? '' : 's'}`)
  return `${parts.join(' ')} remaining`
}

// Announce on a coarse cadence: every 30s, each of the final 10s, and at zero.
function shouldAnnounce(remaining) {
  if (remaining <= 0) return true
  if (remaining <= 10) return true
  return remaining % 30 === 0
}

export default function Timer({ durationSeconds, running = true, onExpire, onTick }) {
  const [remaining, setRemaining] = useState(() => Math.max(0, Math.floor(durationSeconds)))
  // Guard so onExpire fires exactly once even across re-renders.
  const expiredRef = useRef(false)
  // Keep the latest callbacks without re-arming the interval each render.
  const onExpireRef = useRef(onExpire)
  onExpireRef.current = onExpire
  const onTickRef = useRef(onTick)
  onTickRef.current = onTick

  useEffect(() => {
    if (!running) return undefined
    if (expiredRef.current) return undefined

    // Capture a wall-clock anchor so throttled intervals don't accumulate drift.
    const startMs = Date.now()
    const startRemaining = Math.max(0, Math.floor(durationSeconds))

    const compute = () => {
      const elapsed = Math.floor((Date.now() - startMs) / 1000)
      const next = Math.max(0, startRemaining - elapsed)
      setRemaining(next)
      onTickRef.current?.(next)
      if (next <= 0 && !expiredRef.current) {
        expiredRef.current = true
        clearInterval(id)
        onExpireRef.current?.()
      }
    }

    const id = setInterval(compute, 1000)
    return () => clearInterval(id)
  }, [running, durationSeconds])

  const display = formatTime(remaining)
  const isLow = remaining > 0 && remaining <= 30
  const announce = shouldAnnounce(remaining)

  return (
    <div role="timer" aria-label="Time remaining" className="flex items-center gap-1 shrink-0">
      {/* Coarse-cadence live region — only carries text when we choose to
          announce, so the polite region isn't updated every second. */}
      <span aria-live="polite" className="sr-only">
        {announce ? (remaining <= 0 ? 'Time is up' : spokenTime(remaining)) : ''}
      </span>
      <span
        aria-hidden="true"
        className={`text-xs px-2 py-1 rounded font-mono tabular-nums transition-colors motion-reduce:transition-none ${
          isLow ? 'bg-red-100 text-red-800 font-semibold' : 'bg-gray-100 text-gray-700'
        }`}
      >
        {isLow && <span className="mr-1">⏳</span>}
        {display}
        {isLow && <span className="sr-only"> Time low</span>}
      </span>
    </div>
  )
}
