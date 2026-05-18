import { apiRequest } from './client'

export interface UnifiedTaxReportResponse {
  pdf_file: string | null
  verbal_report: string
  ai_validation: string
  ai_validation_status?: string
  validation_summary?: string
}

export function generateUnifiedTaxReport(data: { year: number; quarter: 1 | 2 | 3 | 4 }) {
  return apiRequest<UnifiedTaxReportResponse>('/tax/generate-unified-tax/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
