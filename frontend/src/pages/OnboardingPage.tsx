import { useState, useEffect, FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useOnboarding } from '@/contexts/OnboardingContext'
import {
  getOrganizationStatus,
  getOrganizationProfile,
  updateOrganizationProfile,
  listOrganizationActivities,
  createOrganizationActivity,
  deleteOrganizationActivity,
  finalizeOnboarding,
  type OrgType,
  type TaxRegime,
  type OrganizationActivity,
} from '@/api/organization'
import { listActivityCodes, type ActivityCode } from '@/api/activities'
import '@/styles/login.css'
import '@/styles/layout.css'

export function OnboardingPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [status, setStatus] = useState<{ onboarding_status: string; is_completed: boolean } | null>(null)
  const [profile, setProfile] = useState<{ org_type: OrgType | null; tax_regime: TaxRegime | null } | null>(null)
  const [activities, setActivities] = useState<OrganizationActivity[]>([])
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [newActivity, setNewActivity] = useState({ activity: 0, cash_tax_rate: '3', non_cash_tax_rate: '0', is_primary: false })
  const { refetch } = useOnboarding()

  useEffect(() => {
    if (!isAuthenticated) return
    Promise.all([
      getOrganizationStatus(),
      getOrganizationProfile(),
      listOrganizationActivities(),
      listActivityCodes(),
    ])
      .then(([s, p, a, ac]) => {
        setStatus(s)
        setProfile(p)
        setActivities(Array.isArray(a) ? a : [])
        setActivityCodes(Array.isArray(ac) ? ac : (ac as unknown as ActivityCode[]))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  const handleOrgType = async (org_type: OrgType) => {
    setError(null)
    setSubmitting(true)
    try {
      const p = await updateOrganizationProfile({ org_type })
      setProfile(p)
      setStatus(await getOrganizationStatus())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleTaxRegime = async (tax_regime: TaxRegime) => {
    setError(null)
    setSubmitting(true)
    try {
      const p = await updateOrganizationProfile({ tax_regime })
      setProfile(p)
      setStatus(await getOrganizationStatus())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddActivity = async (e: FormEvent) => {
    e.preventDefault()
    if (!newActivity.activity) return
    setError(null)
    setSubmitting(true)
    try {
      const created = await createOrganizationActivity({
        activity: newActivity.activity,
        cash_tax_rate: newActivity.cash_tax_rate,
        non_cash_tax_rate: newActivity.non_cash_tax_rate,
        is_primary: newActivity.is_primary,
      })
      setActivities((prev) => [...prev, created])
      setNewActivity({ activity: 0, cash_tax_rate: '3', non_cash_tax_rate: '0', is_primary: false })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemoveActivity = async (id: number) => {
    setError(null)
    try {
      await deleteOrganizationActivity(id)
      setActivities((prev) => prev.filter((a) => a.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  const handleFinalize = async () => {
    setError(null)
    setSubmitting(true)
    try {
      await finalizeOnboarding()
      await refetch()
      setStatus(await getOrganizationStatus())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading || !isAuthenticated) {
    return authLoading ? <div className="login-page"><div className="login-card">Загрузка…</div></div> : <Navigate to="/login" replace />
  }

  if (loading || !status || !profile) {
    return <div className="login-page"><div className="login-card">Загрузка…</div></div>
  }

  if (status.is_completed) {
    return <Navigate to="/" replace />
  }

  const step = status.onboarding_status
  const hasPrimary = activities.some((a) => a.is_primary)

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 560 }}>
        <div className="login-header">
          <h1 className="login-title">Настройка организации</h1>
          <p className="login-subtitle">Шаг {step === 'not_started' ? 1 : step === 'org_type' ? 2 : step === 'tax_regime' ? 3 : 4} из 4</p>
        </div>

        {error && <p className="login-error">{error}</p>}

        {step === 'not_started' && (
          <div className="login-form">
            <p className="login-field label">Тип организации</p>
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                type="button"
                className="login-submit"
                onClick={() => handleOrgType('ie')}
                disabled={submitting}
              >
                ИП
              </button>
              <button
                type="button"
                className="login-submit"
                onClick={() => handleOrgType('llc')}
                disabled={submitting}
              >
                ОсОО
              </button>
            </div>
          </div>
        )}

        {step === 'org_type' && (
          <div className="login-form">
            <p className="login-field label">Налоговый режим</p>
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                type="button"
                className="login-submit"
                onClick={() => handleTaxRegime('single')}
                disabled={submitting}
              >
                Единый налог
              </button>
              <button
                type="button"
                className="login-submit"
                onClick={() => handleTaxRegime('general')}
                disabled={submitting}
              >
                Общий режим
              </button>
            </div>
          </div>
        )}

        {(step === 'tax_regime' || step === 'activities') && (
          <div className="login-form">
            <p className="main-card-title">Виды деятельности</p>
            <p className="main-card-desc" style={{ marginBottom: 16 }}>
              Добавьте хотя бы один вид деятельности. Один должен быть отмечен как основной.
            </p>

            {activities.length > 0 && (
              <table className="data-table" style={{ marginBottom: 20 }}>
                <thead>
                  <tr>
                    <th>Вид деятельности</th>
                    <th>Налог наличные %</th>
                    <th>Налог безнал %</th>
                    <th>Основной</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {activities.map((a) => (
                    <tr key={a.id}>
                      <td>{a.activity_name}</td>
                      <td>{a.cash_tax_rate}</td>
                      <td>{a.non_cash_tax_rate}</td>
                      <td>{a.is_primary ? 'Да' : ''}</td>
                      <td>
                        <button type="button" className="btn-sm danger" onClick={() => handleRemoveActivity(a.id)}>
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <form onSubmit={handleAddActivity}>
              <div className="form-row">
                <div className="login-field" style={{ flex: 2 }}>
                  <label>Вид деятельности (ГКЭД)</label>
                  <select
                    className="select-field"
                    value={newActivity.activity || ''}
                    onChange={(e) => setNewActivity((p) => ({ ...p, activity: Number(e.target.value) }))}
                    required
                  >
                    <option value="">Выберите…</option>
                    {activityCodes.map((ac) => (
                      <option key={ac.id} value={ac.id}>
                        {ac.code} — {ac.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="login-field">
                  <label>Налог наличные %</label>
                  <input
                    type="text"
                    value={newActivity.cash_tax_rate}
                    onChange={(e) => setNewActivity((p) => ({ ...p, cash_tax_rate: e.target.value }))}
                  />
                </div>
                <div className="login-field">
                  <label>Налог безнал %</label>
                  <input
                    type="text"
                    value={newActivity.non_cash_tax_rate}
                    onChange={(e) => setNewActivity((p) => ({ ...p, non_cash_tax_rate: e.target.value }))}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={newActivity.is_primary}
                    onChange={(e) => setNewActivity((p) => ({ ...p, is_primary: e.target.checked }))}
                  />
                  Основной вид
                </label>
                <button type="submit" className="login-submit" disabled={submitting}>
                  Добавить
                </button>
              </div>
            </form>

            {activities.length > 0 && hasPrimary && (
              <button
                type="button"
                className="login-submit"
                onClick={handleFinalize}
                disabled={submitting}
                style={{ width: '100%' }}
              >
                Завершить настройку
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
