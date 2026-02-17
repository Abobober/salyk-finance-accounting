import type { LoginRequest, RegisterRequest, TokenPair } from './types'
import { getAuthHeaders } from './client'

const API_BASE = '/api'

/** POST /api/token/ - получить access и refresh токены */
export async function login(credentials: LoginRequest): Promise<TokenPair> {
  const res = await fetch(`${API_BASE}/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.email?.[0] || 'Ошибка авторизации')
  }
  return res.json()
}

/** POST /api/token/refresh/ - обновить access (и refresh при ROTATE_REFRESH_TOKENS) */
export async function refreshToken(refresh: string): Promise<TokenPair> {
  const res = await fetch(`${API_BASE}/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) throw new Error('Не удалось обновить сессию')
  return res.json()
}

/** POST /api/users/register/ - регистрация */
export async function register(data: RegisterRequest): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/users/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = err.password?.[0] || err.email?.[0] || err.password2?.[0] || err.detail || 'Ошибка регистрации'
    throw new Error(typeof msg === 'string' ? msg : msg[0])
  }
  return res.json()
}

/** GET /api/users/me/ - текущий пользователь */
export async function getCurrentUser() {
  const res = await fetch(`${API_BASE}/users/me/`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) throw new Error('Сессия истекла')
  return res.json()
}

/** GET /api/users/profile/ - получить профиль */
export async function getProfile() {
  const res = await fetch(`${API_BASE}/users/profile/`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) throw new Error('Ошибка загрузки профиля')
  return res.json()
}

/** PATCH /api/users/profile/ - обновить профиль */
export async function updateProfile(data: { first_name?: string; last_name?: string; email?: string }) {
  const res = await fetch(`${API_BASE}/users/profile/`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Ошибка обновления профиля')
  }
  return res.json()
}

/** POST /api/users/logout/ - выход, blacklist refresh токена */
export async function logoutApi(refresh: string) {
  const res = await fetch(`${API_BASE}/users/logout/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Ошибка выхода')
  }
}
