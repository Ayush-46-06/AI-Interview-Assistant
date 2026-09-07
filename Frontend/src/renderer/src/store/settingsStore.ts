import { create } from 'zustand'
import type { SettingsResponse, SettingsUpdate } from '../types/api'
import { updateSettings } from '../services/settings.service'

// Safe defaults — GET /api/settings does not exist in the current backend.
// The actual values are only known after a successful PUT response.
const DEFAULTS: Omit<SettingsResponse, 'id' | 'user_id' | 'created_at' | 'updated_at'> = {
  screen_invisibility_enabled: false,
  disclaimer_accepted: false,
  other_preferences: {}
}

interface SettingsState {
  settings: typeof DEFAULTS
  isSaving: boolean
  error: string | null

  applyResponse: (response: SettingsResponse) => void
  update: (data: SettingsUpdate) => Promise<void>
  clearError: () => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: { ...DEFAULTS },
  isSaving: false,
  error: null,

  applyResponse(response: SettingsResponse) {
    set({
      settings: {
        screen_invisibility_enabled: response.screen_invisibility_enabled,
        disclaimer_accepted: response.disclaimer_accepted,
        other_preferences: response.other_preferences
      }
    })
  },

  async update(data: SettingsUpdate) {
    set({ isSaving: true, error: null })
    try {
      const response = await updateSettings(data)
      set({
        settings: {
          screen_invisibility_enabled: response.screen_invisibility_enabled,
          disclaimer_accepted: response.disclaimer_accepted,
          other_preferences: response.other_preferences
        },
        isSaving: false
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update settings'
      set({ error: msg, isSaving: false })
    }
  },

  clearError() {
    set({ error: null })
  }
}))
