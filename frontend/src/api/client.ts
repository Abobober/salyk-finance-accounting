const API_BASE = '/api'

export function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : '/' + path}`
  const res = await fetch(url, {
    ...options,
    headers: { ...getAuthHeaders(), ...options.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = err.detail || err.message || err[Object.keys(err)[0]]?.[0] || `Ошибка ${res.status}`
    throw new Error(typeof msg === 'string' ? msg : String(msg))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}
