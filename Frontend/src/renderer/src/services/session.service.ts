import { apiGet, apiPost } from './api'
import type {
  SessionCreate,
  SessionResponse,
  PaginatedSessionResponse,
  SessionDetailResponse
} from '../types/api'

export function createSession(data: SessionCreate): Promise<SessionResponse> {
  return apiPost<SessionResponse>('/api/sessions/', data)
}

export function listSessions(page = 1, limit = 10): Promise<PaginatedSessionResponse> {
  return apiGet<PaginatedSessionResponse>(`/api/sessions/?page=${page}&limit=${limit}`)
}

export function getSession(sessionId: string): Promise<SessionDetailResponse> {
  return apiGet<SessionDetailResponse>(`/api/sessions/${sessionId}`)
}
