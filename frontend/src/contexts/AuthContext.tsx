import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import type { UserProfile } from '@/api/types'
import { getCurrentUser, login as apiLogin, refreshToken } from '@/api/auth'

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

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const access = localStorage.getItem(ACCESS_KEY)
    const refresh = localStorage.getItem(REFRESH_KEY)
    if (!access && !refresh) {
      setIsLoading(false)
      return
    }
    try {
      if (access) {
        const u = await getCurrentUser()
        setUser(u)
        setIsLoading(false)
        return
      }
      if (refresh) {
        const { access: newAccess } = await refreshToken(refresh)
        localStorage.setItem(ACCESS_KEY, newAccess)
        const u = await getCurrentUser()
        setUser(u)
      }
    } catch {
      localStorage.removeItem(ACCESS_KEY)
      localStorage.removeItem(REFRESH_KEY)
    }
    setIsLoading(false)
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      const { access, refresh } = await apiLogin({ email, password })
      localStorage.setItem(ACCESS_KEY, access)
      if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
      const u = await getCurrentUser()
      setUser(u)
    },
    []
  )

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
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
