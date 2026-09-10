import { apiPost } from './api'
import type { FeedbackCreate, FeedbackResponse } from '../types/api'

export function submitFeedback(data: FeedbackCreate): Promise<FeedbackResponse> {
  return apiPost<FeedbackResponse>('/api/feedback/', data)
}
