// Central API client. All HTTP communication with the FastAPI backend goes
// through this module. Never import fetch() elsewhere for backend calls.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// Token store — lives in memory only; persistent storage is handled by the
// Electron main process via IPC (see preload bridge).
let _accessToken: string | null = null
let _onRefreshFailed: (() => void) | null = null

export function setAccessToken(token: string | null): void {
  _accessToken = token
}

export function getAccessToken(): string | null {
  return _accessToken
}

export function setRefreshFailedHandler(handler: () => void): void {
  _onRefreshFailed = handler
}

// ─── Internal fetch wrapper ───────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  retryOnUnauthorized = true
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>)
  }

  // Attach content-type unless caller provided multipart (FormData)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (_accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401 && retryOnUnauthorized) {
    // Attempt refresh once
    const refreshed = await attemptTokenRefresh()
    if (refreshed) {
      return request<T>(path, options, false)
    }
    _onRefreshFailed?.()
    throw new ApiError(401, 'Unauthorized')
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body?.detail ?? detail
    } catch {
      // body was not JSON
    }
    throw new ApiError(res.status, detail)
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T

  return res.json() as Promise<T>
}

// ─── Token refresh ────────────────────────────────────────────────────────────

let _refreshing: Promise<boolean> | null = null

async function attemptTokenRefresh(): Promise<boolean> {
  // Coalesce concurrent refresh calls
  if (_refreshing) return _refreshing

  _refreshing = (async () => {
    try {
      const stored = await window.electronStore.get('refresh_token')
      if (!stored) return false

      const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: stored })
      })

      if (!res.ok) {
        await window.electronStore.delete('refresh_token')
        return false
      }

      const data = await res.json()
      setAccessToken(data.access_token)
      await window.electronStore.set('refresh_token', data.refresh_token)
      return true
    } catch {
      return false
    } finally {
      _refreshing = null
    }
  })()

  return _refreshing
}

// ─── Error class ─────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// ─── Public helpers ───────────────────────────────────────────────────────────

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' })
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body)
  })
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: JSON.stringify(body)
  })
}

export function buildWsUrl(sessionId: string): string {
  const wsBase = BASE_URL.replace(/^http/, 'ws')
  return `${wsBase}/ws/interview/${sessionId}?token=${_accessToken ?? ''}`
}
