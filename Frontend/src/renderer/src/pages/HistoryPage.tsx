import { useEffect, useState } from 'react'
import { listSessions } from '../services/session.service'
import { useSessionStore } from '../store/sessionStore'
import AppLayout from '../components/AppLayout'

export default function HistoryPage(): React.JSX.Element {
  const { sessions, totalSessions, setSessions, isLoading, setLoading } = useSessionStore()
  const [page, setPage] = useState(1)

  useEffect(() => {
    setLoading(true)
    listSessions(page, 10)
      .then((res) => setSessions(res.sessions, res.total))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [page]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold text-white mb-6">Session History</h1>

        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : sessions.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded p-6 text-gray-500 text-sm text-center">
            No sessions recorded yet.
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-6">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className="bg-gray-900 border border-gray-800 rounded px-4 py-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white text-sm font-medium">{s.mode}</span>
                    <span className="text-gray-500 text-xs">
                      {new Date(s.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-1 text-xs text-gray-400">
                    {s.target_role && <span>{s.target_role}</span>}
                    <span>Questions: {s.question_count}</span>
                    {s.score != null && <span>Score: {s.score.toFixed(0)}</span>}
                    <span className="capitalize">{s.status}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-4 text-sm">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="text-gray-400 hover:text-white disabled:opacity-30"
              >
                ← Previous
              </button>
              <span className="text-gray-500">
                Page {page} · {totalSessions} total
              </span>
              <button
                disabled={page * 10 >= totalSessions}
                onClick={() => setPage((p) => p + 1)}
                className="text-gray-400 hover:text-white disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  )
}
