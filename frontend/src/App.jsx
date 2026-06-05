import { SessionProvider, useSession } from './context/SessionContext'
import SessionSelect from './pages/SessionSelect'
import MCQPractice from './pages/MCQPractice'
import Summary from './pages/Summary'

function CurrentView() {
  const { view } = useSession()
  switch (view) {
    case 'practice':
      return <MCQPractice />
    case 'summary':
      return <Summary />
    case 'select':
    default:
      return <SessionSelect />
  }
}

export default function App() {
  return (
    <SessionProvider>
      <div className="min-h-screen bg-white">
        <header className="bg-gray-100 border-b border-gray-300">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <h1 className="text-3xl font-bold text-gray-900">
              Databricks DE Certification Study Companion
            </h1>
            <p className="text-gray-600 mt-1">
              Practice for your Databricks Data Engineer certification
            </p>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          <CurrentView />
        </main>
      </div>
    </SessionProvider>
  )
}
