import { create } from 'zustand'
import { setAccessToken, setRefreshFailedHandler, apiGet } from '../services/api'
import { login as apiLogin, logout as apiLogout, register as apiRegister } from '../services/auth.service'
import type { UserResponse, LoginRequest, RegisterRequest } from '../types/api'

interface AuthState {
  user: UserResponse | null
  isLoading: boolean
  error: string | null
  isAuthenticated: boolean

  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  restoreSession: () => Promise<boolean>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => {
  // If the backend says our access token is invalid and refresh fails,
  // force a logout so the user is sent back to the login screen.
  setRefreshFailedHandler(() => {
    set({ user: null, isAuthenticated: false })
    setAccessToken(null)
    window.electronStore.delete('refresh_token').catch(() => {})
  })

  return {
    user: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,

    async login(data: LoginRequest) {
      set({ isLoading: true, error: null })
      try {
        const tokens = await apiLogin(data)
        setAccessToken(tokens.access_token)
        await window.electronStore.set('refresh_token', tokens.refresh_token)

        // Fetch user profile to populate store
        const user = await apiGet<UserResponse>('/api/auth/me').catch(() => null)

        set({ isAuthenticated: true, user, isLoading: false })
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Login failed'
        set({ error: msg, isLoading: false, isAuthenticated: false })
      }
    },

    async register(data: RegisterRequest) {
      set({ isLoading: true, error: null })
      try {
        await apiRegister(data)
        set({ isLoading: false })
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Registration failed'
        set({ error: msg, isLoading: false })
      }
    },

    async logout() {
      try {
        await apiLogout()
      } catch {
        // Proceed with local logout even if backend call fails
      }
      setAccessToken(null)
      await window.electronStore.delete('refresh_token').catch(() => {})
      set({ user: null, isAuthenticated: false, error: null })
    },

    async restoreSession(): Promise<boolean> {
      const storedRefresh = await window.electronStore.get('refresh_token').catch(() => null)
      if (!storedRefresh) return false

      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/auth/refresh`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: storedRefresh })
          }
        )
        if (!res.ok) return false
        const tokens = await res.json()
        setAccessToken(tokens.access_token)
        await window.electronStore.set('refresh_token', tokens.refresh_token)

        const user = await apiGet<UserResponse>('/api/auth/me').catch(() => null)
        set({ isAuthenticated: true, user })
        return true
      } catch {
        return false
      }
    },

    clearError() {
      set({ error: null })
    }
  }
})
