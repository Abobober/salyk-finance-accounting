import { useState, useEffect, FormEvent } from 'react'
import {
  listTransactions,
  createTransaction,
  listCategories,
  type Transaction,
  type Category,
  type TransactionCreate,
} from '@/api/finance'
import { listActivityCodes, type ActivityCode } from '@/api/activities'
import { listOrganizationActivities, type OrganizationActivity } from '@/api/organization'
import '@/styles/layout.css'
import '@/styles/login.css'

export function TransactionsPage() {
  const [items, setItems] = useState<Transaction[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([])
  const [orgActivities, setOrgActivities] = useState<OrganizationActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [filters, setFilters] = useState({ date_from: '', date_to: '', transaction_type: '', category: '' })
  const [form, setForm] = useState<TransactionCreate>({
    amount: '',
    transaction_type: 'expense',
    category: undefined,
    description: '',
    transaction_date: new Date().toISOString().slice(0, 10),
    payment_method: 'cash',
    is_business: true,
    is_taxable: true,
    activity_code: undefined,
  })

  const load = () => {
    setLoading(true)
    const params: Record<string, string> = {}
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    if (filters.transaction_type) params.transaction_type = filters.transaction_type
    if (filters.category) params.category = filters.category
    listTransactions(params)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [filters.date_from, filters.date_to, filters.transaction_type, filters.category])

  useEffect(() => {
    listCategories().then(setCategories)
    listActivityCodes().then(setActivityCodes)
    listOrganizationActivities().then(setOrgActivities)
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.amount || !form.transaction_date) return
    if (form.is_business && !form.activity_code) {
      setError('Для бизнес-операции выберите вид деятельности')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await createTransaction({
        ...form,
        amount: String(form.amount),
        category: form.category || null,
        activity_code: form.is_business ? form.activity_code ?? null : null,
        description: form.description || '',
      })
      setForm({
        amount: '',
        transaction_type: 'expense',
        category: undefined,
        description: '',
        transaction_date: new Date().toISOString().slice(0, 10),
        payment_method: 'cash',
        is_business: true,
        is_taxable: true,
        activity_code: undefined,
      })
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const incomeCats = categories.filter((c) => c.category_type === 'income')
  const expenseCats = categories.filter((c) => c.category_type === 'expense')
  const cats = form.transaction_type === 'income' ? incomeCats : expenseCats

  return (
    <>
      <h1 className="main-title">Операции</h1>
      <p className="main-subtitle">Учёт доходов и расходов</p>

      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}

      <div className="main-card" style={{ marginBottom: 24 }}>
        <h2 className="main-card-title">Добавить операцию</h2>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-row">
            <div className="login-field">
              <label>Тип</label>
              <select
                className="select-field"
                value={form.transaction_type}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    transaction_type: e.target.value as 'income' | 'expense',
                    category: undefined,
                  }))
                }
              >
                <option value="income">Доход</option>
                <option value="expense">Расход</option>
              </select>
            </div>
            <div className="login-field">
              <label>Сумма *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={form.amount}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
                required
              />
            </div>
            <div className="login-field">
              <label>Дата *</label>
              <input
                type="date"
                value={form.transaction_date}
                onChange={(e) => setForm((p) => ({ ...p, transaction_date: e.target.value }))}
                required
              />
            </div>
            <div className="login-field">
              <label>Способ оплаты</label>
              <select
                className="select-field"
                value={form.payment_method}
                onChange={(e) => setForm((p) => ({ ...p, payment_method: e.target.value as 'cash' | 'non_cash' }))}
              >
                <option value="cash">Наличный</option>
                <option value="non_cash">Безналичный</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="login-field">
              <label>Категория</label>
              <select
                className="select-field"
                value={form.category ?? ''}
                onChange={(e) => setForm((p) => ({ ...p, category: e.target.value ? Number(e.target.value) : undefined }))}
              >
                <option value="">—</option>
                {cats.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="login-field" style={{ flex: 2 }}>
              <label>Описание</label>
              <input
                value={form.description || ''}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                placeholder="Краткое описание"
              />
            </div>
          </div>
          <div className="form-row" style={{ alignItems: 'center', gap: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={form.is_business}
                onChange={(e) => setForm((p) => ({ ...p, is_business: e.target.checked, activity_code: e.target.checked ? p.activity_code : undefined }))}
              />
              Бизнес
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={form.is_taxable}
                onChange={(e) => setForm((p) => ({ ...p, is_taxable: e.target.checked }))}
              />
              Учитывается в налоговой базе
            </label>
            {form.is_business && orgActivities.length > 0 && (
              <div className="login-field">
                <label>Вид деятельности *</label>
                <select
                  className="select-field"
                  value={form.activity_code ?? ''}
                  onChange={(e) => setForm((p) => ({ ...p, activity_code: e.target.value ? Number(e.target.value) : undefined }))}
                  required={form.is_business}
                >
                  <option value="">Выберите…</option>
                  {orgActivities.map((a) => (
                    <option key={a.id} value={a.activity}>
                      {a.activity_name} {a.is_primary ? '(осн.)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <button type="submit" className="login-submit" disabled={submitting}>
            Добавить
          </button>
        </form>
      </div>

      <div className="main-card" style={{ marginBottom: 16 }}>
        <h2 className="main-card-title">Фильтры</h2>
        <div className="form-row">
          <div className="login-field">
            <label>Дата с</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))}
            />
          </div>
          <div className="login-field">
            <label>Дата по</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))}
            />
          </div>
          <div className="login-field">
            <label>Тип</label>
            <select
              className="select-field"
              value={filters.transaction_type}
              onChange={(e) => setFilters((p) => ({ ...p, transaction_type: e.target.value }))}
            >
              <option value="">Все</option>
              <option value="income">Доход</option>
              <option value="expense">Расход</option>
            </select>
          </div>
          <div className="login-field">
            <label>Категория</label>
            <select
              className="select-field"
              value={filters.category}
              onChange={(e) => setFilters((p) => ({ ...p, category: e.target.value }))}
            >
              <option value="">Все</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <p>Загрузка…</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Тип</th>
              <th>Сумма</th>
              <th>Категория</th>
              <th>Способ</th>
              <th>Описание</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td>{t.transaction_date}</td>
                <td>{t.transaction_type === 'income' ? 'Доход' : 'Расход'}</td>
                <td>{t.amount}</td>
                <td>{t.category_name || '—'}</td>
                <td>{t.payment_method === 'cash' ? 'Наличный' : 'Безнал'}</td>
                <td>{t.description || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
