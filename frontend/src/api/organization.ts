import { apiRequest, toQueryString } from './client'

export type OrgType = 'ie' | 'llc'
export type TaxRegime = 'single' | 'general'
export type TaxPeriodType = 'preset' | 'custom'
export type TaxPeriodPreset = 'monthly' | 'quarterly' | 'yearly'
export type OnboardingStatus = 'not_started' | 'org_type' | 'tax_regime' | 'activities' | 'completed'

export interface OrganizationProfile {
  org_type: OrgType | null
  tax_regime: TaxRegime | null
  onboarding_status: OnboardingStatus
  tax_period_type: TaxPeriodType | null
  tax_period_type_display?: string
  tax_period_preset: TaxPeriodPreset | null
  tax_period_preset_display?: string
  tax_period_custom_day: number | null
}

export interface OrganizationStatusResponse {
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

interface PaginatedOrganizationActivities {
  count: number
  next: string | null
  previous: string | null
  results: OrganizationActivity[]
}

export interface TaxPeriodResponse {
  tax_period_type: TaxPeriodType
  tax_period_preset: TaxPeriodPreset | null
  tax_period_custom_day: number | null
  current_period: {
    start: string
    end: string
  }
  next_period_start: string
}

export function getOrganizationStatus() {
  return apiRequest<OrganizationStatusResponse>('/organization/status/')
}

export function getOrganizationProfile() {
  return apiRequest<OrganizationProfile>('/organization/profile/')
}

export function updateOrganizationProfile(
  data: Partial<{
    org_type: OrgType
    tax_regime: TaxRegime
    tax_period_type: TaxPeriodType | null
    tax_period_preset: TaxPeriodPreset | null
    tax_period_custom_day: number | null
  }>,
) {
  return apiRequest<OrganizationProfile>('/organization/profile/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function finalizeOnboarding() {
  return apiRequest<OrganizationProfile>('/organization/finalize/', {
    method: 'PATCH',
    body: JSON.stringify({}),
  })
}

export function listOrganizationActivities(params: { limit?: number; offset?: number } = { limit: 100 }) {
  return apiRequest<PaginatedOrganizationActivities>(
    `/organization/activities/${toQueryString(params)}`,
  )
}

export function createOrganizationActivity(data: {
  activity: number
  cash_tax_rate: string
  non_cash_tax_rate: string
  is_primary: boolean
}) {
  return apiRequest<OrganizationActivity>('/organization/activities/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateOrganizationActivity(
  id: number,
  data: Partial<{
    cash_tax_rate: string
    non_cash_tax_rate: string
    is_primary: boolean
  }>,
) {
  return apiRequest<OrganizationActivity>(`/organization/activities/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteOrganizationActivity(id: number) {
  return apiRequest<void>(`/organization/activities/${id}/`, {
    method: 'DELETE',
  })
}

export function getTaxPeriod() {
  return apiRequest<TaxPeriodResponse>('/organization/tax-period/')
}
