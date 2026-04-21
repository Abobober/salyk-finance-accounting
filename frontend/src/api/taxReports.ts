import { apiRequest } from './client'

export interface UnifiedTaxReportResponse {
  report_data: Record<string, unknown>
  pdf_file: string
  ai_validation: string
}

export function generateUnifiedTaxReport(data: { year: number; quarter: 1 | 2 | 3 | 4 }) {
  return apiRequest<UnifiedTaxReportResponse>('/tax/generate-unified-tax/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
