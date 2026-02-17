import { apiFetch } from '@/api/client'

export interface UnifiedTaxRequest {
  year: number
  quarter: 1 | 2 | 3 | 4
}

export interface UnifiedTaxReportResponse {
  report_data: Record<string, unknown>
  pdf_file: string
  ai_validation: string
}

export function generateUnifiedTaxReport(payload: UnifiedTaxRequest) {
  return apiFetch<UnifiedTaxReportResponse>('/tax/generate-unified-tax/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
