import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { OnboardingProvider } from '@/contexts/OnboardingContext'
import { MainLayout } from '@/components/MainLayout'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { OnboardingPage } from '@/pages/OnboardingPage'
import { HomePage } from '@/pages/HomePage'
import { CategoriesPage } from '@/pages/CategoriesPage'
import { TransactionsPage } from '@/pages/TransactionsPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { AiChatPage } from '@/pages/AiChatPage'
import { TaxReportsPage } from '@/pages/TaxReportsPage'

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
              <Route path="/" element={<HomePage />} />
              <Route path="/categories" element={<CategoriesPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/reports" element={<TaxReportsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
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
