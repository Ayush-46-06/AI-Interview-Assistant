import { create } from 'zustand'
import type { SessionResponse, SessionDetailResponse, AnswerMode } from '../types/api'
import type { WsConnectionStatus } from '../services/websocket.service'

interface SessionState {
  sessions: SessionResponse[]
  totalSessions: number
  currentSession: SessionDetailResponse | null
  isLoading: boolean
  error: string | null

  // Active Interview State
  activeWsStatus: WsConnectionStatus
  isRecording: boolean
  activeTranscript: string
  activeQuestionId: string | null
  activeAnswerText: string
  isAnswerStreaming: boolean
  activeSuggestions: string[]
  answerMode: AnswerMode

  setSessions: (sessions: SessionResponse[], total: number) => void
  setCurrentSession: (session: SessionDetailResponse | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void

  // Active Interview Actions
  setWsStatus: (status: WsConnectionStatus) => void
  setRecording: (recording: boolean) => void
  setTranscript: (transcript: string, questionId: string | null) => void
  appendAnswerChunk: (chunk: string) => void
  setAnswerComplete: (fullAnswer: string) => void
  setSuggestions: (suggestions: string[]) => void
  setAnswerMode: (mode: AnswerMode) => void
  clearActiveInterview: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  totalSessions: 0,
  currentSession: null,
  isLoading: false,
  error: null,

  activeWsStatus: 'closed',
  isRecording: false,
  activeTranscript: '',
  activeQuestionId: null,
  activeAnswerText: '',
  isAnswerStreaming: false,
  activeSuggestions: [],
  answerMode: 'Normal',

  setSessions: (sessions, total) => set({ sessions, totalSessions: total }),
  setCurrentSession: (session) => set({ currentSession: session }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () => set({ sessions: [], totalSessions: 0, currentSession: null, error: null }),

  setWsStatus: (status) => set({ activeWsStatus: status }),
  setRecording: (isRecording) => set({ isRecording }),
  setTranscript: (activeTranscript, activeQuestionId) => set({ activeTranscript, activeQuestionId }),
  appendAnswerChunk: (chunk) => set((state) => ({ 
    activeAnswerText: state.activeAnswerText + chunk,
    isAnswerStreaming: true
  })),
  setAnswerComplete: (activeAnswerText) => set({ activeAnswerText, isAnswerStreaming: false }),
  setSuggestions: (activeSuggestions) => set({ activeSuggestions }),
  setAnswerMode: (answerMode) => set({ answerMode }),
  clearActiveInterview: () => set({
    activeWsStatus: 'closed',
    isRecording: false,
    activeTranscript: '',
    activeQuestionId: null,
    activeAnswerText: '',
    isAnswerStreaming: false,
    activeSuggestions: []
  })
}))
