import { apiFetch } from './client'

export type OrgType = 'ie' | 'llc'
export type TaxRegime = 'single' | 'general'
export type OnboardingStatus = 'not_started' | 'org_type' | 'tax_regime' | 'activities' | 'completed'

export interface OrganizationProfile {
  org_type: OrgType | null
  tax_regime: TaxRegime | null
  onboarding_status: OnboardingStatus
}

export interface OrganizationStatus {
  onboarding_status: OnboardingStatus
  is_completed: boolean
}

export interface OrganizationActivity {
  id: number
  activity: number
  activity_name: string
  cash_tax_rate: string
  non_cash_tax_rate: string
  is_primary: boolean
}

/** GET /api/organization/status/ */
export function getOrganizationStatus() {
  return apiFetch<OrganizationStatus>('/organization/status/')
}

/** GET /api/organization/profile/ */
export function getOrganizationProfile() {
  return apiFetch<OrganizationProfile>('/organization/profile/')
}

/** PATCH /api/organization/profile/ */
export function updateOrganizationProfile(data: Partial<Pick<OrganizationProfile, 'org_type' | 'tax_regime'>>) {
  return apiFetch<OrganizationProfile>('/organization/profile/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/** POST /api/organization/activities/ */
export function createOrganizationActivity(data: {
  activity: number
  cash_tax_rate: string
  non_cash_tax_rate: string
  is_primary: boolean
}) {
  return apiFetch<OrganizationActivity>('/organization/activities/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/** GET /api/organization/activities/ */
export function listOrganizationActivities() {
  return apiFetch<OrganizationActivity[] | { results: OrganizationActivity[] }>('/organization/activities/').then(
    (r) => (Array.isArray(r) ? r : (r.results ?? []))
  )
}

/** DELETE /api/organization/activities/:id/ */
export function deleteOrganizationActivity(id: number) {
  return apiFetch<void>(`/organization/activities/${id}/`, { method: 'DELETE' })
}

/** PATCH /api/organization/finalize/ - завершить онбординг */
export function finalizeOnboarding() {
  return apiFetch<OrganizationProfile>('/organization/finalize/', {
    method: 'PATCH',
    body: JSON.stringify({}),
  })
}
