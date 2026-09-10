import { create } from 'zustand'
import { getProfile, updateContext, uploadResume } from '../services/profile.service'
import type { ProfileResponse, ProfileUpdate } from '../types/api'

interface ProfileState {
  profile: ProfileResponse | null
  isLoading: boolean
  isSaving: boolean
  isUploading: boolean
  error: string | null
  uploadError: string | null

  fetchProfile: () => Promise<void>
  saveProfileContext: (data: ProfileUpdate) => Promise<boolean>
  uploadResumeFile: (file: File) => Promise<boolean>
  clearErrors: () => void
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,
  isSaving: false,
  isUploading: false,
  error: null,
  uploadError: null,

  fetchProfile: async () => {
    set({ isLoading: true, error: null })
    try {
      const profile = await getProfile()
      set({ profile, isLoading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to load profile', isLoading: false })
    }
  },

  saveProfileContext: async (data: ProfileUpdate) => {
    set({ isSaving: true, error: null })
    try {
      // Both updateProfile and updateContext do the same thing under the hood for these fields.
      // We will use updateProfile for generic saves, or updateContext. The backend schema supports all fields in both.
      const profile = await updateContext(data)
      set({ profile, isSaving: false })
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to save context', isSaving: false })
      return false
    }
  },

  uploadResumeFile: async (file: File) => {
    set({ isUploading: true, uploadError: null })
    try {
      const profile = await uploadResume(file)
      set({ profile, isUploading: false })
      return true
    } catch (err) {
      set({ uploadError: err instanceof Error ? err.message : 'Failed to upload resume', isUploading: false })
      return false
    }
  },

  clearErrors: () => {
    set({ error: null, uploadError: null })
  }
}))
