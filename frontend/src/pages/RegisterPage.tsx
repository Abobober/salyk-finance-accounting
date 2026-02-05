import { useState, FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { register } from '@/api/auth'
import '@/styles/login.css'

export function RegisterPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (form.password !== form.password2) {
      setError('Пароли не совпадают.')
      return
    }
    setSubmitting(true)
    try {
      await register({
        email: form.email,
        password: form.password,
        password2: form.password2,
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
      })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка регистрации')
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="login-page">
        <div className="login-card">Загрузка…</div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">Регистрация</h1>
          <p className="login-subtitle">
            Создание учётной записи для финансового учёта ИП
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && <p className="login-error">{error}</p>}

          <div className="login-field">
            <label htmlFor="email">Электронная почта *</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="example@mail.kg"
              required
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <label htmlFor="first_name">Имя</label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              value={form.first_name}
              onChange={handleChange}
              placeholder="Иван"
              autoComplete="given-name"
            />
          </div>

          <div className="login-field">
            <label htmlFor="last_name">Фамилия</label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              value={form.last_name}
              onChange={handleChange}
              placeholder="Иванов"
              autoComplete="family-name"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Пароль *</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password2">Подтверждение пароля *</label>
            <input
              id="password2"
              name="password2"
              type="password"
              value={form.password2}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
          </div>

          <button
            type="submit"
            className="login-submit"
            disabled={submitting}
          >
            {submitting ? 'Регистрация…' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="login-footer">
          Уже есть учётная запись? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  )
}
