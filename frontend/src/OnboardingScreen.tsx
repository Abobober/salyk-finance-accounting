import { useEffect, useState, type FormEvent } from 'react'
import { listActivityCodes, type ActivityCode } from './api/activities'
import type { UserProfile } from './api/auth'
import {
  createOrganizationActivity,
  deleteOrganizationActivity,
  finalizeOnboarding,
  getOrganizationProfile,
  getOrganizationStatus,
  listOrganizationActivities,
  updateOrganizationActivity,
  updateOrganizationProfile,
  type OrganizationActivity,
  type OrganizationProfile,
  type OrganizationStatusResponse,
  type TaxPeriodPreset,
} from './api/organization'
import { ActivityPicker, Section } from './components'
import type { NoticeTone, OrganizationActivityDraft } from './lib'

const ACTIVITY_SEARCH_LIMIT = 50

export function OnboardingScreen({
  user,
  onCompleted,
  pushNotice,
}: {
  user: UserProfile
  onCompleted: () => Promise<void>
  pushNotice: (tone: NoticeTone, text: string) => void
}) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<OrganizationStatusResponse | null>(null)
  const [profile, setProfile] = useState<OrganizationProfile | null>(null)
  const [activities, setActivities] = useState<OrganizationActivity[]>([])
  const [activityOptions, setActivityOptions] = useState<ActivityCode[]>([])
  const [activityOptionsCount, setActivityOptionsCount] = useState(0)
  const [activityOffset, setActivityOffset] = useState(0)
  const [activitySearch, setActivitySearch] = useState('')
  const [activitySearchLoading, setActivitySearchLoading] = useState(false)
  const [selectedActivityOption, setSelectedActivityOption] = useState<ActivityCode | null>(null)
  const [draft, setDraft] = useState<OrganizationActivityDraft>({
    activity: 0,
    cash_tax_rate: '3',
    non_cash_tax_rate: '0',
    is_primary: false,
  })

  async function loadOnboarding() {
    setLoading(true)
    try {
      const [statusResponse, profileResponse, activityResponse, activityCodesResponse] = await Promise.all([
        getOrganizationStatus(),
        getOrganizationProfile(),
        listOrganizationActivities({ limit: 100 }),
        listActivityCodes({ limit: ACTIVITY_SEARCH_LIMIT, offset: 0 }),
      ])
      setStatus(statusResponse)
      setProfile(profileResponse)
      setActivities(activityResponse.results)
      setActivityOptions(activityCodesResponse.results)
      setActivityOptionsCount(activityCodesResponse.count)
      setActivityOffset(0)
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось загрузить первичную настройку.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadOnboarding()
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      setActivitySearchLoading(true)
      try {
        const response = await listActivityCodes({
          search: activitySearch || undefined,
          limit: ACTIVITY_SEARCH_LIMIT,
          offset: 0,
        })
        setActivityOptions(response.results)
        setActivityOptionsCount(response.count)
        setActivityOffset(0)
      } catch {
        // Quiet while typing.
      } finally {
        setActivitySearchLoading(false)
      }
    }, 250)

    return () => window.clearTimeout(timer)
  }, [activitySearch])

  const saveProfile = async (
    data: Parameters<typeof updateOrganizationProfile>[0],
    successMessage?: string,
  ) => {
    setSaving(true)
    try {
      const response = await updateOrganizationProfile(data)
      setProfile((current) => (current ? { ...current, ...response } : response))
      setStatus(await getOrganizationStatus())
      if (successMessage) {
        pushNotice('success', successMessage)
      }
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось сохранить настройки.')
    } finally {
      setSaving(false)
    }
  }

  const loadMoreActivities = async () => {
    const nextOffset = activityOffset + ACTIVITY_SEARCH_LIMIT
    setActivitySearchLoading(true)
    try {
      const response = await listActivityCodes({
        search: activitySearch || undefined,
        limit: ACTIVITY_SEARCH_LIMIT,
        offset: nextOffset,
      })
      setActivityOptions((current) => [...current, ...response.results])
      setActivityOptionsCount(response.count)
      setActivityOffset(nextOffset)
    } catch {
      pushNotice('error', 'Не удалось загрузить дополнительные варианты видов деятельности.')
    } finally {
      setActivitySearchLoading(false)
    }
  }

  const addActivity = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft.activity) {
      pushNotice('error', 'Выберите вид деятельности.')
      return
    }

    setSaving(true)
    try {
      const response = await createOrganizationActivity({
        ...draft,
        is_primary: activities.length === 0,
      })
      setActivities((current) => [...current, response])
      setDraft({
        activity: 0,
        cash_tax_rate: '3',
        non_cash_tax_rate: '0',
        is_primary: false,
      })
      setSelectedActivityOption(null)
      setActivitySearch('')
      setStatus(await getOrganizationStatus())
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось добавить вид деятельности.')
    } finally {
      setSaving(false)
    }
  }

  const finishOnboarding = async () => {
    if (!profile) {
      return
    }

    const missingRequiredFields: string[] = []
    if (!profile.org_type) {
      missingRequiredFields.push('форма бизнеса')
    }
    if (!profile.tax_regime) {
      missingRequiredFields.push('налоговый режим')
    }
    if (!activityReady) {
      missingRequiredFields.push('основной вид деятельности')
    }
    if (!profile.inn?.trim()) {
      missingRequiredFields.push('ИНН')
    }
    if (!profile.taxpayer_name?.trim()) {
      missingRequiredFields.push('ФИО/наименование налогоплательщика')
    }
    if (!profile.tax_authority_code?.trim()) {
      missingRequiredFields.push('код налогового органа')
    }
    if (!profile.tax_authority_name?.trim()) {
      missingRequiredFields.push('наименование налогового органа')
    }
    if (!profile.contact_phone?.trim()) {
      missingRequiredFields.push('контактный телефон')
    }
    if (missingRequiredFields.length) {
      pushNotice('error', `Заполните перед завершением: ${missingRequiredFields.join(', ')}.`)
      return
    }

    setSaving(true)
    try {
      const updatedProfile = await updateOrganizationProfile({
        inn: profile.inn ?? '',
        contact_phone: profile.contact_phone ?? '',
        taxpayer_name: profile.taxpayer_name ?? '',
        tax_authority_code: profile.tax_authority_code ?? '',
        tax_authority_name: profile.tax_authority_name ?? '',
      })
      setProfile((current) => (current ? { ...current, ...updatedProfile } : updatedProfile))
      await finalizeOnboarding()
      await onCompleted()
      pushNotice('success', 'Настройка завершена.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось завершить настройку.')
    } finally {
      setSaving(false)
    }
  }

  if (loading || !profile || !status) {
    return <div className="loading-state">Загрузка...</div>
  }

  const activityReady = activities.some((activity) => activity.is_primary)
  const stiMissingFields = [
    !profile.inn?.trim() ? 'ИНН' : null,
    !profile.taxpayer_name?.trim() ? 'ФИО/наименование налогоплательщика' : null,
    !profile.tax_authority_code?.trim() ? 'код налогового органа' : null,
    !profile.tax_authority_name?.trim() ? 'наименование налогового органа' : null,
    !profile.contact_phone?.trim() ? 'контактный телефон' : null,
  ].filter(Boolean) as string[]

  return (
    <div className="onboarding-shell">
      <header className="onboarding-header">
        <div>
          <h1>Первичная настройка</h1>
          <p>{user.first_name || user.email}</p>
        </div>

        <div className="status-pill">
          <span>Статус</span>
          <strong>{status.onboarding_status.replace('_', ' ')}</strong>
        </div>
      </header>

      <div className="onboarding-grid">
        <Section title="Форма бизнеса" eyebrow="Шаг 1">
          <div className="choice-grid">
            <button
              type="button"
              className={profile.org_type === 'ie' ? 'choice-card active' : 'choice-card'}
              onClick={() => void saveProfile({ org_type: 'ie' })}
              disabled={saving}
            >
              <strong>ИП</strong>
              <span>Для частной практики и малого бизнеса.</span>
            </button>
            <button
              type="button"
              className={profile.org_type === 'llc' ? 'choice-card active' : 'choice-card'}
              onClick={() => void saveProfile({ org_type: 'llc' })}
              disabled={saving}
            >
              <strong>ОсОО</strong>
              <span>Для компании с более формальной структурой.</span>
            </button>
          </div>
        </Section>

        <Section title="Налоговый режим" eyebrow="Шаг 2">
          <div className="choice-grid">
            <button
              type="button"
              className={profile.tax_regime === 'single' ? 'choice-card active' : 'choice-card'}
              onClick={() => void saveProfile({ tax_regime: 'single' })}
              disabled={saving}
            >
              <strong>Единый налог</strong>
              <span>Упрощенный режим.</span>
            </button>
            <button
              type="button"
              className={profile.tax_regime === 'general' ? 'choice-card active' : 'choice-card'}
              onClick={() => void saveProfile({ tax_regime: 'general' })}
              disabled={saving}
            >
              <strong>Общий режим</strong>
              <span>Полный учет и отчетность.</span>
            </button>
          </div>
        </Section>

        <Section title="Налоговый период" eyebrow="Шаг 3">
          <div className="stack-sm">
            <div className="choice-grid">
              <button
                type="button"
                className={profile.tax_period_type === 'preset' ? 'choice-card active' : 'choice-card'}
                onClick={() =>
                  void saveProfile({
                    tax_period_type: 'preset',
                    tax_period_preset: profile.tax_period_preset ?? 'monthly',
                    tax_period_custom_day: profile.tax_period_custom_day ?? null,
                  })
                }
                disabled={saving}
              >
                <strong>Готовый период</strong>
                <span>Месяц, квартал или год.</span>
              </button>
              <button
                type="button"
                className={profile.tax_period_type === 'custom' ? 'choice-card active' : 'choice-card'}
                onClick={() =>
                  void saveProfile({
                    tax_period_type: 'custom',
                    tax_period_preset: null,
                    tax_period_custom_day: profile.tax_period_custom_day ?? 1,
                  })
                }
                disabled={saving}
              >
                <strong>Свой день</strong>
                <span>Закрытие периода по вашему дню месяца.</span>
              </button>
            </div>

            {profile.tax_period_type === 'preset' ? (
              <div className="stack-sm">
                <div className="field-grid three">
                  {(['monthly', 'quarterly', 'yearly'] as TaxPeriodPreset[]).map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      className={profile.tax_period_preset === preset ? 'choice-card active compact' : 'choice-card compact'}
                      onClick={() => void saveProfile({ tax_period_preset: preset })}
                      disabled={saving}
                    >
                      <strong>
                        {preset === 'monthly'
                          ? 'Ежемесячно'
                          : preset === 'quarterly'
                            ? 'Ежеквартально'
                            : 'Ежегодно'}
                      </strong>
                    </button>
                  ))}
                </div>
                <div className="inline-form">
                  <label className="field">
                    <span>День начала периода</span>
                    <input
                      type="number"
                      min="1"
                      max="31"
                      placeholder="1"
                      value={profile.tax_period_custom_day ?? ''}
                      onChange={(event) =>
                        setProfile({
                          ...profile,
                          tax_period_custom_day: event.target.value ? Number(event.target.value) : null,
                        })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      void saveProfile({
                        tax_period_preset: profile.tax_period_preset ?? 'monthly',
                        tax_period_custom_day: profile.tax_period_custom_day ?? null,
                      })
                    }
                    disabled={saving}
                  >
                    Сохранить
                  </button>
                </div>
              </div>
            ) : null}

            {profile.tax_period_type === 'custom' ? (
              <div className="inline-form">
                <label className="field">
                  <span>День месяца</span>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={profile.tax_period_custom_day ?? ''}
                    onChange={(event) =>
                      setProfile({
                        ...profile,
                        tax_period_custom_day: event.target.value ? Number(event.target.value) : null,
                      })
                    }
                  />
                </label>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    void saveProfile({
                      tax_period_custom_day: profile.tax_period_custom_day ?? 1,
                    })
                  }
                  disabled={saving}
                >
                  Сохранить
                </button>
              </div>
            ) : null}
          </div>
        </Section>

        <Section title="Виды деятельности" eyebrow="Шаг 4">
          <div className="stack-md">
            <p className="muted">Добавьте минимум один вид деятельности и отметьте основной.</p>

            {activities.length ? (
              <div className="mini-table">
                {activities.map((activity) => (
                  <div key={activity.id} className="mini-table-row">
                    <div>
                      <strong>{activity.activity_name}</strong>
                      <p>
                        Наличные {activity.cash_tax_rate}% · Безнал {activity.non_cash_tax_rate}%
                      </p>
                    </div>
                    <div className="mini-table-actions">
                      {activity.is_primary ? <span className="tag">Основной</span> : null}
                      {!activity.is_primary ? (
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={async () => {
                            try {
                              const updated = await updateOrganizationActivity(activity.id, {
                                is_primary: true,
                              })
                              setActivities((current) =>
                                current.map((item) =>
                                  item.id === activity.id ? updated : { ...item, is_primary: false },
                                ),
                              )
                            } catch (error) {
                              pushNotice(
                                'error',
                                error instanceof Error
                                  ? error.message
                                  : 'Не удалось назначить основной вид деятельности.',
                              )
                            }
                          }}
                        >
                          Сделать основным
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className="ghost-button danger"
                        onClick={async () => {
                          try {
                            await deleteOrganizationActivity(activity.id)
                            setActivities((current) => current.filter((item) => item.id !== activity.id))
                          } catch (error) {
                            pushNotice(
                              'error',
                              error instanceof Error ? error.message : 'Не удалось удалить вид деятельности.',
                            )
                          }
                        }}
                      >
                        Удалить
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}

            <form className="stack-sm" onSubmit={addActivity}>
              <ActivityPicker
                searchValue={activitySearch}
                onSearchChange={(value) => {
                  setActivitySearch(value)
                  setSelectedActivityOption(null)
                  setDraft((current) => ({ ...current, activity: 0 }))
                }}
                options={activityOptions}
                selectedActivity={selectedActivityOption}
                onSelect={(activity) => {
                  setSelectedActivityOption(activity)
                  setDraft((current) => ({ ...current, activity: activity.id }))
                }}
                onClear={() => {
                  setActivitySearch('')
                  setSelectedActivityOption(null)
                  setDraft((current) => ({ ...current, activity: 0 }))
                }}
                totalCount={activityOptionsCount}
                loading={activitySearchLoading}
                disabled={saving}
              />
              {activityOptions.length < activityOptionsCount ? (
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => void loadMoreActivities()}
                  disabled={saving || activitySearchLoading}
                >
                  {activitySearchLoading
                    ? 'Загружаем...'
                    : `Показать еще (${activityOptionsCount - activityOptions.length})`}
                </button>
              ) : null}

              <div className="field-grid two">
                <label className="field">
                  <span>Налог наличными</span>
                  <input
                    value={draft.cash_tax_rate}
                    onChange={(event) => setDraft({ ...draft, cash_tax_rate: event.target.value })}
                    required
                  />
                </label>

                <label className="field">
                  <span>Налог безналом</span>
                  <input
                    value={draft.non_cash_tax_rate}
                    onChange={(event) => setDraft({ ...draft, non_cash_tax_rate: event.target.value })}
                    required
                  />
                </label>
              </div>

              {!activities.length ? <p className="muted">Первый добавленный вид станет основным.</p> : null}

              <button type="submit" className="secondary-button" disabled={saving}>
                Добавить
              </button>
            </form>
            <div className="onboarding-subsection stack-sm">
              <div>
                <p className="panel-eyebrow">Шаг 5</p>
                <h3>Реквизиты для STI-091</h3>
              </div>
              <p className="muted">
                Эти данные обязательны для автоматического заполнения отчета по единому налогу.
              </p>
              {stiMissingFields.length ? (
                <p className="muted">Осталось заполнить: {stiMissingFields.join(', ')}.</p>
              ) : (
                <p className="muted">Все обязательные реквизиты заполнены.</p>
              )}
              <div className="field-grid two">
                <label className="field">
                  <span>ИНН</span>
                  <input
                    value={profile.inn ?? ''}
                    onChange={(event) => setProfile({ ...profile, inn: event.target.value })}
                    required
                  />
                </label>
                <label className="field">
                  <span>Контактный телефон</span>
                  <input
                    value={profile.contact_phone ?? ''}
                    onChange={(event) => setProfile({ ...profile, contact_phone: event.target.value })}
                    required
                  />
                </label>
                <label className="field">
                  <span>ФИО / Наименование налогоплательщика</span>
                  <input
                    value={profile.taxpayer_name ?? ''}
                    onChange={(event) => setProfile({ ...profile, taxpayer_name: event.target.value })}
                    required
                  />
                </label>
                <label className="field">
                  <span>Код налогового органа</span>
                  <input
                    value={profile.tax_authority_code ?? ''}
                    onChange={(event) => setProfile({ ...profile, tax_authority_code: event.target.value })}
                    required
                  />
                </label>
              </div>
              <label className="field">
                <span>Наименование налогового органа</span>
                <input
                  value={profile.tax_authority_name ?? ''}
                  onChange={(event) => setProfile({ ...profile, tax_authority_name: event.target.value })}
                  required
                />
              </label>
            </div>

            <button
              type="button"
              className="primary-button"
              disabled={saving}
              onClick={() => void finishOnboarding()}
            >
              Завершить
            </button>
          </div>
        </Section>
      </div>
    </div>
  )
}
