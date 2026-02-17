import { useState, FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import '@/styles/login.css'

export function LoginPage() {
  const location = useLocation()
  const fromRegister = (location.state as { registered?: boolean })?.registered
  const { login, isAuthenticated, isLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка авторизации')
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
          <h1 className="login-title">Вход в систему</h1>
          <p className="login-subtitle">
            Финансовый учёт для индивидуальных предпринимателей
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {fromRegister && (
            <p style={{ margin: 0, padding: '8px 12px', background: '#e8f5e9', border: '1px solid #a5d6a7', borderRadius: 2, fontSize: 13, color: '#2e7d32' }}>
              Регистрация успешна. Войдите в систему.
            </p>
          )}
          {error && <p className="login-error">{error}</p>}

          <div className="login-field">
            <label htmlFor="email">Электронная почта</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@mail.kg"
              required
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="login-submit"
            disabled={submitting}
          >
            {submitting ? 'Вход…' : 'Войти'}
          </button>
        </form>

        <p className="login-footer">
          Нет учётной записи? <Link to="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  )
}
