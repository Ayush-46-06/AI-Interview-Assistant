// Central TypeScript type definitions mirroring the actual FastAPI backend schemas.
// All types verified against the Pydantic models in app/schemas/*.py

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface LoginRequest {
  username: string // OAuth2 form field — backend expects 'username' for the email
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface UserResponse {
  id: string
  name: string
  email: string
  is_active: boolean
}

// ─── Profile ─────────────────────────────────────────────────────────────────

export interface ContextPreferences {
  experience_years?: number | null
  current_company?: string | null
  key_achievements?: string[] | null
  company_info?: string | null
  behavioral_context?: string | null
  past_projects?: string[] | null
  [key: string]: unknown // allows arbitrary extra context
}

export interface ProfileUpdate {
  target_role?: string | null
  technologies?: string[] | null
  resume_text?: string | null
  jd_text?: string | null
  preferences?: ContextPreferences | null
}

export interface ProfileResponse {
  id: string
  user_id: string
  target_role: string | null
  technologies: string[]
  resume_text: string | null
  jd_text: string | null
  preferences: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── Session ──────────────────────────────────────────────────────────────────

export type AnswerMode = 'Short' | 'Normal' | 'Detailed' | 'STAR'

export interface SessionCreate {
  mode: string
  target_role?: string | null
}

export interface SessionResponse {
  id: string
  user_id: string
  mode: string
  target_role: string | null
  started_at: string
  completed_at: string | null
  status: string
  score: number | null
  question_count: number
  context_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AnswerResponse {
  id: string
  question_id: string
  answer_text: string
  model: string | null
  mode: string | null
  latency_ms: number | null
  token_usage: Record<string, unknown> | null
  is_regenerated: boolean
  created_at: string
}

export interface QuestionResponse {
  id: string
  session_id: string
  transcript: string
  category: string | null
  difficulty: string | null
  is_answered: boolean
  created_at: string
  answers: AnswerResponse[]
}

export interface SessionDetailResponse extends SessionResponse {
  questions: QuestionResponse[]
}

export interface PaginatedSessionResponse {
  sessions: SessionResponse[]
  total: number
}

// ─── Feedback ─────────────────────────────────────────────────────────────────

export interface FeedbackCreate {
  answerId: string // backend uses alias 'answerId'
  rating: number // 1–5
  notes?: string | null
}

export interface FeedbackResponse {
  id: string
  answer_id: string
  rating: number | null
  notes: string | null
  created_at: string
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface AnalyticsResponse {
  total_sessions: number
  completed_sessions: number
  total_questions: number
  answered_questions: number
  average_score: number | null
  average_rating: number | null
}

// ─── Weak Topics ──────────────────────────────────────────────────────────────

export interface WeakTopicResponse {
  id: string
  user_id: string
  topic: string
  category: string | null
  frequency: number
  avg_score: number | null
  last_encountered: string
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export interface SettingsUpdate {
  screen_invisibility_enabled?: boolean | null
  disclaimer_accepted?: boolean | null
  other_preferences?: Record<string, unknown> | null
}

export interface SettingsResponse {
  id: string
  user_id: string
  screen_invisibility_enabled: boolean
  disclaimer_accepted: boolean
  other_preferences: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── WebSocket Events ─────────────────────────────────────────────────────────

// Events sent FROM the client TO the server
export type ClientEventType =
  | 'start_recording'
  | 'audio_chunk'
  | 'stop_recording'
  | 'request_answer'
  | 'regenerate_answer'
  | 'end_session'

export interface ClientEvent {
  event: ClientEventType
  [key: string]: unknown
}

export interface AudioChunkEvent extends ClientEvent {
  event: 'audio_chunk'
  audio: string // base64-encoded audio chunk
}

export interface RequestAnswerEvent extends ClientEvent {
  event: 'request_answer'
  answer_mode?: AnswerMode
}

// Events sent FROM the server TO the client
export type ServerEventType =
  | 'recording_started'
  | 'transcription_complete'
  | 'question_processed'
  | 'answer_streaming'
  | 'answer_complete'
  | 'followup_suggestions'
  | 'session_summary'
  | 'error'

export interface ServerEvent {
  event: ServerEventType
  [key: string]: unknown
}

export interface TranscriptionCompleteEvent extends ServerEvent {
  event: 'transcription_complete'
  transcript: string
  question_id: string
}

export interface QuestionProcessedEvent extends ServerEvent {
  event: 'question_processed'
  question_id: string
  transcript: string
}

export interface AnswerStreamingEvent extends ServerEvent {
  event: 'answer_streaming'
  chunk: string
}

export interface AnswerCompleteEvent extends ServerEvent {
  event: 'answer_complete'
  answer_id: string
  answer_text: string
  mode: string
  latency_ms: number
}

export interface FollowupSuggestionsEvent extends ServerEvent {
  event: 'followup_suggestions'
  suggestions: string[]
}

export interface SessionSummaryEvent extends ServerEvent {
  event: 'session_summary'
  session_id: string
  score: number | null
  total_questions: number
}

export interface ErrorEvent extends ServerEvent {
  event: 'error'
  error: string
}
