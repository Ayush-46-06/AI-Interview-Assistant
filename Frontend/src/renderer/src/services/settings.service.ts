import { apiPut } from './api'
import type { SettingsUpdate, SettingsResponse } from '../types/api'

// GET /api/settings does not exist in the current backend contract.
// Settings are read from the response of the PUT call or from local defaults.

export function updateSettings(data: SettingsUpdate): Promise<SettingsResponse> {
  return apiPut<SettingsResponse>('/api/settings', data)
}
