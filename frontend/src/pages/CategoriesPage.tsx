import { useState, useEffect, FormEvent } from 'react'
import { listCategories, createCategory, updateCategory, deleteCategory, type Category } from '@/api/finance'
import '@/styles/layout.css'
import '@/styles/login.css'

export function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', category_type: 'expense' as 'income' | 'expense' })
  const [submitting, setSubmitting] = useState(false)

  const load = () => {
    setLoading(true)
    listCategories()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setError(null)
    setSubmitting(true)
    try {
      await createCategory({ name: form.name.trim(), category_type: form.category_type })
      setForm({ name: '', category_type: 'expense' })
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number, isSystem: boolean) => {
    if (isSystem) return
    if (!confirm('Удалить категорию?')) return
    setError(null)
    try {
      await deleteCategory(id)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  return (
    <>
      <h1 className="main-title">Категории</h1>
      <p className="main-subtitle">Категории доходов и расходов для операций</p>

      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}

      <div className="main-card" style={{ marginBottom: 24 }}>
        <h2 className="main-card-title">Добавить категорию</h2>
        <form onSubmit={handleSubmit} className="login-form" style={{ maxWidth: 400 }}>
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
          <button type="submit" className="login-submit" disabled={submitting}>
            Добавить
          </button>
        </form>
      </div>

      {loading ? (
        <p>Загрузка…</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип</th>
              <th>Системная</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.category_type_display || (c.category_type === 'income' ? 'Доход' : 'Расход')}</td>
                <td>{c.is_system ? 'Да' : ''}</td>
                <td>
                  {!c.is_system && (
                    <button type="button" className="btn-sm danger" onClick={() => handleDelete(c.id, c.is_system)}>
                      Удалить
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
