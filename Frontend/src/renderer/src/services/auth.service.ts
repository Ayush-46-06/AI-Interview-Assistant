import { apiPost } from './api'
import type { RegisterRequest, LoginRequest, TokenResponse, UserResponse } from '../types/api'

export async function register(data: RegisterRequest): Promise<UserResponse> {
  // Backend returns 201 with the created user — no token on registration
  return apiPost<UserResponse>('/api/auth/register', data)
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  // Backend auth/login uses OAuth2PasswordRequestForm — must be form-encoded
  const form = new URLSearchParams()
  form.append('username', data.username)
  form.append('password', data.password)

  const res = await fetch(
    `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/auth/login`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString()
    }
  )

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body?.detail ?? detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }

  return res.json() as Promise<TokenResponse>
}

export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/api/auth/refresh', { refresh_token: refreshToken })
}

export async function logout(): Promise<void> {
  await apiPost<{ success: boolean }>('/api/auth/logout')
}
