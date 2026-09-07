import { create } from 'zustand'
import type { SessionResponse, SessionDetailResponse } from '../types/api'

interface SessionState {
  sessions: SessionResponse[]
  totalSessions: number
  currentSession: SessionDetailResponse | null
  isLoading: boolean
  error: string | null

  setSessions: (sessions: SessionResponse[], total: number) => void
  setCurrentSession: (session: SessionDetailResponse | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  totalSessions: 0,
  currentSession: null,
  isLoading: false,
  error: null,

  setSessions: (sessions, total) => set({ sessions, totalSessions: total }),
  setCurrentSession: (session) => set({ currentSession: session }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () => set({ sessions: [], totalSessions: 0, currentSession: null, error: null })
}))
