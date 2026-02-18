import { useState, useEffect, FormEvent, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { updateProfile } from '@/api/auth'
import {
  listOrganizationActivities,
  createOrganizationActivity,
  updateOrganizationActivity,
  deleteOrganizationActivity,
  type OrganizationActivity,
} from '@/api/organization'
import { listActivityCodes, type ActivityCode } from '@/api/activities'
import { getTelegramLinkToken } from '@/api/telegram'
import '@/styles/layout.css'
import '@/styles/login.css'

export function ProfilePage() {
  const { user } = useAuth()
  const [form, setForm] = useState({
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
  })
  const [activities, setActivities] = useState<OrganizationActivity[]>([])
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([])
  const [newActivity, setNewActivity] = useState({
    activity: 0,
    cash_tax_rate: '3',
    non_cash_tax_rate: '0',
    is_primary: false,
  })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({ cash_tax_rate: '', non_cash_tax_rate: '', is_primary: false })
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [tgLink, setTgLink] = useState<string | null>(null)

  useEffect(() => {
    setForm({ first_name: user?.first_name ?? '', last_name: user?.last_name ?? '' })
  }, [user])

  const [activitySearch, setActivitySearch] = useState('')

  const loadActivityCodes = useCallback((search?: string) => {
    listActivityCodes({ search: search || undefined, limit: 200 }).then((ac) =>
      setActivityCodes(Array.isArray(ac) ? ac : [])
    )
  }, [])

  useEffect(() => {
    listOrganizationActivities().then((a) => setActivities(Array.isArray(a) ? a : []))
  }, [])

  useEffect(() => {
    const t = setTimeout(() => loadActivityCodes(activitySearch || undefined), 300)
    return () => clearTimeout(t)
  }, [activitySearch, loadActivityCodes])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setSubmitting(true)
    try {
      await updateProfile({ first_name: form.first_name, last_name: form.last_name })
      setSuccess(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddActivity = async (e: FormEvent) => {
    e.preventDefault()
    if (!newActivity.activity) return
    setError(null)
    setSubmitting(true)
    try {
      const created = await createOrganizationActivity({
        activity: newActivity.activity,
        cash_tax_rate: newActivity.cash_tax_rate,
        non_cash_tax_rate: newActivity.non_cash_tax_rate,
        is_primary: newActivity.is_primary,
      })
      setActivities((prev) => [...prev, created])
      setNewActivity({ activity: 0, cash_tax_rate: '3', non_cash_tax_rate: '0', is_primary: false })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleStartEdit = (a: OrganizationActivity) => {
    setEditingId(a.id)
    setEditForm({
      cash_tax_rate: a.cash_tax_rate,
      non_cash_tax_rate: a.non_cash_tax_rate,
      is_primary: a.is_primary,
    })
  }

  const handleSaveEdit = async () => {
    if (!editingId) return
    setError(null)
    setSubmitting(true)
    try {
      const updated = await updateOrganizationActivity(editingId, editForm)
      setActivities((prev) => prev.map((a) => (a.id === editingId ? updated : a)))
      setEditingId(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemoveActivity = async (id: number) => {
    if (!confirm('Удалить вид деятельности?')) return
    setError(null)
    try {
      await deleteOrganizationActivity(id)
      setActivities((prev) => prev.filter((a) => a.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  return (
    <>
      <h1 className="main-title">Профиль</h1>
      <p className="main-subtitle">Личные данные и виды деятельности</p>

      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}
      {success && (
        <p style={{ marginBottom: 16, padding: 12, background: '#e8f5e9', border: '1px solid #a5d6a7', borderRadius: 2 }}>
          Данные сохранены
        </p>
      )}

      <div className="main-card" style={{ maxWidth: 480, marginBottom: 24 }}>
        <h2 className="main-card-title">Личные данные</h2>
        <div style={{ marginBottom: 16 }}>
          <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Email</span>
          <p style={{ margin: '4px 0 0 0', fontWeight: 600 }}>{user?.email}</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label>Имя</label>
            <input
              value={form.first_name}
              onChange={(e) => setForm((p) => ({ ...p, first_name: e.target.value }))}
            />
          </div>
          <div className="login-field">
            <label>Фамилия</label>
            <input
              value={form.last_name}
              onChange={(e) => setForm((p) => ({ ...p, last_name: e.target.value }))}
            />
          </div>
          <button type="submit" className="login-submit" disabled={submitting}>
            Сохранить
          </button>
        </form>
      </div>

      <div className="main-card" style={{ marginBottom: 24 }}>
        <h2 className="main-card-title">Telegram</h2>
        <p className="main-card-desc" style={{ marginBottom: 12 }}>
          Привяжите Telegram для добавления операций через бота.
        </p>
        <button
          type="button"
          className="btn-sm"
          onClick={async () => {
            try {
              const { link } = await getTelegramLinkToken()
              setTgLink(link)
            } catch (e) {
              setError(e instanceof Error ? e.message : 'Ошибка')
            }
          }}
        >
          Получить ссылку для привязки
        </button>
        {tgLink && (
          <div style={{ marginTop: 12 }}>
            <a href={tgLink} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-accent)', wordBreak: 'break-all' }}>
              {tgLink}
            </a>
            <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 8 }}>
              Перейдите по ссылке — бот откроется и привяжет аккаунт. Ссылка действительна 10 минут.
            </p>
          </div>
        )}
      </div>

      <div className="main-card">
        <h2 className="main-card-title">Виды деятельности (ГКЭД)</h2>
        <p className="main-card-desc" style={{ marginBottom: 16 }}>
          Добавляйте и редактируйте виды деятельности для операций.
        </p>

        {activities.length > 0 && (
          <table className="data-table" style={{ marginBottom: 20 }}>
            <thead>
              <tr>
                <th>Вид деятельности</th>
                <th>Налог наличные %</th>
                <th>Налог безнал %</th>
                <th>Основной</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => (
                <tr key={a.id}>
                  <td>{a.activity_name}</td>
                  <td>
                    {editingId === a.id ? (
                      <input
                        type="text"
                        value={editForm.cash_tax_rate}
                        onChange={(e) => setEditForm((p) => ({ ...p, cash_tax_rate: e.target.value }))}
                        style={{ width: 60 }}
                      />
                    ) : (
                      a.cash_tax_rate
                    )}
                  </td>
                  <td>
                    {editingId === a.id ? (
                      <input
                        type="text"
                        value={editForm.non_cash_tax_rate}
                        onChange={(e) => setEditForm((p) => ({ ...p, non_cash_tax_rate: e.target.value }))}
                        style={{ width: 60 }}
                      />
                    ) : (
                      a.non_cash_tax_rate
                    )}
                  </td>
                  <td>
                    {editingId === a.id ? (
                      <input
                        type="checkbox"
                        checked={editForm.is_primary}
                        onChange={(e) => setEditForm((p) => ({ ...p, is_primary: e.target.checked }))}
                      />
                    ) : (
                      a.is_primary ? 'Да' : ''
                    )}
                  </td>
                  <td>
                    {editingId === a.id ? (
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
                        <button type="button" className="btn-sm" onClick={() => handleStartEdit(a)}>
                          Изменить
                        </button>
                        {!a.is_primary && (
                          <button
                            type="button"
                            className="btn-sm danger"
                            onClick={() => handleRemoveActivity(a.id)}
                          >
                            Удалить
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <form onSubmit={handleAddActivity} className="login-form">
          <div className="form-row">
            <div className="login-field" style={{ flex: 2 }}>
              <label>Добавить вид деятельности</label>
              <input
                type="text"
                value={activitySearch}
                onChange={(e) => setActivitySearch(e.target.value)}
                placeholder="Поиск по коду или названию…"
                style={{ marginBottom: 8 }}
              />
              <select
                className="select-field"
                value={newActivity.activity || ''}
                onChange={(e) => setNewActivity((p) => ({ ...p, activity: Number(e.target.value) }))}
              >
                <option value="">Выберите…</option>
                {activityCodes.map((ac) => (
                  <option key={ac.id} value={ac.id}>
                    {ac.code} — {ac.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="login-field">
              <label>Налог наличные %</label>
              <input
                type="text"
                value={newActivity.cash_tax_rate}
                onChange={(e) => setNewActivity((p) => ({ ...p, cash_tax_rate: e.target.value }))}
              />
            </div>
            <div className="login-field">
              <label>Налог безнал %</label>
              <input
                type="text"
                value={newActivity.non_cash_tax_rate}
                onChange={(e) => setNewActivity((p) => ({ ...p, non_cash_tax_rate: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={newActivity.is_primary}
                onChange={(e) => setNewActivity((p) => ({ ...p, is_primary: e.target.checked }))}
              />
              Основной вид
            </label>
            <button type="submit" className="login-submit" disabled={submitting}>
              Добавить
            </button>
          </div>
        </form>
      </div>
    </>
  )
}
