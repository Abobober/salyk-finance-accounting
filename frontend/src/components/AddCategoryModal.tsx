import { useState, FormEvent } from 'react'
import { createCategory } from '@/api/finance'
import '@/styles/login.css'

interface AddCategoryModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function AddCategoryModal({ onClose, onSuccess }: AddCategoryModalProps) {
  const [form, setForm] = useState({ name: '', category_type: 'expense' as 'income' | 'expense' })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setError(null)
    setSubmitting(true)
    try {
      await createCategory({ name: form.name.trim(), category_type: form.category_type })
      setForm({ name: '', category_type: 'expense' })
      onSuccess()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="login-form">
      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}
      <div className="form-row">
        <div className="login-field" style={{ flex: 1 }}>
          <label>Название</label>
          <input
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="Например: Продукты"
          />
        </div>
        <div className="login-field">
          <label>Тип</label>
          <select
            className="select-field"
            value={form.category_type}
            onChange={(e) => setForm((p) => ({ ...p, category_type: e.target.value as 'income' | 'expense' }))}
          >
            <option value="income">Доход</option>
            <option value="expense">Расход</option>
          </select>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        <button type="submit" className="login-submit" disabled={submitting}>
          Добавить
        </button>
        <button type="button" className="layout-logout" onClick={onClose}>
          Отмена
        </button>
      </div>
    </form>
  )
}
