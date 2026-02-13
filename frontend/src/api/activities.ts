import { apiFetch } from './client'

export interface ActivityCode {
  id: number
  code: string
  section: string
  name: string
}

/** GET /api/activities/ - список видов деятельности ГКЭД */
export function listActivityCodes(search?: string) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  params.set('limit', '500')
  const q = params.toString()
  return apiFetch<{ results?: ActivityCode[] } | ActivityCode[]>(`/activities/?${q}`).then(
    (r) => (Array.isArray(r) ? r : (r.results ?? []))
  )
}
