import { useState, useEffect, FormEvent } from 'react'
import type { Transaction, TransactionCreate } from '@/api/finance'
import {
  deleteTransaction,
  updateTransaction,
  listCategories,
  type Category,
} from '@/api/finance'
import { listOrganizationActivities, type OrganizationActivity } from '@/api/organization'
import { Modal } from './Modal'
import '@/styles/login.css'

interface TransactionDetailsModalProps {
  transaction: Transaction | null
  isOpen: boolean
  onClose: () => void
  onDeleted?: () => void
  onUpdated?: () => void
}

export function TransactionDetailsModal({
  transaction,
  isOpen,
  onClose,
  onDeleted,
  onUpdated,
}: TransactionDetailsModalProps) {
  const [deleting, setDeleting] = useState(false)
  const [editing, setEditing] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [orgActivities, setOrgActivities] = useState<OrganizationActivity[]>([])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState<Partial<TransactionCreate>>({})

  useEffect(() => {
    if (transaction && editing) {
      setForm({
        amount: transaction.amount,
        transaction_type: transaction.transaction_type,
        category: transaction.category ?? undefined,
        description: transaction.description || '',
        transaction_date: transaction.transaction_date,
        payment_method: transaction.payment_method,
        is_business: transaction.is_business,
        is_taxable: transaction.is_taxable,
        activity_code: transaction.activity_code ?? undefined,
      })
      listCategories().then(setCategories)
      listOrganizationActivities().then(setOrgActivities)
    }
  }, [transaction, editing])

  if (!transaction) return null
  const t = transaction

  const handleDelete = async () => {
    if (!confirm('Удалить эту транзакцию?')) return
    setDeleting(true)
    try {
      await deleteTransaction(t.id)
      onClose()
      onDeleted?.()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setDeleting(false)
    }
  }

  const handleUpdate = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.amount || !form.transaction_date) return
    if (form.is_business && !form.activity_code) {
      setError('Для бизнес-операции выберите вид деятельности')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await updateTransaction(t.id, {
        ...form,
        amount: String(form.amount),
        category: form.category || null,
        activity_code: form.is_business ? form.activity_code ?? null : null,
        description: form.description || '',
      })
      setEditing(false)
      onUpdated?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const incomeCats = categories.filter((c) => c.category_type === 'income')
  const expenseCats = categories.filter((c) => c.category_type === 'expense')
  const cats = form.transaction_type === 'income' ? incomeCats : expenseCats

  if (editing) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="Редактировать операцию">
        <form onSubmit={handleUpdate} className="login-form">
          {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}
          <div className="form-row">
            <div className="login-field">
              <label>Тип</label>
              <select
                className="select-field"
                value={form.transaction_type ?? ''}
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
                value={form.amount ?? ''}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
                required
              />
            </div>
            <div className="login-field">
              <label>Дата *</label>
              <input
                type="date"
                value={form.transaction_date ?? ''}
                onChange={(e) => setForm((p) => ({ ...p, transaction_date: e.target.value }))}
                required
              />
            </div>
            <div className="login-field">
              <label>Способ оплаты</label>
              <select
                className="select-field"
                value={form.payment_method ?? ''}
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
                onChange={(e) =>
                  setForm((p) => ({ ...p, category: e.target.value ? Number(e.target.value) : undefined }))
                }
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
                value={form.description ?? ''}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                placeholder="Краткое описание"
              />
            </div>
          </div>
          <div className="form-row" style={{ alignItems: 'center', gap: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={form.is_business ?? false}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    is_business: e.target.checked,
                    activity_code: e.target.checked ? p.activity_code : undefined,
                  }))
                }
              />
              Бизнес
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={form.is_taxable ?? false}
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
                  onChange={(e) =>
                    setForm((p) => ({
                      ...p,
                      activity_code: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
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
          <div style={{ display: 'flex', gap: 12, marginTop: 16, justifyContent: 'flex-end' }}>
            <button type="button" className="btn-sm" onClick={() => setEditing(false)}>
              Отмена
            </button>
            <button type="submit" className="login-submit" disabled={submitting}>
              {submitting ? 'Сохранение…' : 'Сохранить'}
            </button>
          </div>
        </form>
      </Modal>
    )
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Детали операции">
      <dl className="transaction-details">
        <div className="detail-row">
          <dt>Дата</dt>
          <dd>{t.transaction_date}</dd>
        </div>
        <div className="detail-row">
          <dt>Тип</dt>
          <dd>{t.transaction_type === 'income' ? 'Доход' : 'Расход'}</dd>
        </div>
        <div className="detail-row">
          <dt>Сумма</dt>
          <dd>{t.amount}</dd>
        </div>
        <div className="detail-row">
          <dt>Способ оплаты</dt>
          <dd>{t.payment_method === 'cash' ? 'Наличный' : 'Безналичный'}</dd>
        </div>
        <div className="detail-row">
          <dt>Категория</dt>
          <dd>{t.category_name || '—'}</dd>
        </div>
        <div className="detail-row">
          <dt>Описание</dt>
          <dd>{t.description || '—'}</dd>
        </div>
        <div className="detail-row">
          <dt>Бизнес</dt>
          <dd>{t.is_business ? 'Да' : 'Нет'}</dd>
        </div>
        <div className="detail-row">
          <dt>Учитывается в налоговой базе</dt>
          <dd>{t.is_taxable ? 'Да' : 'Нет'}</dd>
        </div>
        {t.activity_code_name && (
          <div className="detail-row">
            <dt>Вид деятельности</dt>
            <dd>{t.activity_code_name}</dd>
          </div>
        )}
        {(t.cash_tax_rate != null || t.non_cash_tax_rate != null) && (
          <div className="detail-row">
            <dt>Ставки налога</dt>
            <dd>
              наличные: {t.cash_tax_rate ?? '—'}% / безнал: {t.non_cash_tax_rate ?? '—'}%
            </dd>
          </div>
        )}
        <div className="detail-row">
          <dt>Создано</dt>
          <dd>{new Date(t.created_at).toLocaleString('ru')}</dd>
        </div>
      </dl>
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button type="button" className="btn-sm" onClick={() => setEditing(true)}>
          Изменить
        </button>
        <button
          type="button"
          className="btn-sm danger"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? 'Удаление…' : 'Удалить'}
        </button>
      </div>
    </Modal>
  )
}
