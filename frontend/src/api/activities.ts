import { apiFetch } from './client'

export interface ActivityCode {
  id: number
  code: string
  section: string
  name: string
}

/** GET /api/activities/ - список видов деятельности ГКЭД (paginated) */
export function listActivityCodes(params?: { search?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams()
  if (params?.search) q.set('search', params.search)
  q.set('limit', String(params?.limit ?? 500))
  if (params?.offset != null) q.set('offset', String(params.offset))
  return apiFetch<{ results?: ActivityCode[] } | ActivityCode[]>(`/activities/?${q.toString()}`).then(
    (r) => (Array.isArray(r) ? r : (r.results ?? []))
  )
}
