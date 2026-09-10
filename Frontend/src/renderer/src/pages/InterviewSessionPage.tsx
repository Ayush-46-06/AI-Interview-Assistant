import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import { getSession } from '../services/session.service'
import { useSessionStore } from '../store/sessionStore'
import { useWebSocket } from '../hooks/useWebSocket'
import type { AnswerMode } from '../types/api'
import { AlertCircle, Clock, RefreshCw } from 'lucide-react'

function formatDuration(ms: number) {
  const totalSeconds = Math.floor(ms / 1000)
  const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
  const s = (totalSeconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export default function InterviewSessionPage(): React.JSX.Element {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [initError, setInitError] = useState<string | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [micError, setMicError] = useState<string | null>(null)
  const [elapsedTime, setElapsedTime] = useState<number>(0)

  // Session Store
  const {
    currentSession,
    setCurrentSession,
    setWsStatus,
    isRecording,
    setRecording,
    activeTranscript,
    setTranscript,
    activeQuestionId,
    activeAnswerText,
    isAnswerStreaming,
    appendAnswerChunk,
    setAnswerComplete,
    activeSuggestions,
    setSuggestions,
    answerMode,
    setAnswerMode,
    clearActiveInterview
  } = useSessionStore()

  // WebSocket
  const { status: wsStatus, lastEvent, send, disconnect, reconnect } = useWebSocket(sessionId ?? null)

  // MediaRecorder refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Initialize Session
  useEffect(() => {
    if (!sessionId) return
    setIsInitializing(true)
    clearActiveInterview()
    
    getSession(sessionId)
      .then((session) => {
        setCurrentSession(session)
        setIsInitializing(false)
      })
      .catch((err) => {
        setInitError(err instanceof Error ? err.message : 'Failed to load session')
        setIsInitializing(false)
      })

    return () => {
      stopRecordingCleanup()
      disconnect()
      clearActiveInterview()
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
    }
  }, [sessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Timer Effect
  useEffect(() => {
    if (currentSession?.started_at && currentSession.status !== 'completed') {
      const startTime = new Date(currentSession.started_at).getTime()
      
      const updateTimer = () => {
        const now = Date.now()
        setElapsedTime(Math.max(0, now - startTime))
      }
      
      updateTimer() // initial tick
      timerIntervalRef.current = setInterval(updateTimer, 1000)
    } else if (currentSession?.status === 'completed') {
       if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
    }

    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
    }
  }, [currentSession?.started_at, currentSession?.status])

  // Sync WS status to store for global visibility if needed
  useEffect(() => {
    setWsStatus(wsStatus)
    // If WS disconnected while recording, stop recording to prevent orphaned streams
    if ((wsStatus === 'closed' || wsStatus === 'error') && isRecording) {
      setRecording(false)
      stopRecordingCleanup()
      setMicError('Connection lost. Recording stopped.')
    }
  }, [wsStatus, setWsStatus, isRecording, setRecording])

  // Handle Server Events
  useEffect(() => {
    if (!lastEvent) return

    switch (lastEvent.event) {
      case 'recording_started':
        setRecording(true)
        setMicError(null)
        break
      case 'transcription_complete':
        setTranscript(lastEvent.transcript as string, activeQuestionId)
        break
      case 'question_processed':
        setTranscript(lastEvent.transcript as string, lastEvent.question_id as string)
        break
      case 'answer_streaming':
        appendAnswerChunk(lastEvent.chunk as string)
        break
      case 'answer_complete':
        setAnswerComplete(lastEvent.answer_text as string)
        break
      case 'followup_suggestions':
        setSuggestions(lastEvent.suggestions as string[])
        break
      case 'session_summary':
        setCurrentSession({
          ...currentSession!,
          status: 'completed',
          score: lastEvent.score as number | null,
          question_count: lastEvent.total_questions as number
        })
        break
      case 'error':
        setMicError(`Backend error: ${lastEvent.error}`)
        break
    }
  }, [lastEvent]) // eslint-disable-line react-hooks/exhaustive-deps

  // Audio Pipeline
  async function handleToggleRecording() {
    setMicError(null)
    
    if (isRecording) {
      // Stop Recording
      send({ event: 'stop_recording' })
      setRecording(false) // Optimistic update
      stopRecordingCleanup()
    } else {
      // Start Recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
        
        // Use webm opus
        const options = { mimeType: 'audio/webm;codecs=opus' }
        const mediaRecorder = new MediaRecorder(stream, options)
        mediaRecorderRef.current = mediaRecorder

        send({ event: 'start_recording' })

        mediaRecorder.ondataavailable = async (e) => {
          if (e.data.size > 0 && wsStatus === 'open') {
            const buffer = await e.data.arrayBuffer()
            const base64Data = btoa(
              new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
            )
            send({
              event: 'audio_chunk',
              payload: { audio: base64Data }
            })
          }
        }

        // Start with a small timeslice to stream chunks to the backend
        mediaRecorder.start(500)
      } catch (err) {
        stopRecordingCleanup()
        if (err instanceof DOMException) {
          if (err.name === 'NotAllowedError') setMicError('Microphone access was denied. Please allow permissions.')
          else if (err.name === 'NotFoundError') setMicError('No microphone found on this device.')
          else setMicError(`Microphone error: ${err.message}`)
        } else {
          setMicError('Could not initialize recording.')
        }
      }
    }
  }

  function stopRecordingCleanup() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch (e) { /* ignore state errors */ }
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }

  // Actions
  function handleRequestAnswer() {
    if (!activeQuestionId || isRecording || isAnswerStreaming) return
    send({
      event: 'request_answer',
      payload: { mode: answerMode }
    })
  }

  function handleRegenerateAnswer() {
    if (!activeQuestionId || isRecording || isAnswerStreaming) return
    
    // Clear current answer optimistically
    useSessionStore.setState({ activeAnswerText: '', isAnswerStreaming: true })
    
    send({
      event: 'regenerate_answer',
      payload: { mode: answerMode }
    })
  }

  function handleEndSession() {
    if (!window.confirm('Are you sure you want to end this interview session?')) return
    send({ event: 'end_session' })
  }

  if (isInitializing) {
    return (
      <AppLayout>
        <div className="flex h-full items-center justify-center text-gray-500">
          Loading workspace...
        </div>
      </AppLayout>
    )
  }

  if (initError || !currentSession) {
    return (
      <AppLayout>
        <div className="p-8">
          <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded text-sm">
            {initError || 'Session not found'}
          </div>
          <button onClick={() => navigate('/')} className="mt-4 text-blue-400 text-sm hover:underline">
            ← Back to Dashboard
          </button>
        </div>
      </AppLayout>
    )
  }

  const isSessionEnded = currentSession.status === 'completed'
  const isWsDisconnected = !isSessionEnded && (wsStatus === 'closed' || wsStatus === 'error')

  return (
    <AppLayout>
      <div className="flex flex-col h-full bg-gray-950">
        {/* Header */}
        <header className="shrink-0 flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900">
          <div>
            <h1 className="text-lg font-semibold text-white">Interview Workspace</h1>
            <div className="flex items-center gap-3 mt-1 text-xs">
              <span className="px-2 py-0.5 rounded-full bg-blue-900/40 text-blue-300 border border-blue-800">
                {currentSession.mode}
              </span>
              {currentSession.target_role && (
                <span className="text-gray-400">{currentSession.target_role}</span>
              )}
              <span className="text-gray-500">|</span>
              <span className="text-gray-400 flex items-center gap-1">
                <Clock size={12} /> {formatDuration(elapsedTime)}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400 text-sm">
              Status: <strong className={wsStatus === 'open' ? 'text-green-400' : 'text-amber-400'}>{wsStatus}</strong>
            </span>
            {!isSessionEnded && (
              <button
                onClick={handleEndSession}
                className="px-4 py-1.5 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors text-sm font-medium border border-red-800/50"
              >
                End Session
              </button>
            )}
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 relative">
          
          {/* Connection Lost Banner */}
          {isWsDisconnected && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-amber-900/90 border border-amber-500 text-amber-100 px-6 py-3 rounded-lg shadow-lg flex items-center gap-4 backdrop-blur-sm">
              <AlertCircle size={20} />
              <span className="text-sm font-medium">Connection to server lost.</span>
              <button 
                onClick={() => {
                  setMicError(null)
                  reconnect()
                }}
                className="bg-amber-800 hover:bg-amber-700 text-white px-3 py-1.5 rounded text-xs font-medium flex items-center gap-2 transition"
              >
                <RefreshCw size={14} /> Reconnect
              </button>
            </div>
          )}

          {isSessionEnded ? (
            <div className="max-w-2xl mx-auto text-center mt-12 bg-gray-900 border border-gray-800 p-8 rounded-lg">
              <div className="w-16 h-16 bg-green-900/30 text-green-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-800/50">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Session Completed</h2>
              <p className="text-gray-400 mb-6">Great job! The interview has been finalized.</p>
              
              <div className="grid grid-cols-2 gap-4 text-left max-w-sm mx-auto mb-8">
                <div className="bg-gray-800 p-4 rounded border border-gray-700">
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Questions Answered</p>
                  <p className="text-2xl text-white font-semibold">{currentSession.question_count}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded border border-gray-700">
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Overall Score</p>
                  <p className="text-2xl text-white font-semibold">
                    {currentSession.score != null ? currentSession.score.toFixed(1) : '—'}
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => navigate('/history')}
                className="bg-blue-600 text-white px-8 py-2.5 rounded font-medium hover:bg-blue-700 transition shadow-sm"
              >
                View History
              </button>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6 pb-12">
              
              {/* Audio Controls */}
              <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="text-sm font-medium text-white mb-1">Microphone Input</h3>
                    <p className="text-xs text-gray-400">
                      {isRecording ? 'Listening and streaming...' : 'Ready to record your question/answer'}
                    </p>
                  </div>
                  <button
                    onClick={handleToggleRecording}
                    disabled={isAnswerStreaming || wsStatus !== 'open'}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded font-medium text-sm transition-all shadow-sm ${
                      isRecording 
                        ? 'bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30' 
                        : 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:bg-gray-700'
                    }`}
                  >
                    {isRecording ? (
                      <>
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                        Stop Recording
                      </>
                    ) : (
                      'Start Recording'
                    )}
                  </button>
                </div>
                {micError && (
                  <div className="mt-3 text-xs text-red-400 flex items-center gap-1.5 bg-red-900/20 px-3 py-2 rounded">
                    <AlertCircle size={14} /> {micError}
                  </div>
                )}
              </div>

              {/* Transcript */}
              <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden flex flex-col focus-within:border-gray-600 transition-colors">
                <div className="px-5 py-3 border-b border-gray-800 bg-gray-800/50 flex justify-between items-center">
                  <h3 className="text-sm font-medium text-gray-300">Question / Transcript</h3>
                  {activeTranscript && !isRecording && (
                     <button 
                       onClick={() => setTranscript('', null)}
                       className="text-xs text-gray-400 hover:text-white transition-colors"
                     >
                       Clear
                     </button>
                  )}
                </div>
                <div className="relative">
                  {!activeTranscript && !isRecording && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <span className="text-gray-600 text-sm italic">Waiting for voice input...</span>
                    </div>
                  )}
                  <textarea
                    className="w-full h-32 bg-transparent text-white p-5 resize-y focus:outline-none focus:bg-gray-800/30 text-sm leading-relaxed relative z-10"
                    placeholder=""
                    value={activeTranscript}
                    disabled={isRecording}
                    onChange={(e) => setTranscript(e.target.value, activeQuestionId)}
                  />
                </div>
              </div>

              {/* Action Bar */}
              <div className="flex items-center gap-4 bg-gray-900 border border-gray-800 p-4 rounded-lg">
                <div className="flex-1 flex items-center gap-3">
                  <label className="text-sm text-gray-400">Answer Mode:</label>
                  <select 
                    className="bg-gray-800 border border-gray-700 text-white text-sm rounded px-3 py-1.5 focus:outline-none focus:border-blue-500 transition-colors"
                    value={answerMode}
                    onChange={(e) => setAnswerMode(e.target.value as AnswerMode)}
                    disabled={isRecording || isAnswerStreaming}
                  >
                    <option value="Short">Short</option>
                    <option value="Normal">Normal</option>
                    <option value="Detailed">Detailed</option>
                    <option value="STAR">STAR Method</option>
                  </select>
                </div>
                
                <button
                  onClick={handleRequestAnswer}
                  disabled={!activeQuestionId || isRecording || isAnswerStreaming || !activeTranscript || wsStatus !== 'open'}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-6 py-2 rounded transition shadow-sm"
                >
                  Request Answer
                </button>
                {activeAnswerText && !isAnswerStreaming && (
                  <button
                    onClick={handleRegenerateAnswer}
                    disabled={isRecording || wsStatus !== 'open'}
                    className="bg-gray-800 hover:bg-gray-700 border border-gray-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition"
                  >
                    Regenerate
                  </button>
                )}
              </div>

              {/* AI Answer */}
              <div className="bg-gray-900 border border-gray-800 rounded-lg flex flex-col min-h-[12rem] shadow-sm">
                <div className="px-5 py-3 border-b border-gray-800 bg-gray-800/50 flex justify-between items-center">
                  <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    AI Response
                    {isAnswerStreaming && (
                      <span className="flex gap-1 ml-2">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    )}
                  </h3>
                </div>
                <div className="p-6 text-gray-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {activeAnswerText ? (
                     <span>{activeAnswerText}</span>
                  ) : (
                     <span className="text-gray-600 flex items-center justify-center h-full italic mt-8">No answer generated yet. Request one above.</span>
                  )}
                </div>
              </div>

              {/* Follow-up Suggestions */}
              {activeSuggestions.length > 0 && !isRecording && !isAnswerStreaming && (
                <div className="space-y-3 pt-2">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-1">Suggested Follow-ups</h3>
                  <div className="flex flex-wrap gap-2">
                    {activeSuggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setTranscript(suggestion, null)
                          window.scrollTo({ top: 0, behavior: 'smooth' })
                        }}
                        className="text-left text-sm bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 hover:border-gray-500 hover:text-white px-4 py-2 rounded-full transition-all"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </main>
      </div>
    </AppLayout>
  )
}
