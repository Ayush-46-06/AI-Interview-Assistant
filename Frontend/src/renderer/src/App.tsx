import { useEffect, useState } from 'react'
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import HistoryPage from './pages/HistoryPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'
import InterviewSessionPage from './pages/InterviewSessionPage'
import NewSessionPage from './pages/NewSessionPage'
import ContextPage from './pages/ContextPage'
import SessionDetailPage from './pages/SessionDetailPage'

function App(): React.JSX.Element {
  const [restoring, setRestoring] = useState(true)
  const restoreSession = useAuthStore((s) => s.restoreSession)

  // Attempt to restore auth from a stored refresh token before rendering routes.
  useEffect(() => {
    restoreSession().finally(() => setRestoring(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (restoring) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-500 text-sm">Loading…</p>
      </div>
    )
  }

  return (
    <HashRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/:sessionId"
          element={
            <ProtectedRoute>
              <InterviewSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/new"
          element={
            <ProtectedRoute>
              <NewSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history/:sessionId"
          element={
            <ProtectedRoute>
              <SessionDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <AnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/context"
          element={
            <ProtectedRoute>
              <ContextPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  )
}

export default App
