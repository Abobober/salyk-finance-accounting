const API_BASE = '/api'
const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem(ACCESS_KEY)
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

export function getStoredRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

/** Выполнить запрос с автоматическим refresh при 401 и повторной попыткой */
async function fetchWithAuth<T>(
  path: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : '/' + path}`
  const res = await fetch(url, {
    ...options,
    headers: { ...getAuthHeaders(), ...options.headers } as HeadersInit,
  })

  if (res.status === 401 && !isRetry) {
    const refresh = getStoredRefresh()
    if (refresh) {
      try {
        const refreshRes = await fetch(`${API_BASE}/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        })
        if (refreshRes.ok) {
          const data = await refreshRes.json()
          setTokens(data.access, data.refresh)
          return fetchWithAuth<T>(path, options, true)
        }
      } catch {
        clearTokens()
      }
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = err.detail || err.message || err.error || err[Object.keys(err)[0]]?.[0] || `Ошибка ${res.status}`
    throw new Error(typeof msg === 'string' ? msg : String(msg))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const apiFetch = fetchWithAuth
