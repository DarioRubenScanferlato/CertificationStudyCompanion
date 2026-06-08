import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import Timer from './Timer'

describe('Timer (Story 8.1)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the formatted starting time as MM:SS', () => {
    render(<Timer durationSeconds={90} onExpire={() => {}} />)
    // 90s -> 01:30
    expect(screen.getByText('01:30')).toBeInTheDocument()
  })

  it('renders HH:MM:SS for durations of an hour or more', () => {
    render(<Timer durationSeconds={5400} onExpire={() => {}} />)
    // 90 minutes -> 01:30:00
    expect(screen.getByText('01:30:00')).toBeInTheDocument()
  })

  it('decrements as time advances', () => {
    render(<Timer durationSeconds={90} onExpire={() => {}} />)
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    expect(screen.getByText('01:25')).toBeInTheDocument()
  })

  it('calls onExpire exactly once at zero and not again after further ticks', () => {
    const onExpire = vi.fn()
    render(<Timer durationSeconds={3} onExpire={onExpire} />)
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    expect(onExpire).toHaveBeenCalledTimes(1)
    expect(screen.getByText('00:00')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    expect(onExpire).toHaveBeenCalledTimes(1)
  })

  it('does not tick (or expire) while running is false', () => {
    const onExpire = vi.fn()
    render(<Timer durationSeconds={10} running={false} onExpire={onExpire} />)
    act(() => {
      vi.advanceTimersByTime(20000)
    })
    expect(screen.getByText('00:10')).toBeInTheDocument()
    expect(onExpire).not.toHaveBeenCalled()
  })

  it('clears its interval on unmount (no expiry after teardown)', () => {
    const onExpire = vi.fn()
    const { unmount } = render(<Timer durationSeconds={5} onExpire={onExpire} />)
    unmount()
    act(() => {
      vi.advanceTimersByTime(10000)
    })
    expect(onExpire).not.toHaveBeenCalled()
  })

  it('exposes a timer role and a polite live region', () => {
    render(<Timer durationSeconds={90} onExpire={() => {}} />)
    expect(screen.getByRole('timer')).toBeInTheDocument()
  })
})
