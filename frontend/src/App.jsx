import { createContext, useContext, useEffect, useRef } from 'react'
import { SessionProvider, useSession } from './context/SessionContext'
import SessionSelect from './pages/SessionSelect'
import MCQPractice from './pages/MCQPractice'
import CodeCompletion from './pages/CodeCompletion'
import Summary from './pages/Summary'
import StatsDashboard from './pages/StatsDashboard'
import { EXERCISE_TYPES } from './constants'

/**
 * Lets the Practice surface register its Exit-confirm trigger so the header
 * Home affordance can route through the very same confirm flow (no duplicate
 * modal). MCQPractice owns the modal + answered-count logic; it registers a
 * `requestExit` callback here while mounted. The context is optional — when
 * MCQPractice is rendered outside this provider (e.g. unit tests) registration
 * is a harmless no-op.
 */
const ExitConfirmContext = createContext(null)

export function useRegisterExitConfirm(requestExit) {
  const ctx = useContext(ExitConfirmContext)
  useEffect(() => {
    if (!ctx) return undefined
    ctx.register(requestExit)
    return () => ctx.register(null)
  }, [ctx, requestExit])
}

// The `practice` view hosts both runners — dispatch by the current exercise's
// type so a single session can mix MCQ and Code-Completion exercises (Epic 4).
function PracticeRouter() {
  const { currentExercise } = useSession()
  if (currentExercise?.type === EXERCISE_TYPES.CODE_COMPLETION) {
    return <CodeCompletion />
  }
  return <MCQPractice />
}

function CurrentView() {
  const { view } = useSession()
  switch (view) {
    case 'practice':
      return <PracticeRouter />
    case 'summary':
      return <Summary />
    case 'stats':
      return <StatsDashboard />
    case 'select':
    default:
      return <SessionSelect />
  }
}

function AppShell() {
  const { view, reset, goStats } = useSession()
  // Holds the Practice surface's current requestExit handler, if mounted.
  const exitHandlerRef = useRef(null)

  const exitContext = {
    register: (fn) => {
      exitHandlerRef.current = fn
    },
  }

  // Header title = Home affordance. On Practice it behaves like End session
  // (routes through the Exit-confirm / zero-answered shortcut owned by
  // MCQPractice). On Select/Summary it goes to Start directly.
  function goHome() {
    if (view === 'practice' && exitHandlerRef.current) {
      exitHandlerRef.current()
    } else {
      reset()
    }
  }

  // Stats is a read-only view reachable from anywhere except an active session
  // (where leaving would abandon in-progress answers). On Practice we hide the
  // affordance so the existing Exit-confirm flow stays the single way out.
  const showStatsLink = view !== 'practice' && view !== 'stats'

  return (
    <ExitConfirmContext.Provider value={exitContext}>
      <div className="min-h-screen bg-white">
        <header className="bg-gray-100 border-b border-gray-300">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                <button
                  type="button"
                  onClick={goHome}
                  className="text-left rounded hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-databricks-500"
                  aria-label="Databricks DE Certification Study Companion — go home"
                >
                  Databricks DE Certification Study Companion
                </button>
              </h1>
              <p className="text-gray-600 mt-1">
                Practice for your Databricks Data Engineer certification
              </p>
            </div>
            {showStatsLink && (
              <nav>
                <button
                  type="button"
                  onClick={goStats}
                  className="text-databricks-600 hover:text-databricks-900 font-medium rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-databricks-500"
                >
                  Stats
                </button>
              </nav>
            )}
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          <CurrentView />
        </main>
      </div>
    </ExitConfirmContext.Provider>
  )
}

export default function App() {
  return (
    <SessionProvider>
      <AppShell />
    </SessionProvider>
  )
}
