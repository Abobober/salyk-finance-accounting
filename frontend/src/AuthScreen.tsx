import { useState, type FormEvent } from 'react'
import { getCurrentUser, login, register, type RegisterRequest, type UserProfile } from './api/auth'
import { setTokens } from './api/client'
import type { AuthMode, NoticeTone } from './lib'

export function AuthScreen({
  mode,
  onModeChange,
  onAuthenticated,
  pushNotice,
}: {
  mode: AuthMode
  onModeChange: (mode: AuthMode) => void
  onAuthenticated: (user: UserProfile) => void
  pushNotice: (tone: NoticeTone, text: string) => void
}) {
  const [submitting, setSubmitting] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)

    try {
      if (mode === 'register') {
        const payload: RegisterRequest = {
          email,
          password,
          password2,
          first_name: firstName,
          last_name: lastName,
        }
        await register(payload)
      }

      const tokens = await login({ email, password })
      setTokens(tokens.access, tokens.refresh)
      const user = await getCurrentUser()
      onAuthenticated(user)
      pushNotice('success', mode === 'register' ? 'Регистрация завершена.' : 'Вход выполнен.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось выполнить вход.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-copy">
        <h1>Финансы</h1>
        <p>Войдите или создайте аккаунт.</p>
      </div>

      <div className="auth-card">
        <div className="segment-control">
          <button
            type="button"
            className={mode === 'login' ? 'segment active' : 'segment'}
            onClick={() => onModeChange('login')}
          >
            Вход
          </button>
          <button
            type="button"
            className={mode === 'register' ? 'segment active' : 'segment'}
            onClick={() => onModeChange('register')}
          >
            Регистрация
          </button>
        </div>

        <form className="stack-md" onSubmit={handleSubmit}>
          {mode === 'register' ? (
            <div className="field-grid two">
              <label className="field">
                <span>Имя</span>
                <input value={firstName} onChange={(event) => setFirstName(event.target.value)} />
              </label>
              <label className="field">
                <span>Фамилия</span>
                <input value={lastName} onChange={(event) => setLastName(event.target.value)} />
              </label>
            </div>
          ) : null}

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              required
            />
          </label>

          <label className="field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {mode === 'register' ? (
            <label className="field">
              <span>Повторите пароль</span>
              <input
                type="password"
                value={password2}
                onChange={(event) => setPassword2(event.target.value)}
                required
              />
            </label>
          ) : null}

          <button type="submit" className="primary-button" disabled={submitting}>
            {submitting ? 'Загрузка...' : mode === 'register' ? 'Создать аккаунт' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  )
}
