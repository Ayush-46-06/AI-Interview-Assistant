import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import { createSession } from '../services/session.service'
import { useProfileStore } from '../store/profileStore'

const INTERVIEW_MODES = [
  'Technical Q&A',
  'Coding',
  'HR/Behavioral',
  'Mock Interview',
  'Rapid-Fire',
  'Revision'
]

export default function NewSessionPage(): React.JSX.Element {
  const navigate = useNavigate()
  const { profile, fetchProfile } = useProfileStore()
  const [mode, setMode] = useState(INTERVIEW_MODES[0])
  const [targetRole, setTargetRole] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProfile()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (profile?.target_role && !targetRole) {
      setTargetRole(profile.target_role)
    }
  }, [profile])

  async function handleStartSession(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const session = await createSession({
        mode,
        target_role: targetRole.trim() || null
      })
      navigate(`/interview/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
      setIsSubmitting(false)
    }
  }

  return (
    <AppLayout>
      <div className="p-8 max-w-xl mx-auto mt-12">
        <h1 className="text-2xl font-semibold text-white mb-2">New Interview Session</h1>
        <p className="text-gray-400 text-sm mb-8">
          Configure your interview setting and parameters before starting.
        </p>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 text-sm px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleStartSession} className="space-y-6 bg-gray-900 border border-gray-800 rounded p-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Interview Mode
            </label>
            <div className="grid grid-cols-2 gap-3">
              {INTERVIEW_MODES.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`px-4 py-3 text-sm rounded border text-left transition-colors ${
                    mode === m
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label htmlFor="targetRole" className="block text-sm font-medium text-gray-300 mb-2">
              Target Role (Optional)
            </label>
            <input
              id="targetRole"
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Frontend Engineer"
              className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2.5 rounded focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded transition-colors"
            >
              {isSubmitting ? 'Starting...' : 'Start Session'}
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
