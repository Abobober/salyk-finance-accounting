const API_BASE = '/api'
const ACCESS_KEY = 'finance_access_token'
const REFRESH_KEY = 'finance_refresh_token'

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

function isJsonBody(body: BodyInit | null | undefined): body is string {
  return typeof body === 'string'
}

function parseErrorPayload(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback
  }

  const record = payload as Record<string, unknown>
  const preferred = record.detail ?? record.error ?? record.message
  if (typeof preferred === 'string' && preferred.trim()) {
    return preferred
  }

  for (const value of Object.values(record)) {
    if (typeof value === 'string' && value.trim()) {
      return value
    }
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0]
    }
  }

  return fallback
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getStoredRefreshToken()
  if (!refresh) {
    return false
  }

  const response = await fetch(`${API_BASE}/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  if (!response.ok) {
    clearTokens()
    return false
  }

  const payload = (await response.json()) as { access: string; refresh?: string }
  setTokens(payload.access, payload.refresh ?? refresh)
  return true
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers = new Headers(options.headers)
  const access = localStorage.getItem(ACCESS_KEY)

  if (access) {
    headers.set('Authorization', `Bearer ${access}`)
  }
  if (isJsonBody(options.body) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401 && retry) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      return apiRequest<T>(path, options, false)
    }
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(parseErrorPayload(payload, `Request failed with status ${response.status}`))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getStoredRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

export function toQueryString(params: Record<string, JsonValue | undefined>) {
  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') {
      continue
    }
    searchParams.set(key, String(value))
  }

  const query = searchParams.toString()
  return query ? `?${query}` : ''
}
