
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

// Wraps protected routes — redirects to /login if not authenticated.
export default function ProtectedRoute({ children }: { children: React.ReactNode }): React.JSX.Element {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
