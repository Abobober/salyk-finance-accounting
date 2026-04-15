import { apiRequest, toQueryString } from './client'

export interface ActivityCode {
  id: number
  code: string
  section: string
  name: string
}

interface PaginatedActivityCodes {
  count: number
  next: string | null
  previous: string | null
  results: ActivityCode[]
}

export function listActivityCodes(params: { search?: string; limit?: number; offset?: number } = {}) {
  return apiRequest<PaginatedActivityCodes>(`/activities/${toQueryString(params)}`)
}
