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
  amount: string
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

/** GET /api/finance/transactions/ */
export function listTransactions(params?: {
  transaction_type?: string
  category?: number
  date_from?: string
  date_to?: string
  is_business?: boolean
  payment_method?: string
}) {
  const q = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') q.set(k, String(v))
    })
  }
  const query = q.toString()
  return apiFetch<Transaction[] | { results: Transaction[] }>(
    `/finance/transactions/${query ? '?' + query : ''}`
  ).then((r) => (Array.isArray(r) ? r : (r.results ?? [])))
}

/** POST /api/finance/transactions/ */
export function createTransaction(data: TransactionCreate) {
  return apiFetch<Transaction>('/finance/transactions/', {
    method: 'POST',
    body: JSON.stringify(data),
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
