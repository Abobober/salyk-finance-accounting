import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import '@/styles/layout.css'

export function HomePage() {
  const { isAuthenticated, user, isLoading, logout } = useAuth()

  if (isLoading) {
    return (
      <div className="layout">
        <div className="layout-main" style={{ textAlign: 'center', paddingTop: 60 }}>
          Загрузка…
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="layout-header-inner">
          <Link to="/" className="layout-logo">
            Система финансового учёта
          </Link>
          <div className="layout-user">
            <span className="layout-user-email">{fullName}</span>
            <button type="button" className="layout-logout" onClick={logout}>
              Выйти
            </button>
          </div>
        </div>
      </header>

      <main className="layout-main">
        <h1 className="main-title">Главная</h1>
        <p className="main-subtitle">
          Система финансового учёта для индивидуальных предпринимателей.
        </p>

        <div className="main-grid">
          <div className="main-card">
            <h2 className="main-card-title">Операции</h2>
            <p className="main-card-desc">
              Учёт доходов и расходов, категоризация операций.
            </p>
          </div>
          <div className="main-card">
            <h2 className="main-card-title">Отчёты</h2>
            <p className="main-card-desc">
              Формирование отчётности для налоговых органов.
            </p>
          </div>
          <div className="main-card">
            <h2 className="main-card-title">Справочники</h2>
            <p className="main-card-desc">
              Категории, контрагенты и прочие справочные данные.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
