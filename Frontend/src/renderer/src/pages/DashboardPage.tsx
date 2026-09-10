import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../store/sessionStore'
import { listSessions } from '../services/session.service'
import { apiGet } from '../services/api'
import type { AnalyticsResponse } from '../types/api'
import AppLayout from '../components/AppLayout'

export default function DashboardPage(): React.JSX.Element {
  const navigate = useNavigate()
  const { sessions, totalSessions, setSessions } = useSessionStore()
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      listSessions(1, 5).then((res) => setSessions(res.sessions, res.total)),
      apiGet<AnalyticsResponse>('/api/analytics').then(setAnalytics)
    ])
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AppLayout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-white">
              Welcome back
            </h1>
            <p className="text-gray-400 text-sm mt-1">Your interview preparation dashboard</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/context')}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 text-sm font-medium px-4 py-2 rounded transition-colors"
            >
              Manage Context
            </button>
            <button
              onClick={() => navigate('/interview/new')}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
            >
              Start Interview
            </button>
          </div>
        </div>

        {/* Stats */}
        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : analytics ? (
          <div className="grid grid-cols-2 gap-4 mb-8 lg:grid-cols-4">
            <StatCard label="Sessions" value={analytics.total_sessions} />
            <StatCard label="Questions" value={analytics.total_questions} />
            <StatCard label="Avg Score" value={analytics.average_score != null ? analytics.average_score.toFixed(1) : '—'} />
            <StatCard label="Avg Rating" value={analytics.average_rating != null ? analytics.average_rating.toFixed(1) : '—'} />
          </div>
        ) : null}

        {/* Recent Sessions */}
        <h2 className="text-lg font-medium text-white mb-4">Recent Sessions</h2>
        {sessions.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded p-6 text-gray-500 text-sm text-center">
            No sessions yet. Start your first interview to see results here.
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/history`)}
                className="w-full bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded px-4 py-3 text-left transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm font-medium">{s.mode}</span>
                  <span className="text-gray-500 text-xs">
                    {new Date(s.created_at).toLocaleDateString()}
                  </span>
                </div>
                {s.target_role && (
                  <p className="text-gray-400 text-xs mt-1">{s.target_role}</p>
                )}
              </button>
            ))}
            {totalSessions > 5 && (
              <button
                onClick={() => navigate('/history')}
                className="text-blue-400 hover:text-blue-300 text-sm"
              >
                View all {totalSessions} sessions →
              </button>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <p className="text-gray-400 text-xs mb-1">{label}</p>
      <p className="text-white text-2xl font-semibold">{value}</p>
    </div>
  )
}
