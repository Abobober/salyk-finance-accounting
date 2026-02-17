import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useOnboarding } from '@/contexts/OnboardingContext'
import '@/styles/layout.css'

export function MainLayout() {
  const { isAuthenticated, user, isLoading: authLoading, logout } = useAuth()
  const { isCompleted, isLoading: onboardingLoading } = useOnboarding()
  const location = useLocation()

  if (authLoading) {
    return (
      <div className="layout">
        <div className="layout-main" style={{ textAlign: 'center', paddingTop: 60 }}>Загрузка...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (onboardingLoading) {
    return (
      <div className="layout">
        <div className="layout-main" style={{ textAlign: 'center', paddingTop: 60 }}>Загрузка...</div>
      </div>
    )
  }

  if (isCompleted === false) {
    return <Navigate to="/onboarding" replace />
  }

  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email
  const navItems = [
    { path: '/', label: 'Дэшборд' },
    { path: '/profile', label: 'Профиль' },
    { path: '/aichat', label: 'AI-консультант' },
  ]

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="layout-header-inner">
          <Link to="/" className="layout-logo">
            Система финансового учета
          </Link>

          <nav className="layout-nav">
            {navItems.map(({ path, label }) => (
              <Link key={path} to={path} className={location.pathname === path ? 'active' : ''}>
                {label}
              </Link>
            ))}
          </nav>

          <div className="layout-user">
            <span className="layout-user-email">{fullName}</span>
            <button type="button" className="layout-logout" onClick={logout}>
              Выйти
            </button>
          </div>
        </div>
      </header>

      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  )
}
