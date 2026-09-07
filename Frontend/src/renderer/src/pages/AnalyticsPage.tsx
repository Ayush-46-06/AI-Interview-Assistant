import { useEffect, useState } from 'react'
import { apiGet } from '../services/api'
import type { AnalyticsResponse, WeakTopicResponse } from '../types/api'
import AppLayout from '../components/AppLayout'

export default function AnalyticsPage(): React.JSX.Element {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [weakTopics, setWeakTopics] = useState<WeakTopicResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiGet<AnalyticsResponse>('/api/analytics'),
      apiGet<WeakTopicResponse[]>('/api/weak-topics')
    ])
      .then(([a, w]) => {
        setAnalytics(a)
        setWeakTopics(w)
      })
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-2xl font-semibold text-white mb-6">Analytics</h1>

        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : !analytics ? (
          <div className="text-gray-500 text-sm">Unable to load analytics.</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 mb-8 lg:grid-cols-3">
              <Stat label="Total Sessions" value={analytics.total_sessions} />
              <Stat label="Completed" value={analytics.completed_sessions} />
              <Stat label="Questions Asked" value={analytics.total_questions} />
              <Stat label="Questions Answered" value={analytics.answered_questions} />
              <Stat
                label="Avg Session Score"
                value={analytics.average_score != null ? `${analytics.average_score.toFixed(1)}` : '—'}
              />
              <Stat
                label="Avg Answer Rating"
                value={analytics.average_rating != null ? `${analytics.average_rating.toFixed(1)} / 5` : '—'}
              />
            </div>

            <h2 className="text-lg font-medium text-white mb-4">Weak Topics</h2>
            {weakTopics.length === 0 ? (
              <div className="bg-gray-900 border border-gray-800 rounded p-4 text-gray-500 text-sm text-center">
                No weak topics detected yet.
              </div>
            ) : (
              <div className="space-y-2">
                {weakTopics.map((t) => (
                  <div
                    key={t.id}
                    className="bg-gray-900 border border-gray-800 rounded px-4 py-3 flex items-center justify-between"
                  >
                    <div>
                      <span className="text-white text-sm">{t.topic}</span>
                      {t.category && (
                        <span className="ml-2 text-gray-500 text-xs">{t.category}</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 text-right">
                      <div>Frequency: {t.frequency}</div>
                      {t.avg_score != null && <div>Avg score: {t.avg_score.toFixed(1)}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <p className="text-gray-400 text-xs mb-1">{label}</p>
      <p className="text-white text-xl font-semibold">{value}</p>
    </div>
  )
}
