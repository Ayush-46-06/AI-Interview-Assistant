import { apiGet, apiPost, apiPut } from './api'
import type { ProfileResponse, ProfileUpdate, ContextUpdate } from '../types/api'

export function getProfile(): Promise<ProfileResponse> {
  return apiGet<ProfileResponse>('/api/profile/')
}

export function updateProfile(data: ProfileUpdate): Promise<ProfileResponse> {
  return apiPut<ProfileResponse>('/api/profile/', data)
}

export function updateContext(data: ContextUpdate): Promise<ProfileResponse> {
  return apiPost<ProfileResponse>('/api/profile/context', data)
}

export function uploadResume(file: File): Promise<ProfileResponse> {
  const formData = new FormData()
  formData.append('file', file) // Backend explicitly uses 'file' for the UploadFile parameter
  return apiPost<ProfileResponse>('/api/profile/resume', formData)
}
