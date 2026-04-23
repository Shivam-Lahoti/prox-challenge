import { useState, useEffect } from 'react'
import Chat from './components/Chat'
import { checkHealth } from './utils/api'

function App() {
  const [isHealthy, setIsHealthy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const healthCheck = async () => {
      try {
        const health = await checkHealth()
        setIsHealthy(health.agent_ready && health.vector_store_ready)
      } catch (error) {
        console.error('Health check failed:', error)
        setIsHealthy(false)
      } finally {
        setLoading(false)
      }
    }
    healthCheck()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Connecting to agent...</p>
        </div>
      </div>
    )
  }

  if (!isHealthy) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <div className="text-red-600 text-xl mb-4">⚠️ Agent Offline</div>
          <p className="text-slate-700 mb-4">
            Cannot connect to the Vulcan OmniPro 220 agent.
          </p>
          <p className="text-sm text-slate-500">
            Make sure the backend is running on port 8000.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">⚡</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">
                Vulcan OmniPro 220
              </h1>
              <p className="text-sm text-slate-500">
                Multiprocess Welding System Expert
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Chat />
      </main>

      <footer className="border-t border-slate-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-slate-500">
          Built for Prox Founding Engineer Challenge
        </div>
      </footer>
    </div>
  )
}

export default App