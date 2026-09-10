import { useEffect, useState } from 'react'
import { getAnalytics, getWeakTopics } from '../services/analytics.service'
import type { AnalyticsResponse, WeakTopicResponse } from '../types/api'
import AppLayout from '../components/AppLayout'
import { Activity, AlertCircle } from 'lucide-react'

export default function AnalyticsPage(): React.JSX.Element {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [weakTopics, setWeakTopics] = useState<WeakTopicResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('all')

  // We refetch only analytics when timeRange changes. 
  // Weak topics does not accept timeRange in the backend schema.
  useEffect(() => {
    setIsLoading(true)
    Promise.all([
      getAnalytics(timeRange),
      getWeakTopics()
    ])
      .then(([a, w]) => {
        setAnalytics(a)
        setWeakTopics(w)
      })
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [timeRange])

  return (
    <AppLayout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold text-white flex items-center gap-3">
            <Activity className="text-blue-500" /> Analytics
          </h1>
          
          <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded px-3 py-1.5">
            <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Time Range:</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              disabled={isLoading}
              className="bg-transparent text-white text-sm focus:outline-none cursor-pointer"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>

        {isLoading && !analytics ? (
          <div className="text-gray-500 text-sm">Loading analytics...</div>
        ) : !analytics ? (
          <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded text-sm">
            Unable to load analytics data.
          </div>
        ) : (
          <div className={isLoading ? 'opacity-50 transition-opacity' : 'transition-opacity'}>
            <div className="grid grid-cols-2 gap-4 mb-10 lg:grid-cols-3">
              <Stat label="Total Sessions" value={analytics.total_sessions} />
              <Stat label="Completed" value={analytics.completed_sessions} />
              <Stat label="Questions Asked" value={analytics.total_questions} />
              <Stat label="Questions Answered" value={analytics.answered_questions} />
              <Stat
                label="Avg Session Score"
                value={analytics.average_score != null ? `${analytics.average_score.toFixed(1)} / 10` : '—'}
              />
              <Stat
                label="Avg Answer Rating"
                value={analytics.average_rating != null ? `${analytics.average_rating.toFixed(1)} / 5` : '—'}
              />
            </div>

            <div className="flex items-center gap-2 mb-4">
              <h2 className="text-lg font-semibold text-white">Weak Topics</h2>
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">Detected via AI</span>
            </div>
            
            {weakTopics.length === 0 ? (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-gray-500 text-sm flex flex-col items-center justify-center gap-3">
                <AlertCircle size={24} className="text-gray-700" />
                No weak topics detected yet. Complete more interviews to gather data.
              </div>
            ) : (
              <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
                {weakTopics.map((t) => (
                  <div
                    key={t.id}
                    className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between hover:border-gray-700 transition"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{t.topic}</span>
                        {t.category && (
                          <span className="text-xs bg-blue-900/30 text-blue-400 border border-blue-900 px-2 py-0.5 rounded">
                            {t.category}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Last seen: {new Date(t.last_encountered).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-300">
                        Freq: <strong className="text-white">{t.frequency}</strong>
                      </div>
                      {t.avg_score != null && (
                        <div className="text-xs text-amber-400 mt-0.5 font-medium">
                          Avg: {t.avg_score.toFixed(1)} / 10
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:bg-gray-800/50 transition">
      <p className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-2">{label}</p>
      <p className="text-white text-2xl font-bold">{value}</p>
    </div>
  )
}
