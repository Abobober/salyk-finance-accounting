import { apiRequest, toQueryString } from './client'

export type TransactionType = 'income' | 'expense'
export type PaymentMethod = 'cash' | 'non_cash'

export interface Category {
  id: number
  name: string
  category_type: TransactionType
  category_type_display?: string
  is_system: boolean
  created_at: string
}

interface PaginatedCategories {
  count: number
  next: string | null
  previous: string | null
  results: Category[]
}

export interface Transaction {
  id: number
  amount: string
  transaction_type: TransactionType
  category: number | null
  category_name: string | null
  description: string
  transaction_date: string
  created_at: string
  payment_method: PaymentMethod
  is_business: boolean
  is_taxable: boolean
  activity_code: number | null
  activity_code_name: string | null
  cash_tax_rate: string | null
  non_cash_tax_rate: string | null
}

export interface TransactionDraft {
  amount: string
  transaction_type: TransactionType
  category: number | null
  description: string
  transaction_date: string
  payment_method: PaymentMethod
  is_business: boolean
  is_taxable: boolean
  activity_code: number | null
}

export interface PaginatedTransactions {
  count: number
  next: string | null
  previous: string | null
  results: Transaction[]
}

export interface DashboardResponse {
  totals: {
    total_income: string
    total_expense: string
  }
  by_category: Array<{
    category_name: string | null
    category_type: TransactionType | null
    total: string
  }>
  recent_transactions: Array<{
    id: number
    amount: string
    transaction_type: TransactionType
    category_name: string | null
    description: string
    transaction_date: string
    created_at: string
    payment_method: PaymentMethod
  }>
}

export interface TimeSeriesPoint {
  period: string
  income: string
  expense: string
  net: string
}

export interface TimeSeriesResponse {
  period: string
  preset: string | null
  date_from: string | null
  date_to: string | null
  data: TimeSeriesPoint[]
}

export interface CategoryBreakdownItem {
  category_name: string
  category_type: TransactionType
  total: string
  count: number
}

export interface CategoryBreakdownResponse {
  preset: string | null
  date_from: string | null
  date_to: string | null
  transaction_type: string | null
  data: CategoryBreakdownItem[]
}

export interface TaxReportResponse {
  period: {
    date_from: string
    date_to: string
  }
  totals: {
    total_income: string
    total_expense: string
    net: string
  }
  taxable: {
    income: string
    expense: string
  }
  non_taxable: {
    income: string
    expense: string
  }
  by_payment_method: Array<{
    payment_method: PaymentMethod
    payment_method_display: string
    income: string
    expense: string
    net: string
  }>
  by_activity: Array<{
    activity_code_id: number | null
    activity_name: string | null
    income: string
    expense: string
    net: string
  }>
}

export interface TransactionQueryParams {
  [key: string]: string | number | undefined
  date_from?: string
  date_to?: string
  transaction_type?: string
  category?: string | number
  activity_code?: string | number
  payment_method?: string
  is_business?: string
  is_taxable?: string
  search?: string
  ordering?: string
  limit?: number
  offset?: number
}

export function listCategories(params: { limit?: number; offset?: number } = { limit: 100 }) {
  return apiRequest<PaginatedCategories>(`/finance/categories/${toQueryString(params)}`)
}

export function createCategory(data: { name: string; category_type: TransactionType }) {
  return apiRequest<Category>('/finance/categories/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateCategory(
  id: number,
  data: Partial<{
    name: string
    category_type: TransactionType
  }>,
) {
  return apiRequest<Category>(`/finance/categories/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteCategory(id: number) {
  return apiRequest<void>(`/finance/categories/${id}/`, {
    method: 'DELETE',
  })
}

export function listTransactions(params: TransactionQueryParams) {
  return apiRequest<PaginatedTransactions>(`/finance/transactions/${toQueryString(params)}`)
}

export function createTransaction(data: TransactionDraft) {
  return apiRequest<Transaction>('/finance/transactions/', {
    method: 'POST',
    body: JSON.stringify({
      ...data,
      amount: Number(data.amount),
    }),
  })
}

export function updateTransaction(id: number, data: TransactionDraft) {
  return apiRequest<Transaction>(`/finance/transactions/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify({
      ...data,
      amount: Number(data.amount),
    }),
  })
}

export function deleteTransaction(id: number) {
  return apiRequest<void>(`/finance/transactions/${id}/`, {
    method: 'DELETE',
  })
}

export function getDashboard(params: TransactionQueryParams) {
  return apiRequest<DashboardResponse>(`/finance/dashboard/${toQueryString(params)}`)
}

export function getTimeSeries(
  params: TransactionQueryParams & {
    period?: 'daily' | 'monthly' | 'yearly'
  },
) {
  return apiRequest<TimeSeriesResponse>(`/finance/analytics/time-series/${toQueryString(params)}`)
}

export function getCategoryBreakdown(
  params: TransactionQueryParams & {
    limit?: number
  },
) {
  return apiRequest<CategoryBreakdownResponse>(
    `/finance/analytics/category-breakdown/${toQueryString(params)}`,
  )
}

export function getTaxReport(
  params: TransactionQueryParams & {
    use_org_tax_period?: string
    preset?: string
  },
) {
  return apiRequest<TaxReportResponse>(`/finance/tax-report/${toQueryString(params)}`)
}
