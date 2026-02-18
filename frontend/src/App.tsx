import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { OnboardingProvider } from '@/contexts/OnboardingContext'
import { MainLayout } from '@/components/MainLayout'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { OnboardingPage } from '@/pages/OnboardingPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { AiChatPage } from '@/pages/AiChatPage'
import { TaxReportsPage } from '@/pages/TaxReportsPage'
import { CategoriesPage } from '@/pages/CategoriesPage'

function App() {
  return (
    <AuthProvider>
      <OnboardingProvider>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route element={<MainLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/tax-reports" element={<TaxReportsPage />} />
              <Route path="/categories" element={<CategoriesPage />} />
              <Route path="/aichat" element={<AiChatPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </OnboardingProvider>
    </AuthProvider>
  )
}

export default App
