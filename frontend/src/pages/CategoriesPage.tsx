import { useState, useEffect, FormEvent, useMemo } from 'react'
import {
  listCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  type Category,
} from '@/api/finance'
import '@/styles/layout.css'
import '@/styles/login.css'

type SortBy = 'name' | 'type' | ''

export function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', category_type: 'expense' as 'income' | 'expense' })
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({ name: '', category_type: 'expense' as 'income' | 'expense' })
  const [sortBy, setSortBy] = useState<SortBy>('name')

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

  const handleStartEdit = (c: Category) => {
    setEditingId(c.id)
    setEditForm({ name: c.name, category_type: c.category_type })
  }

  const handleSaveEdit = async () => {
    if (!editingId) return
    setError(null)
    setSubmitting(true)
    try {
      await updateCategory(editingId, editForm)
      setEditingId(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const sortedItems = useMemo(() => {
    const arr = [...items]
    if (sortBy === 'name') arr.sort((a, b) => a.name.localeCompare(b.name))
    if (sortBy === 'type') arr.sort((a, b) => a.category_type.localeCompare(b.category_type) || a.name.localeCompare(b.name))
    return arr
  }, [items, sortBy])

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
        <>
          <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>Сортировка:</span>
            <select
              className="select-field"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              style={{ width: 'auto' }}
            >
              <option value="">По умолчанию</option>
              <option value="name">По названию</option>
              <option value="type">По типу</option>
            </select>
          </div>
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
              {sortedItems.map((c) => (
                <tr key={c.id}>
                  <td>
                    {editingId === c.id ? (
                      <input
                        value={editForm.name}
                        onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
                        style={{ width: '100%' }}
                      />
                    ) : (
                      c.name
                    )}
                  </td>
                  <td>
                    {editingId === c.id ? (
                      <select
                        className="select-field"
                        value={editForm.category_type}
                        onChange={(e) => setEditForm((p) => ({ ...p, category_type: e.target.value as 'income' | 'expense' }))}
                      >
                        <option value="income">Доход</option>
                        <option value="expense">Расход</option>
                      </select>
                    ) : (
                      c.category_type_display || (c.category_type === 'income' ? 'Доход' : 'Расход')
                    )}
                  </td>
                  <td>{c.is_system ? 'Да' : ''}</td>
                  <td>
                    {!c.is_system &&
                      (editingId === c.id ? (
                        <>
                          <button type="button" className="btn-sm" onClick={handleSaveEdit} disabled={submitting}>
                            Сохранить
                          </button>
                          <button type="button" className="btn-sm" onClick={() => setEditingId(null)}>
                            Отмена
                          </button>
                        </>
                      ) : (
                        <>
                          <button type="button" className="btn-sm" onClick={() => handleStartEdit(c)}>
                            Изменить
                          </button>
                          <button type="button" className="btn-sm danger" onClick={() => handleDelete(c.id, c.is_system)}>
                            Удалить
                          </button>
                        </>
                      ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  )
}
