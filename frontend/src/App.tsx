import { useEffect, useState } from 'react'
import { AuthScreen } from './AuthScreen'
import { OnboardingScreen } from './OnboardingScreen'
import { WorkspaceScreen } from './WorkspaceScreen'
import { getCurrentUser, logout, type UserProfile } from './api/auth'
import { clearTokens, getStoredRefreshToken } from './api/client'
import { getOrganizationStatus, type OrganizationStatusResponse } from './api/organization'
import type { AuthMode, NoticeState, NoticeTone } from './lib'

export default function App() {
  const [sessionLoading, setSessionLoading] = useState(true)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [organizationStatus, setOrganizationStatus] = useState<OrganizationStatusResponse | null>(null)
  const [organizationLoading, setOrganizationLoading] = useState(false)
  const [notice, setNotice] = useState<NoticeState | null>(null)

  const pushNotice = (tone: NoticeTone, text: string) => {
    setNotice({ tone, text })
  }

  useEffect(() => {
    if (!notice) {
      return undefined
    }
    const timer = window.setTimeout(() => setNotice(null), 4200)
    return () => window.clearTimeout(timer)
  }, [notice])

  async function loadOrganizationStatus() {
    if (!user) {
      setOrganizationStatus(null)
      return
    }

    setOrganizationLoading(true)
    try {
      const response = await getOrganizationStatus()
      setOrganizationStatus(response)
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось загрузить статус настройки.')
      setOrganizationStatus({
        onboarding_status: 'not_started',
        is_completed: false,
      })
    } finally {
      setOrganizationLoading(false)
    }
  }

  useEffect(() => {
    const restoreSession = async () => {
      const refresh = getStoredRefreshToken()
      if (!refresh) {
        setSessionLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch {
        clearTokens()
      } finally {
        setSessionLoading(false)
      }
    }

    void restoreSession()
  }, [])

  useEffect(() => {
    if (!user) {
      setOrganizationStatus(null)
      return
    }
    void loadOrganizationStatus()
  }, [user])

  const handleLogout = async () => {
    const refresh = getStoredRefreshToken()
    try {
      if (refresh) {
        await logout(refresh)
      }
    } catch {
      // Always clear the local session even if logout API fails.
    } finally {
      clearTokens()
      setUser(null)
      setOrganizationStatus(null)
      pushNotice('info', 'Вы вышли из аккаунта.')
    }
  }

  if (sessionLoading) {
    return <div className="loading-state">Восстанавливаем сессию...</div>
  }

  return (
    <div className="app-shell">
      {notice ? <div className={`notice-banner ${notice.tone}`}>{notice.text}</div> : null}

      {!user ? (
        <AuthScreen
          mode={authMode}
          onModeChange={setAuthMode}
          onAuthenticated={setUser}
          pushNotice={pushNotice}
        />
      ) : organizationLoading || !organizationStatus ? (
        <div className="loading-state">Загружаем настройку организации...</div>
      ) : !organizationStatus.is_completed ? (
        <OnboardingScreen
          user={user}
          onCompleted={async () => {
            await loadOrganizationStatus()
          }}
          pushNotice={pushNotice}
        />
      ) : (
        <WorkspaceScreen
          user={user}
          onLogout={handleLogout}
          onUserUpdated={setUser}
          pushNotice={pushNotice}
        />
      )}
    </div>
  )
}
