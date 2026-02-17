import { useState, FormEvent } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { updateProfile } from '@/api/auth'
import '@/styles/layout.css'
import '@/styles/login.css'

export function ProfilePage() {
  const { user } = useAuth()
  const [form, setForm] = useState({
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
  })
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [submitting, setSubmitting] = useState(false)

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

  return (
    <>
      <h1 className="main-title">Профиль</h1>
      <p className="main-subtitle">Личные данные</p>

      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}
      {success && <p style={{ marginBottom: 16, padding: 12, background: '#e8f5e9', border: '1px solid #a5d6a7', borderRadius: 2 }}>Данные сохранены</p>}

      <div className="main-card" style={{ maxWidth: 480 }}>
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
    </>
  )
}
