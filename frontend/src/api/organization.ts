import { apiFetch } from './client'

export type OrgType = 'ie' | 'llc'
export type TaxRegime = 'single' | 'general'
export type OnboardingStatus = 'not_started' | 'org_type' | 'tax_regime' | 'activities' | 'completed'

export interface OrganizationProfile {
  org_type: OrgType | null
  tax_regime: TaxRegime | null
  onboarding_status: OnboardingStatus
  tax_period_type?: 'preset' | 'custom' | null
  tax_period_type_display?: string
  tax_period_preset?: 'monthly' | 'quarterly' | 'yearly' | null
  tax_period_preset_display?: string
  tax_period_custom_day?: number | null
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
export function updateOrganizationProfile(data: {
  org_type?: OrgType
  tax_regime?: TaxRegime
  tax_period_type?: 'preset' | 'custom'
  tax_period_preset?: 'monthly' | 'quarterly' | 'yearly'
  tax_period_custom_day?: number
}) {
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

/** PATCH /api/organization/activities/:id/ */
export function updateOrganizationActivity(
  id: number,
  data: { cash_tax_rate?: string; non_cash_tax_rate?: string; is_primary?: boolean }
) {
  return apiFetch<OrganizationActivity>(`/organization/activities/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
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
