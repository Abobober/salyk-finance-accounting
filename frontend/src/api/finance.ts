import { apiFetch } from './client'

export interface Category {
  id: number
  name: string
  category_type: 'income' | 'expense'
  category_type_display?: string
  is_system: boolean
  created_at: string
}

export interface Transaction {
  id: number
  amount: string
  transaction_type: 'income' | 'expense'
  category: number | null
  category_name: string | null
  description: string
  transaction_date: string
  created_at: string
  payment_method: 'cash' | 'non_cash'
  is_business: boolean
  is_taxable: boolean
  activity_code: number | null
  activity_code_name: string | null
  cash_tax_rate: string | null
  non_cash_tax_rate: string | null
}

export interface TransactionCreate {
  amount: number | string
  transaction_type: 'income' | 'expense'
  category?: number | null
  description?: string
  transaction_date: string
  payment_method: 'cash' | 'non_cash'
  is_business: boolean
  is_taxable: boolean
  activity_code?: number | null
}

/** GET /api/finance/categories/ */
export function listCategories() {
  return apiFetch<Category[] | { results: Category[] }>('/finance/categories/').then((r) =>
    Array.isArray(r) ? r : (r.results ?? [])
  )
}

/** POST /api/finance/categories/ */
export function createCategory(data: { name: string; category_type: 'income' | 'expense' }) {
  return apiFetch<Category>('/finance/categories/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/** PATCH /api/finance/categories/:id/ */
export function updateCategory(id: number, data: Partial<Pick<Category, 'name' | 'category_type'>>) {
  return apiFetch<Category>(`/finance/categories/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/** DELETE /api/finance/categories/:id/ */
export function deleteCategory(id: number) {
  return apiFetch<void>(`/finance/categories/${id}/`, { method: 'DELETE' })
}

export interface TransactionsListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Transaction[]
}

/** GET /api/finance/transactions/ */
export function listTransactions(params?: {
  transaction_type?: 'income' | 'expense'
  category?: number
  date_from?: string
  date_to?: string
  is_business?: boolean
  is_taxable?: boolean
  payment_method?: 'cash' | 'non_cash'
  activity_code?: number
  ordering?: string
  search?: string
  limit?: number
  offset?: number
}) {
  const q = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') q.set(k, String(v))
    })
  }
  const query = q.toString()
  return apiFetch<Transaction[] | TransactionsListResponse>(
    `/finance/transactions/${query ? '?' + query : ''}`
  )
}

/** GET /api/finance/transactions/ — возвращает только массив (для обратной совместимости) */
export function listTransactionsArray(params?: Parameters<typeof listTransactions>[0]) {
  return listTransactions(params).then((r) =>
    Array.isArray(r) ? r : (r.results ?? [])
  )
}

/** POST /api/finance/transactions/ - amount по контракту: number (> 0) */
export function createTransaction(data: TransactionCreate) {
  const payload = {
    ...data,
    amount: typeof data.amount === 'string' ? parseFloat(data.amount) || 0 : data.amount,
    description: (data.description ?? '').slice(0, 100),
  }
  return apiFetch<Transaction>('/finance/transactions/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** PATCH /api/finance/transactions/:id/ */
export function updateTransaction(id: number, data: Partial<TransactionCreate>) {
  return apiFetch<Transaction>(`/finance/transactions/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/** DELETE /api/finance/transactions/:id/ */
export function deleteTransaction(id: number) {
  return apiFetch<void>(`/finance/transactions/${id}/`, { method: 'DELETE' })
}

/** GET /api/finance/dashboard/ - totals, by_category, recent_transactions */
export interface DashboardData {
  totals: { total_income: string; total_expense: string }
  by_category: { category_name: string; category_type: 'income' | 'expense'; total: string }[]
  recent_transactions: {
    id: number
    amount: string
    transaction_type: 'income' | 'expense'
    category_name: string | null
    description: string
    transaction_date: string
    created_at: string
    payment_method: 'cash' | 'non_cash'
  }[]
}

export function getDashboard() {
  return apiFetch<DashboardData>('/finance/dashboard/')
}

/** GET /api/finance/analytics/time-series/ */
export interface TimeSeriesPoint {
  period: string
  income: string
  expense: string
  net: string
}

export interface TimeSeriesResponse {
  period: string
  preset?: string | null
  date_from?: string | null
  date_to?: string | null
  data: TimeSeriesPoint[]
}

export function getTimeSeries(params?: {
  preset?: 'week' | 'month' | 'year' | 'all_time'
  period?: 'daily' | 'monthly' | 'yearly'
  transaction_type?: 'income' | 'expense'
  date_from?: string
  date_to?: string
}) {
  const q = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') q.set(k, String(v))
    })
  }
  const query = q.toString()
  return apiFetch<TimeSeriesResponse>(
    `/finance/analytics/time-series/${query ? '?' + query : ''}`
  )
}

/** GET /api/finance/analytics/category-breakdown/ */
export interface CategoryBreakdownItem {
  category_name: string
  category_type: 'income' | 'expense'
  total: string
  count: number
}

export interface CategoryBreakdownResponse {
  preset?: string | null
  date_from?: string | null
  date_to?: string | null
  transaction_type?: string | null
  data: CategoryBreakdownItem[]
}

export function getCategoryBreakdown(params?: {
  preset?: 'week' | 'month' | 'year' | 'all_time'
  transaction_type?: 'income' | 'expense'
  limit?: number
  date_from?: string
  date_to?: string
}) {
  const q = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') q.set(k, String(v))
    })
  }
  const query = q.toString()
  return apiFetch<CategoryBreakdownResponse>(
    `/finance/analytics/category-breakdown/${query ? '?' + query : ''}`
  )
}
