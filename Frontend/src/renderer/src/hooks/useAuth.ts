import { useEffect } from 'react'
import { useAuthStore } from '../store/authStore'

/**
 * Convenience hook to get authenticated user state and auth actions.
 */
export function useAuth() {
  return useAuthStore()
}

/**
 * Attempt to restore a session from a stored refresh token on mount.
 * Only runs once at application startup.
 */
export function useSessionRestore() {
  const restoreSession = useAuthStore((s) => s.restoreSession)

  useEffect(() => {
    restoreSession()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
