import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import type { UserProfile } from '@/api/types'
import { getCurrentUser, login as apiLogin, refreshToken, logoutApi } from '@/api/auth'
import { setTokens, clearTokens, getStoredRefresh } from '@/api/client'

interface AuthState {
  user: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const refresh = getStoredRefresh()
    if (!refresh) {
      setIsLoading(false)
      return
    }
    try {
      const tokens = await refreshToken(refresh)
      setTokens(tokens.access, tokens.refresh)
      const u = await getCurrentUser()
      setUser(u)
    } catch {
      clearTokens()
    }
    setIsLoading(false)
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      const { access, refresh } = await apiLogin({ email, password })
      setTokens(access, refresh)
      const u = await getCurrentUser()
      setUser(u)
    },
    []
  )

  const logout = useCallback(async () => {
    const refresh = getStoredRefresh()
    if (refresh) {
      try {
        await logoutApi(refresh)
      } catch {
        // ignore
      }
    }
    clearTokens()
    setUser(null)
  }, [])

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
