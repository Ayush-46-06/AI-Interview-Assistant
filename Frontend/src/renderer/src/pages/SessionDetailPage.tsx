import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import { getSession } from '../services/session.service'
import { submitFeedback } from '../services/feedback.service'
import type { SessionDetailResponse, QuestionResponse, AnswerResponse } from '../types/api'
import { ArrowLeft, Check, Star } from 'lucide-react'

export default function SessionDetailPage(): React.JSX.Element {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetailResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    setIsLoading(true)
    getSession(sessionId)
      .then(setSession)
      .catch((err) => setError(err.message || 'Failed to load session details'))
      .finally(() => setIsLoading(false))
  }, [sessionId])

  if (isLoading) {
    return (
      <AppLayout>
        <div className="p-8 text-gray-500 text-sm">Loading session details...</div>
      </AppLayout>
    )
  }

  if (error || !session) {
    return (
      <AppLayout>
        <div className="p-8">
          <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded text-sm">
            {error || 'Session not found'}
          </div>
          <button onClick={() => navigate('/history')} className="mt-4 text-blue-400 text-sm hover:underline">
            ← Back to History
          </button>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="h-full flex flex-col bg-gray-950">
        <header className="shrink-0 px-6 py-4 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/history')}
              className="text-gray-400 hover:text-white transition"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-white">Session Review</h1>
              <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                <span className="capitalize">{session.mode}</span>
                {session.target_role && <span>| {session.target_role}</span>}
                <span>| {new Date(session.started_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-white capitalize">{session.status}</div>
            {session.score != null && (
              <div className="text-xs text-blue-400 mt-1">Score: {session.score.toFixed(1)} / 10</div>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-8">
            {(!session.questions || session.questions.length === 0) ? (
              <div className="bg-gray-900 border border-gray-800 rounded p-8 text-center text-gray-500 text-sm">
                No questions recorded for this session.
              </div>
            ) : (
              session.questions.map((q, i) => (
                <QuestionCard key={q.id} question={q} index={i} />
              ))
            )}
          </div>
        </main>
      </div>
    </AppLayout>
  )
}

function QuestionCard({ question, index }: { question: QuestionResponse; index: number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <div className="bg-gray-800/50 px-5 py-4 border-b border-gray-800 flex justify-between items-start">
        <div>
          <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
            Question {index + 1}
          </span>
          <p className="text-gray-200 mt-2 text-sm leading-relaxed">{question.transcript}</p>
        </div>
        {question.category && (
          <span className="text-xs bg-gray-800 border border-gray-700 text-gray-400 px-2 py-1 rounded">
            {question.category}
          </span>
        )}
      </div>
      
      <div className="p-5 space-y-6">
        {(!question.answers || question.answers.length === 0) ? (
          <div className="text-sm text-gray-500 italic">No answers generated for this question.</div>
        ) : (
          question.answers.map((ans, i) => (
            <AnswerCard key={ans.id} answer={ans} isLatest={i === question.answers.length - 1} />
          ))
        )}
      </div>
    </div>
  )
}

function AnswerCard({ answer, isLatest }: { answer: AnswerResponse; isLatest: boolean }) {
  const [rating, setRating] = useState<number>(0)
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFeedbackSubmit() {
    if (rating < 1 || rating > 5) return
    setIsSubmitting(true)
    setError(null)
    
    try {
      await submitFeedback({
        answerId: answer.id,
        rating,
        notes: notes.trim() || null
      })
      setIsSubmitted(true)
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-gray-400">AI Response</span>
        {!isLatest && <span className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded">Previous Version</span>}
        {answer.mode && <span className="text-xs text-gray-500">({answer.mode})</span>}
      </div>
      
      <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap bg-gray-800/20 p-4 rounded border border-gray-800/50">
        {answer.answer_text}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-800/50">
        {isSubmitted ? (
          <div className="text-sm text-green-400 flex items-center gap-2">
            <Check size={16} /> Feedback submitted successfully
          </div>
        ) : (
          <div className="space-y-3 max-w-md">
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400 font-medium">Rate this answer:</span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    disabled={isSubmitting}
                    onClick={() => setRating(star)}
                    className={`focus:outline-none transition-colors ${
                      rating >= star ? 'text-yellow-400' : 'text-gray-600 hover:text-gray-500'
                    }`}
                  >
                    <Star size={18} fill={rating >= star ? "currentColor" : "none"} />
                  </button>
                ))}
              </div>
            </div>
            
            {rating > 0 && (
              <div className="space-y-2">
                <textarea
                  placeholder="Optional notes about this answer..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={isSubmitting}
                  className="w-full bg-gray-800 border border-gray-700 rounded text-sm text-white p-2 h-20 focus:outline-none focus:border-blue-500 resize-none"
                />
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-red-400">{error}</span>
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={isSubmitting}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium transition disabled:opacity-50"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
