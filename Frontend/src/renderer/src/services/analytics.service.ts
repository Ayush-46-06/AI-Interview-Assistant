import { apiGet } from './api'
import type { AnalyticsResponse, WeakTopicResponse } from '../types/api'

export function getAnalytics(timeRange: string = 'all'): Promise<AnalyticsResponse> {
  return apiGet<AnalyticsResponse>(`/api/analytics/?timeRange=${timeRange}`)
}

export function getWeakTopics(): Promise<WeakTopicResponse[]> {
  return apiGet<WeakTopicResponse[]>('/api/weak-topics/')
}
