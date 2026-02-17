import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { getOrganizationStatus } from '@/api/organization'

interface OnboardingState {
  isCompleted: boolean | null
  isLoading: boolean
  refetch: () => Promise<void>
}

const OnboardingContext = createContext<OnboardingState | null>(null)

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [isCompleted, setIsCompleted] = useState<boolean | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refetch = useCallback(async () => {
    if (!isAuthenticated) {
      setIsCompleted(null)
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    try {
      const s = await getOrganizationStatus()
      setIsCompleted(s.is_completed)
    } catch {
      setIsCompleted(false)
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => {
    refetch()
  }, [refetch])

  return (
    <OnboardingContext.Provider value={{ isCompleted, isLoading, refetch }}>
      {children}
    </OnboardingContext.Provider>
  )
}

export function useOnboarding() {
  const ctx = useContext(OnboardingContext)
  if (!ctx) throw new Error('useOnboarding must be used within OnboardingProvider')
  return ctx
}
