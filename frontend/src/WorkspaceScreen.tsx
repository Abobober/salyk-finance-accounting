import { useEffect, useRef, useState, type FormEvent } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { consultAi } from './api/aichat'
import { updateProfile, type UserProfile } from './api/auth'
import { listActivityCodes, type ActivityCode } from './api/activities'
import {
  createCategory,
  createTransaction,
  deleteCategory,
  deleteTransaction,
  getCategoryBreakdown,
  getDashboard,
  getTaxReport,
  getTimeSeries,
  listCategories,
  listTransactions,
  updateCategory,
  updateTransaction,
  type Category,
  type CategoryBreakdownItem,
  type DashboardResponse,
  type PaginatedTransactions,
  type TaxReportResponse,
  type TimeSeriesPoint,
  type Transaction,
  type TransactionDraft,
  type TransactionType,
} from './api/finance'
import {
  createOrganizationActivity,
  deleteOrganizationActivity,
  getOrganizationProfile,
  getTaxPeriod,
  listOrganizationActivities,
  updateOrganizationActivity,
  updateOrganizationProfile,
  type OrganizationActivity,
  type OrganizationProfile,
  type TaxPeriodPreset,
  type TaxPeriodResponse,
  type TaxPeriodType,
} from './api/organization'
import { generateUnifiedTaxReport, type UnifiedTaxReportResponse } from './api/taxReports'
import { getTelegramLinkToken } from './api/telegram'
import { ActivityPicker, ChatMessageBody, Dialog, Section, TransactionForm } from './components'
import {
  buildAnalyticsParams,
  buildDashboardParams,
  buildReportParams,
  createAiSessionId,
  formatAiAssistantReply,
  formatCurrency,
  formatDateInput,
  formatDateLabel,
  getPresetRange,
  makeDefaultTransactionDraft,
  PIE_COLORS,
  TAX_TRANSACTION_PAGE_SIZE,
  TRANSACTION_PAGE_SIZE,
  type ChartGranularity,
  type ChartMode,
  type DashboardFilters,
  type NoticeTone,
  type OrganizationActivityDraft,
  type ReportControls,
} from './lib'

const ACTIVITY_SEARCH_LIMIT = 24

export function WorkspaceScreen({
  user,
  onLogout,
  onUserUpdated,
  pushNotice,
}: {
  user: UserProfile
  onLogout: () => Promise<void>
  onUserUpdated: (user: UserProfile) => void
  pushNotice: (tone: NoticeTone, text: string) => void
}) {
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions' | 'tax' | 'profile' | 'assistant'>('overview')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [showComposerDialog, setShowComposerDialog] = useState(false)
  const [loading, setLoading] = useState(true)
  const [staticLoading, setStaticLoading] = useState(true)
  const [chartMode, setChartMode] = useState<ChartMode>('area')
  const [chartGranularity, setChartGranularity] = useState<ChartGranularity>('monthly')
  const [filters, setFilters] = useState<DashboardFilters>({
    preset: 'month',
    date_from: '',
    date_to: '',
    transaction_type: '',
    category: '',
    activity_code: '',
    payment_method: '',
    is_business: '',
    is_taxable: '',
    search: '',
    ordering: '-transaction_date',
  })
  const [transactionOffset, setTransactionOffset] = useState(0)
  const [reportOffset, setReportOffset] = useState(0)
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([])
  const [breakdown, setBreakdown] = useState<CategoryBreakdownItem[]>([])
  const [transactionPage, setTransactionPage] = useState<PaginatedTransactions | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [activities, setActivities] = useState<OrganizationActivity[]>([])
  const [profile, setProfile] = useState<UserProfile>(user)
  const [organizationProfile, setOrganizationProfile] = useState<OrganizationProfile | null>(null)
  const [taxPeriod, setTaxPeriod] = useState<TaxPeriodResponse | null>(null)
  const [activitySearch, setActivitySearch] = useState('')
  const [activityOptions, setActivityOptions] = useState<ActivityCode[]>([])
  const [activityOptionsCount, setActivityOptionsCount] = useState(0)
  const [activitySearchLoading, setActivitySearchLoading] = useState(false)
  const [selectedActivityOption, setSelectedActivityOption] = useState<ActivityCode | null>(null)
  const [activityDraft, setActivityDraft] = useState<OrganizationActivityDraft>({
    activity: 0,
    cash_tax_rate: '3',
    non_cash_tax_rate: '0',
    is_primary: false,
  })
  const [newCategoryName, setNewCategoryName] = useState('')
  const [newCategoryType, setNewCategoryType] = useState<TransactionType>('expense')
  const [categoryEditingId, setCategoryEditingId] = useState<number | null>(null)
  const [categoryEditName, setCategoryEditName] = useState('')
  const [composerDraft, setComposerDraft] = useState<TransactionDraft>(makeDefaultTransactionDraft())
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const [transactionSubmitting, setTransactionSubmitting] = useState(false)
  const [taxReport, setTaxReport] = useState<TaxReportResponse | null>(null)
  const [taxTransactions, setTaxTransactions] = useState<PaginatedTransactions | null>(null)
  const [taxLoading, setTaxLoading] = useState(true)
  const [reportControls, setReportControls] = useState<ReportControls>({
    mode: 'org',
    preset: 'month',
    date_from: '',
    date_to: '',
    year: new Date().getFullYear(),
    quarter: 1,
  })
  const [unifiedTaxResult, setUnifiedTaxResult] = useState<UnifiedTaxReportResponse | null>(null)
  const [unifiedTaxLoading, setUnifiedTaxLoading] = useState(false)
  const [tgLink, setTgLink] = useState<string | null>(null)
  const [aiInput, setAiInput] = useState('')
  const [aiMessages, setAiMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([])
  const [aiLoading, setAiLoading] = useState(false)
  const [aiSessionId] = useState(createAiSessionId())
  const bottomRef = useRef<HTMLDivElement | null>(null)

  async function loadStaticData() {
    setStaticLoading(true)
    try {
      const [
        categoryResponse,
        activityResponse,
        organizationResponse,
        activityOptionsResponse,
        taxPeriodResponse,
      ] = await Promise.all([
        listCategories({ limit: 100 }),
        listOrganizationActivities({ limit: 100 }),
        getOrganizationProfile(),
        listActivityCodes({ limit: ACTIVITY_SEARCH_LIMIT }),
        getTaxPeriod().catch(() => null),
      ])

      setCategories(categoryResponse.results)
      setActivities(activityResponse.results)
      setOrganizationProfile(organizationResponse)
      setActivityOptions(activityOptionsResponse.results)
      setActivityOptionsCount(activityOptionsResponse.count)
      setTaxPeriod(taxPeriodResponse)
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось загрузить настройки рабочего пространства.')
    } finally {
      setStaticLoading(false)
    }
  }

  async function loadWorkspaceData() {
    setLoading(true)
    try {
      const params = buildDashboardParams(filters)
      const analyticsParams = buildAnalyticsParams(filters)
      const [dashboardResponse, seriesResponse, breakdownResponse, transactionResponse] = await Promise.all([
        getDashboard(params),
        getTimeSeries({
          ...analyticsParams,
          period: chartGranularity,
        }),
        getCategoryBreakdown({
          ...analyticsParams,
          limit: 6,
        }),
        listTransactions({
          ...params,
          limit: TRANSACTION_PAGE_SIZE,
          offset: transactionOffset,
        }),
      ])

      setDashboard(dashboardResponse)
      setTimeSeries(seriesResponse.data)
      setBreakdown(breakdownResponse.data)
      setTransactionPage(transactionResponse)
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось загрузить данные панели.')
    } finally {
      setLoading(false)
    }
  }

  async function loadTaxPanel() {
    if (reportControls.mode === 'custom' && (!reportControls.date_from || !reportControls.date_to)) {
      setTaxReport(null)
      setTaxTransactions(null)
      setTaxLoading(false)
      return
    }

    setTaxLoading(true)
    try {
      const { taxParams, transactionParams } = buildReportParams(reportControls, filters, reportOffset)
      const safeTransactionParams =
        reportControls.mode === 'org' && taxPeriod
          ? {
              ...transactionParams,
              date_from: taxPeriod.current_period.start,
              date_to: taxPeriod.current_period.end,
            }
          : transactionParams

      const [reportResponse, transactionResponse] = await Promise.all([
        getTaxReport(taxParams),
        listTransactions(safeTransactionParams),
      ])
      setTaxReport(reportResponse)
      setTaxTransactions(transactionResponse)
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось загрузить налоговый отчет.')
    } finally {
      setTaxLoading(false)
    }
  }

  useEffect(() => {
    setProfile(user)
  }, [user])

  useEffect(() => {
    void loadStaticData()
  }, [])

  useEffect(() => {
    void loadWorkspaceData()
  }, [
    chartGranularity,
    transactionOffset,
    filters.preset,
    filters.date_from,
    filters.date_to,
    filters.transaction_type,
    filters.category,
    filters.activity_code,
    filters.payment_method,
    filters.is_business,
    filters.is_taxable,
    filters.search,
    filters.ordering,
  ])

  useEffect(() => {
    void loadTaxPanel()
  }, [
    reportOffset,
    reportControls.mode,
    reportControls.preset,
    reportControls.date_from,
    reportControls.date_to,
    filters.transaction_type,
    filters.category,
    filters.activity_code,
    filters.payment_method,
    filters.is_business,
    filters.is_taxable,
    filters.ordering,
    taxPeriod?.current_period.start,
    taxPeriod?.current_period.end,
  ])

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      setActivitySearchLoading(true)
      try {
        const response = await listActivityCodes({
          search: activitySearch || undefined,
          limit: ACTIVITY_SEARCH_LIMIT,
        })
        setActivityOptions(response.results)
        setActivityOptionsCount(response.count)
      } catch {
        // Quiet while searching.
      } finally {
        setActivitySearchLoading(false)
      }
    }, 250)

    return () => window.clearTimeout(timer)
  }, [activitySearch])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [aiMessages, aiLoading])

  const incomeTotal = Number(dashboard?.totals.total_income ?? 0)
  const expenseTotal = Number(dashboard?.totals.total_expense ?? 0)
  const net = incomeTotal - expenseTotal
  const filteredCount = transactionPage?.count ?? 0
  const topCategories = dashboard?.by_category.slice(0, 4) ?? []
  const editableCategories = categories.filter((category) => !category.is_system)
  const currentTabMeta = {
    overview: {
      title: 'Панель управления',
    },
    transactions: {
      title: 'Операции',
    },
    tax: {
      title: 'Налоги',
    },
    profile: {
      title: 'Профиль и настройки',
    },
    assistant: {
      title: 'AI-помощник',
    },
  }[activeTab]

  const resetComposer = () => {
    setComposerDraft({
      ...makeDefaultTransactionDraft(),
      transaction_date: formatDateInput(new Date()),
    })
  }

  const saveTransaction = async (draft: TransactionDraft, existingId?: number) => {
    if (draft.is_business && !draft.activity_code) {
      pushNotice('error', 'Для бизнес-операции нужно выбрать вид деятельности.')
      return false
    }

    setTransactionSubmitting(true)
    try {
      if (existingId) {
        await updateTransaction(existingId, draft)
        pushNotice('success', 'Операция обновлена.')
      } else {
        await createTransaction(draft)
        pushNotice('success', 'Операция добавлена.')
        resetComposer()
      }
      setEditingTransaction(null)
      setTransactionOffset(0)
      setReportOffset(0)
      await Promise.all([loadWorkspaceData(), loadTaxPanel()])
      return true
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось сохранить операцию.')
      return false
    } finally {
      setTransactionSubmitting(false)
    }
  }

  const deleteTransactionItem = async (id: number) => {
    if (!window.confirm('Удалить эту операцию?')) {
      return
    }

    try {
      await deleteTransaction(id)
      pushNotice('success', 'Операция удалена.')
      await Promise.all([loadWorkspaceData(), loadTaxPanel()])
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось удалить операцию.')
    }
  }

  const saveProfileChanges = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const updated = await updateProfile({
        email: profile.email,
        first_name: profile.first_name,
        last_name: profile.last_name,
      })
      setProfile(updated)
      onUserUpdated(updated)
      pushNotice('success', 'Профиль обновлен.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось обновить профиль.')
    }
  }

  const saveOrganizationSettings = async (event: FormEvent) => {
    event.preventDefault()
    if (!organizationProfile) {
      return
    }

    try {
      const updated = await updateOrganizationProfile({
        tax_period_type: organizationProfile.tax_period_type ?? null,
        tax_period_preset:
          organizationProfile.tax_period_type === 'preset'
            ? organizationProfile.tax_period_preset ?? 'monthly'
            : null,
        tax_period_custom_day:
          organizationProfile.tax_period_type === 'custom'
            ? organizationProfile.tax_period_custom_day ?? 1
            : organizationProfile.tax_period_type === 'preset'
              ? organizationProfile.tax_period_custom_day ?? null
            : null,
      })
      setOrganizationProfile(updated)
      setTaxPeriod(await getTaxPeriod().catch(() => null))
      pushNotice('success', 'Настройки организации обновлены.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось обновить настройки организации.')
    }
  }

  const handleAddCategory = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const created = await createCategory({
        name: newCategoryName,
        category_type: newCategoryType,
      })
      setCategories((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)))
      setNewCategoryName('')
      pushNotice('success', 'Категория добавлена.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось добавить категорию.')
    }
  }

  const handleUpdateCategory = async (id: number) => {
    try {
      const updated = await updateCategory(id, { name: categoryEditName })
      setCategories((current) => current.map((category) => (category.id === id ? updated : category)))
      setCategoryEditingId(null)
      setCategoryEditName('')
      pushNotice('success', 'Категория обновлена.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось обновить категорию.')
    }
  }

  const handleDeleteCategory = async (category: Category) => {
    if (!window.confirm(`Удалить категорию «${category.name}»?`)) {
      return
    }
    try {
      await deleteCategory(category.id)
      setCategories((current) => current.filter((item) => item.id !== category.id))
      pushNotice('success', 'Категория удалена.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось удалить категорию.')
    }
  }

  const handleAddActivity = async (event: FormEvent) => {
    event.preventDefault()
    if (!activityDraft.activity) {
      pushNotice('error', 'Выберите вид деятельности.')
      return
    }
    try {
      const created = await createOrganizationActivity({
        ...activityDraft,
        is_primary: activities.length === 0,
      })
      setActivities((current) => [...current, created])
      setActivityDraft({
        activity: 0,
        cash_tax_rate: '3',
        non_cash_tax_rate: '0',
        is_primary: false,
      })
      setSelectedActivityOption(null)
      setActivitySearch('')
      pushNotice('success', 'Вид деятельности добавлен.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось добавить вид деятельности.')
    }
  }

  const togglePrimaryActivity = async (activity: OrganizationActivity) => {
    try {
      const updated = await updateOrganizationActivity(activity.id, { is_primary: true })
      setActivities((current) =>
        current.map((item) => (item.id === activity.id ? updated : { ...item, is_primary: false })),
      )
      pushNotice('success', 'Основной вид деятельности обновлен.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось обновить вид деятельности.')
    }
  }

  const removeActivity = async (id: number) => {
    if (!window.confirm('Удалить этот вид деятельности?')) {
      return
    }
    try {
      await deleteOrganizationActivity(id)
      setActivities((current) => current.filter((item) => item.id !== id))
      pushNotice('success', 'Вид деятельности удален.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось удалить вид деятельности.')
    }
  }

  const fetchTelegramLink = async () => {
    try {
      const response = await getTelegramLinkToken()
      setTgLink(response.link)
      pushNotice('info', 'Ссылка для Telegram создана. Она действует недолго.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось создать ссылку для Telegram.')
    }
  }

  const sendAiMessage = async (event: FormEvent) => {
    event.preventDefault()
    const message = aiInput.trim()
    if (!message || aiLoading) {
      return
    }

    setAiInput('')
    setAiMessages((current) => [...current, { role: 'user', text: message }])
    setAiLoading(true)
    try {
      const response = await consultAi(message, aiSessionId)
      setAiMessages((current) => [
        ...current,
        { role: 'assistant', text: formatAiAssistantReply(response.assistant) },
      ])
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'AI-помощник сейчас недоступен.')
    } finally {
      setAiLoading(false)
    }
  }

  const generateUnifiedReport = async () => {
    setUnifiedTaxLoading(true)
    try {
      const response = await generateUnifiedTaxReport({
        year: reportControls.year,
        quarter: reportControls.quarter,
      })
      setUnifiedTaxResult(response)
      pushNotice('success', 'Единый налоговый отчет сформирован.')
    } catch (error) {
      pushNotice('error', error instanceof Error ? error.message : 'Не удалось сформировать единый налоговый отчет.')
    } finally {
      setUnifiedTaxLoading(false)
    }
  }

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="sidebar-brand">
          <strong>Финансы</strong>
          <span>{profile.first_name || profile.email}</span>
        </div>

        <nav className="sidebar-nav">
          {[
            ['overview', 'Обзор'],
            ['transactions', 'Операции'],
            ['tax', 'Налоги'],
            ['profile', 'Профиль'],
            ['assistant', 'Помощник'],
          ].map(([tabKey, label]) => (
            <button
              key={tabKey}
              type="button"
              className={activeTab === tabKey ? 'sidebar-link active' : 'sidebar-link'}
              onClick={() => setActiveTab(tabKey as typeof activeTab)}
            >
              <strong>{label}</strong>
            </button>
          ))}
        </nav>

        <button type="button" className="ghost-button sidebar-logout" onClick={() => void onLogout()}>
          Выйти
        </button>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <div>
            <h1>{currentTabMeta.title}</h1>
          </div>

          <div className="workspace-actions">
            {activeTab === 'transactions' ? (
              <button type="button" className="primary-button" onClick={() => setShowComposerDialog(true)}>
                Новая операция
              </button>
            ) : null}
          </div>
        </header>

        <div
          className={`workspace-grid ${
            activeTab === 'overview' || activeTab === 'tax' || activeTab === 'transactions'
              ? 'overview-layout'
              : 'focus-layout'
          }`}
        >
        <main className="main-column">
          {(activeTab === 'overview' || activeTab === 'transactions') ? (
            <Section
              title="Период и фильтры"
              actions={
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setShowAdvancedFilters((current) => !current)}
                >
                  {showAdvancedFilters ? 'Скрыть фильтры' : 'Еще фильтры'}
                </button>
              }
            >
              <div className="compact-toolbar">
                <div className="segmented-inline">
                  {[
                    ['week', 'Неделя'],
                    ['month', 'Месяц'],
                    ['year', 'Год'],
                    ['all_time', 'Все время'],
                    ['custom', 'Свои даты'],
                  ].map(([preset, label]) => (
                    <button
                      key={preset}
                      type="button"
                      className={filters.preset === preset ? 'segment active' : 'segment'}
                      onClick={() => {
                        setFilters({
                          ...filters,
                          preset: preset as DashboardFilters['preset'],
                          ...(preset === 'custom' ? {} : getPresetRange(preset as Exclude<DashboardFilters['preset'], 'custom'>)),
                        })
                        setTransactionOffset(0)
                        setReportOffset(0)
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="field compact-search">
                  <input
                    value={filters.search}
                    onChange={(event) => {
                      setFilters({ ...filters, search: event.target.value })
                      setTransactionOffset(0)
                    }}
                    placeholder="Поиск по описанию"
                  />
                </div>

                <div className="compact-controls">
                  <label className="field compact-field">
                    <span>Тип</span>
                    <select
                      value={filters.transaction_type}
                      onChange={(event) => {
                        setFilters({
                          ...filters,
                          transaction_type: event.target.value as DashboardFilters['transaction_type'],
                        })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      <option value="income">Доходы</option>
                      <option value="expense">Расходы</option>
                    </select>
                  </label>

                  <label className="field compact-field">
                    <span>Сортировка</span>
                    <select
                      value={filters.ordering}
                      onChange={(event) => {
                        setFilters({ ...filters, ordering: event.target.value })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="-transaction_date">Сначала новые</option>
                      <option value="transaction_date">Сначала старые</option>
                      <option value="-amount">Сумма по убыванию</option>
                      <option value="amount">Сумма по возрастанию</option>
                    </select>
                  </label>

                  {activeTab === 'overview' ? (
                    <label className="field compact-field">
                      <span>График</span>
                      <select
                        value={chartGranularity}
                        onChange={(event) => setChartGranularity(event.target.value as ChartGranularity)}
                      >
                        <option value="daily">По дням</option>
                        <option value="monthly">По месяцам</option>
                        <option value="yearly">По годам</option>
                      </select>
                    </label>
                  ) : null}
                </div>
              </div>

              {showAdvancedFilters ? (
                <div className="field-grid four compact-advanced">
                  {filters.preset === 'custom' ? (
                    <>
                      <label className="field">
                        <span>Дата с</span>
                        <input
                          type="date"
                          value={filters.date_from}
                          onChange={(event) => {
                            setFilters({ ...filters, date_from: event.target.value })
                            setTransactionOffset(0)
                          }}
                        />
                      </label>
                      <label className="field">
                        <span>Дата по</span>
                        <input
                          type="date"
                          value={filters.date_to}
                          onChange={(event) => {
                            setFilters({ ...filters, date_to: event.target.value })
                            setTransactionOffset(0)
                          }}
                        />
                      </label>
                    </>
                  ) : null}

                  <label className="field">
                    <span>Категория</span>
                    <select
                      value={filters.category}
                      onChange={(event) => {
                        setFilters({ ...filters, category: event.target.value })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Вид деятельности</span>
                    <select
                      value={filters.activity_code}
                      onChange={(event) => {
                        setFilters({ ...filters, activity_code: event.target.value })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      {activities.map((activity) => (
                        <option key={activity.id} value={activity.activity}>
                          {activity.activity_name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Оплата</span>
                    <select
                      value={filters.payment_method}
                      onChange={(event) => {
                        setFilters({
                          ...filters,
                          payment_method: event.target.value as DashboardFilters['payment_method'],
                        })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      <option value="cash">Наличные</option>
                      <option value="non_cash">Безнал</option>
                    </select>
                  </label>

                  <label className="field">
                    <span>Назначение</span>
                    <select
                      value={filters.is_business}
                      onChange={(event) => {
                        setFilters({
                          ...filters,
                          is_business: event.target.value as DashboardFilters['is_business'],
                        })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      <option value="true">Бизнес</option>
                      <option value="false">Личное</option>
                    </select>
                  </label>

                  <label className="field">
                    <span>Налог</span>
                    <select
                      value={filters.is_taxable}
                      onChange={(event) => {
                        setFilters({
                          ...filters,
                          is_taxable: event.target.value as DashboardFilters['is_taxable'],
                        })
                        setTransactionOffset(0)
                      }}
                    >
                      <option value="">Все</option>
                      <option value="true">Облагается</option>
                      <option value="false">Не облагается</option>
                    </select>
                  </label>
                </div>
              ) : null}
            </Section>
          ) : null}

          {activeTab === 'overview' ? (
            <>
              <div className="metric-row dashboard-metrics">
                <article className="metric-card accent">
                  <span>Доход</span>
                  <strong>{formatCurrency(incomeTotal)}</strong>
                </article>
                <article className="metric-card">
                  <span>Расход</span>
                  <strong>{formatCurrency(expenseTotal)}</strong>
                </article>
                <article className="metric-card">
                  <span>Баланс</span>
                  <strong>{formatCurrency(net)}</strong>
                </article>
                <article className="metric-card">
                  <span>Операций</span>
                  <strong>{filteredCount}</strong>
                </article>
              </div>

              <div className="chart-grid">
                <Section
                  title="Динамика"
                  actions={
                    <div className="segmented-inline">
                      {(['area', 'bar', 'pie'] as ChartMode[]).map((mode) => (
                        <button
                          key={mode}
                          type="button"
                          className={chartMode === mode ? 'segment active' : 'segment'}
                          onClick={() => setChartMode(mode)}
                        >
                          {mode === 'area' ? 'Линия' : mode === 'bar' ? 'Столбцы' : 'Круг'}
                        </button>
                      ))}
                    </div>
                  }
                >
                  <div className="chart-frame">
                    {loading ? (
                      <div className="empty-state">Обновление графика...</div>
                    ) : chartMode === 'pie' ? (
                      breakdown.length ? (
                        <ResponsiveContainer width="100%" height={320}>
                          <PieChart key={`pie-${filters.preset}-${breakdown.length}`}>
                            <Pie
                              data={breakdown.map((item) => ({
                                name: item.category_name,
                                value: Number(item.total),
                              }))}
                              dataKey="value"
                              nameKey="name"
                              innerRadius={72}
                              outerRadius={112}
                              paddingAngle={2}
                            >
                              {breakdown.map((item, index) => (
                                <Cell
                                  key={`${item.category_name}-${index}`}
                                  fill={PIE_COLORS[index % PIE_COLORS.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="empty-state">Нет данных для круговой диаграммы.</div>
                      )
                    ) : timeSeries.length ? (
                      chartMode === 'bar' ? (
                        <ResponsiveContainer width="100%" height={320}>
                          <BarChart
                            key={`bar-${chartGranularity}-${filters.preset}-${timeSeries.length}`}
                            data={timeSeries.map((item) => ({
                              period: item.period,
                              income: Number(item.income),
                              expense: Number(item.expense),
                            }))}
                          >
                            <CartesianGrid strokeDasharray="4 4" stroke="rgba(32, 62, 52, 0.12)" />
                            <XAxis dataKey="period" stroke="#365148" />
                            <YAxis stroke="#365148" />
                            <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                            <Bar dataKey="income" fill="#1d7f5f" radius={[8, 8, 0, 0]} />
                            <Bar dataKey="expense" fill="#d97706" radius={[8, 8, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <ResponsiveContainer width="100%" height={320}>
                          <AreaChart
                            key={`area-${chartGranularity}-${filters.preset}-${timeSeries.length}`}
                            data={timeSeries.map((item) => ({
                              period: item.period,
                              income: Number(item.income),
                              expense: Number(item.expense),
                            }))}
                          >
                            <defs>
                              <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#1d7f5f" stopOpacity={0.5} />
                                <stop offset="95%" stopColor="#1d7f5f" stopOpacity={0.05} />
                              </linearGradient>
                              <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#d97706" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#d97706" stopOpacity={0.04} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="4 4" stroke="rgba(32, 62, 52, 0.12)" />
                            <XAxis dataKey="period" stroke="#365148" />
                            <YAxis stroke="#365148" />
                            <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                            <Area
                              type="monotone"
                              dataKey="income"
                              stroke="#1d7f5f"
                              fill="url(#incomeFill)"
                              strokeWidth={2.5}
                            />
                            <Area
                              type="monotone"
                              dataKey="expense"
                              stroke="#d97706"
                              fill="url(#expenseFill)"
                              strokeWidth={2.5}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      )
                    ) : (
                      <div className="empty-state">Нет данных для графика по выбранным фильтрам.</div>
                    )}
                  </div>
                </Section>

                <Section title="Категории">
                  <div className="stack-sm">
                    {topCategories.length ? (
                      topCategories.map((item) => (
                        <div key={`${item.category_name}-${item.total}`} className="stat-row">
                          <div>
                            <strong>{item.category_name || 'Без категории'}</strong>
                            <p>
                              {item.category_type === 'income'
                                ? 'Доход'
                                : item.category_type === 'expense'
                                  ? 'Расход'
                                  : 'Смешанный'}
                            </p>
                          </div>
                          <span>{formatCurrency(item.total)}</span>
                        </div>
                      ))
                    ) : (
                      <div className="empty-state">Нет данных по категориям.</div>
                    )}
                  </div>
                </Section>
              </div>
            </>
          ) : null}

          {activeTab === 'transactions' ? (
          <>
          <div className="metric-grid compact">
            <article className="metric-card positive">
              <span>Доход</span>
              <strong>{formatCurrency(incomeTotal)}</strong>
            </article>
            <article className="metric-card">
              <span>Расход</span>
              <strong>{formatCurrency(expenseTotal)}</strong>
            </article>
            <article className="metric-card">
              <span>Баланс</span>
              <strong>{formatCurrency(net)}</strong>
            </article>
            <article className="metric-card">
              <span>Операций</span>
              <strong>{filteredCount}</strong>
            </article>
          </div>

          <Section title="Операции" id="transactions">
            {loading || staticLoading ? (
              <div className="empty-state">Загрузка операций...</div>
            ) : transactionPage?.results.length ? (
              <>
                <div className="transaction-stream">
                  {transactionPage.results.map((transaction) => (
                    <article key={transaction.id} className="transaction-item">
                      <div className="transaction-main">
                        <div className="transaction-head">
                          <div>
                            <strong>{transaction.description || 'Без описания'}</strong>
                            <p>
                              {formatDateLabel(transaction.transaction_date)} ·{' '}
                              {transaction.transaction_type === 'income' ? 'Доход' : 'Расход'}
                            </p>
                          </div>
                          <div className="transaction-amount">
                            {formatCurrency(transaction.amount)}
                          </div>
                        </div>

                        <div className="transaction-meta">
                          <span className="tag neutral">{transaction.category_name || 'Без категории'}</span>
                          <span className="tag neutral">{transaction.activity_code_name || 'Без деятельности'}</span>
                          <span className="tag neutral">
                            {transaction.payment_method === 'cash' ? 'Наличные' : 'Безнал'}
                          </span>
                          <span className="tag neutral">
                            {transaction.is_business ? 'Бизнес' : 'Личное'}
                          </span>
                          <span className="tag neutral">
                            {transaction.is_taxable ? 'Облагается' : 'Не облагается'}
                          </span>
                        </div>
                      </div>

                      <div className="transaction-actions">
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => setEditingTransaction(transaction)}
                        >
                          Изменить
                        </button>
                        <button
                          type="button"
                          className="ghost-button danger"
                          onClick={() => void deleteTransactionItem(transaction.id)}
                        >
                          Удалить
                        </button>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="pagination-row">
                  <span>
                    Показано {transactionPage.results.length} из {transactionPage.count}
                  </span>
                  <div className="segmented-inline">
                    <button
                      type="button"
                      className="segment"
                      onClick={() => setTransactionOffset((current) => Math.max(0, current - TRANSACTION_PAGE_SIZE))}
                      disabled={transactionOffset === 0}
                    >
                      Назад
                    </button>
                    <button
                      type="button"
                      className="segment"
                      onClick={() => setTransactionOffset((current) => current + TRANSACTION_PAGE_SIZE)}
                      disabled={!transactionPage.next}
                    >
                      Вперед
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">По этим фильтрам операций нет.</div>
            )}
          </Section>
          </>
          ) : null}

          {activeTab === 'tax' ? (
          <Section title="Налоги" id="tax">
            <div className="stack-md">
              <div className="segmented-inline">
                {(['org', 'preset', 'custom'] as ReportControls['mode'][]).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    className={reportControls.mode === mode ? 'segment active' : 'segment'}
                    onClick={() => {
                      setReportControls({ ...reportControls, mode })
                      setReportOffset(0)
                    }}
                  >
                    {mode === 'org' ? 'Период организации' : mode === 'preset' ? 'Готовый период' : 'Свои даты'}
                  </button>
                ))}
              </div>

              {reportControls.mode === 'preset' ? (
                <div className="segmented-inline">
                  {(['week', 'month', 'year', 'all_time'] as ReportControls['preset'][]).map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      className={reportControls.preset === preset ? 'segment active' : 'segment'}
                      onClick={() => {
                        setReportControls({ ...reportControls, preset })
                        setReportOffset(0)
                      }}
                    >
                      {preset === 'week' ? 'Неделя' : preset === 'month' ? 'Месяц' : preset === 'year' ? 'Год' : 'Все время'}
                    </button>
                  ))}
                </div>
              ) : null}

              {reportControls.mode === 'custom' ? (
                <div className="field-grid two">
                  <label className="field">
                    <span>Дата с</span>
                    <input
                      type="date"
                      value={reportControls.date_from}
                      onChange={(event) => {
                        setReportControls({ ...reportControls, date_from: event.target.value })
                        setReportOffset(0)
                      }}
                    />
                  </label>
                  <label className="field">
                    <span>Дата по</span>
                    <input
                      type="date"
                      value={reportControls.date_to}
                      onChange={(event) => {
                        setReportControls({ ...reportControls, date_to: event.target.value })
                        setReportOffset(0)
                      }}
                    />
                  </label>
                </div>
              ) : null}

              {taxPeriod ? (
                <div className="soft-card">
                  <p className="soft-card-title">Текущий налоговый период</p>
                  <p>
                    {formatDateLabel(taxPeriod.current_period.start)} -{' '}
                    {formatDateLabel(taxPeriod.current_period.end)}
                  </p>
                  <small>Следующий период начинается {formatDateLabel(taxPeriod.next_period_start)}</small>
                </div>
              ) : null}

              {taxLoading ? (
                <div className="empty-state">Загрузка налоговых данных...</div>
              ) : taxReport ? (
                <>
                  <div className="metric-row compact">
                    <article className="metric-card accent">
                      <span>Доход</span>
                      <strong>{formatCurrency(taxReport.totals.total_income)}</strong>
                    </article>
                    <article className="metric-card">
                      <span>Расход</span>
                      <strong>{formatCurrency(taxReport.totals.total_expense)}</strong>
                    </article>
                    <article className="metric-card">
                      <span>Итог</span>
                      <strong>{formatCurrency(taxReport.totals.net)}</strong>
                    </article>
                  </div>

                  <div className="field-grid two">
                    <div className="soft-card">
                      <p className="soft-card-title">Облагаемые</p>
                      <p>Доход: {formatCurrency(taxReport.taxable.income)}</p>
                      <p>Расход: {formatCurrency(taxReport.taxable.expense)}</p>
                    </div>
                    <div className="soft-card">
                      <p className="soft-card-title">Необлагаемые</p>
                      <p>Доход: {formatCurrency(taxReport.non_taxable.income)}</p>
                      <p>Расход: {formatCurrency(taxReport.non_taxable.expense)}</p>
                    </div>
                  </div>

                  <div className="field-grid two">
                    <div className="soft-card">
                      <p className="soft-card-title">По способу оплаты</p>
                      <div className="stack-xs">
                        {taxReport.by_payment_method.map((row) => (
                          <div key={row.payment_method} className="stat-row">
                            <div>
                              <strong>{row.payment_method_display}</strong>
                              <p>Доход {formatCurrency(row.income)}</p>
                            </div>
                            <span>{formatCurrency(row.net)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="soft-card">
                      <p className="soft-card-title">По видам деятельности</p>
                      <div className="stack-xs">
                        {taxReport.by_activity.length ? (
                          taxReport.by_activity.map((row) => (
                            <div key={`${row.activity_code_id}-${row.activity_name}`} className="stat-row">
                              <div>
                                <strong>{row.activity_name || 'Без деятельности'}</strong>
                                <p>Доход {formatCurrency(row.income)}</p>
                              </div>
                              <span>{formatCurrency(row.net)}</span>
                            </div>
                          ))
                        ) : (
                          <div className="empty-state shallow">Нет данных по видам деятельности.</div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="soft-card">
                    <p className="soft-card-title">Операции за период</p>
                    <div className="table-scroll">
                      <table className="data-table dense">
                        <thead>
                          <tr>
                            <th>Дата</th>
                            <th>Тип</th>
                            <th>Сумма</th>
                            <th>Категория</th>
                            <th>Описание</th>
                          </tr>
                        </thead>
                        <tbody>
                          {taxTransactions?.results.map((transaction) => (
                            <tr key={transaction.id}>
                              <td>{formatDateLabel(transaction.transaction_date)}</td>
                              <td>{transaction.transaction_type === 'income' ? 'Доход' : 'Расход'}</td>
                              <td>{formatCurrency(transaction.amount)}</td>
                              <td>{transaction.category_name || '-'}</td>
                              <td>{transaction.description || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="pagination-row">
                      <span>
                        Показано {taxTransactions?.results.length ?? 0} из {taxTransactions?.count ?? 0}
                      </span>
                      <div className="segmented-inline">
                        <button
                          type="button"
                          className="segment"
                          onClick={() => setReportOffset((current) => Math.max(0, current - TAX_TRANSACTION_PAGE_SIZE))}
                          disabled={reportOffset === 0}
                        >
                          Назад
                        </button>
                        <button
                          type="button"
                          className="segment"
                          onClick={() => setReportOffset((current) => current + TAX_TRANSACTION_PAGE_SIZE)}
                          disabled={!taxTransactions?.next}
                        >
                          Вперед
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-state">Выберите период.</div>
              )}

              <div className="field-grid three">
                <label className="field">
                  <span>Год отчета</span>
                  <input
                    type="number"
                    min="2000"
                    max="2100"
                    value={reportControls.year}
                    onChange={(event) =>
                      setReportControls({
                        ...reportControls,
                        year: Number(event.target.value),
                      })
                    }
                  />
                </label>

                <label className="field">
                  <span>Квартал</span>
                  <select
                    value={reportControls.quarter}
                    onChange={(event) =>
                      setReportControls({
                        ...reportControls,
                        quarter: Number(event.target.value) as 1 | 2 | 3 | 4,
                      })
                    }
                  >
                    <option value={1}>1 квартал</option>
                    <option value={2}>2 квартал</option>
                    <option value={3}>3 квартал</option>
                    <option value={4}>4 квартал</option>
                  </select>
                </label>

                <div className="field action-field">
                  <span>Формирование</span>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void generateUnifiedReport()}
                    disabled={unifiedTaxLoading}
                  >
                    {unifiedTaxLoading ? 'Формирование...' : 'Сформировать'}
                  </button>
                </div>
              </div>

              {unifiedTaxResult ? (
                <div className="soft-card">
                  <p className="soft-card-title">Единый налоговый отчет</p>
                  {unifiedTaxResult.validation_summary ? (
                    <p className="muted">{unifiedTaxResult.validation_summary}</p>
                  ) : null}
                  {unifiedTaxResult.pdf_file ? (
                    <p>
                      <a href={unifiedTaxResult.pdf_file} target="_blank" rel="noreferrer">
                        Открыть файл PDF
                      </a>
                    </p>
                  ) : (
                    <p className="muted">PDF не сформирован (нет шаблона или ошибка генерации).</p>
                  )}
                  <pre className="report-pre">{unifiedTaxResult.verbal_report}</pre>
                  <ChatMessageBody text={formatAiAssistantReply(unifiedTaxResult.ai_validation)} />
                </div>
              ) : null}
            </div>
          </Section>
          ) : null}
        </main>

        {activeTab === 'profile' || activeTab === 'assistant' ? (
        <aside className="side-column">
          {activeTab === 'assistant' ? (
          <Section title="AI-помощник" id="assistant">
            <div className="ai-log">
              {aiMessages.length ? (
                aiMessages.map((message, index) => (
                  <article key={`${message.role}-${index}`} className={`chat-bubble ${message.role}`}>
                    <span>{message.role === 'user' ? 'Вы' : 'Помощник'}</span>
                    <ChatMessageBody text={message.text} />
                  </article>
                ))
              ) : (
                <div className="empty-state shallow">
                  Задайте вопрос по налогам, отчету или классификации операции.
                </div>
              )}
              {aiLoading ? <div className="empty-state shallow">Думаю...</div> : null}
              <div ref={bottomRef} />
            </div>
            <form className="stack-sm" onSubmit={(event) => void sendAiMessage(event)}>
              <label className="field">
                <span>Сообщение</span>
                <textarea
                  rows={3}
                  value={aiInput}
                  onChange={(event) => setAiInput(event.target.value)}
                  placeholder="Например: как учитывать этот расход?"
                />
              </label>
              <button type="submit" className="primary-button" disabled={aiLoading}>
                Отправить
              </button>
            </form>
          </Section>
          ) : null}

          {activeTab === 'profile' ? (
          <Section title="Профиль и Telegram" id="profile">
            <form className="stack-sm" onSubmit={(event) => void saveProfileChanges(event)}>
              <label className="field">
                <span>Почта</span>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(event) => setProfile({ ...profile, email: event.target.value })}
                />
              </label>
              <div className="field-grid two">
                <label className="field">
                  <span>Имя</span>
                  <input
                    value={profile.first_name}
                    onChange={(event) => setProfile({ ...profile, first_name: event.target.value })}
                  />
                </label>
                <label className="field">
                  <span>Фамилия</span>
                  <input
                    value={profile.last_name}
                    onChange={(event) => setProfile({ ...profile, last_name: event.target.value })}
                  />
                </label>
              </div>
              <button type="submit" className="secondary-button">
                Сохранить профиль
              </button>
            </form>

            <div className="soft-card">
              <p className="soft-card-title">Наименование организации</p>
              {organizationProfile?.taxpayer_name?.trim() ? (
                <p>{organizationProfile.taxpayer_name}</p>
              ) : (
                <p className="muted">
                  Наименование пока не заполнено. Заполните реквизиты организации в онбординге, чтобы оно
                  отображалось здесь.
                </p>
              )}
              {organizationProfile?.org_type ? (
                <p className="muted">
                  Тип организации: {organizationProfile.org_type === 'ie' ? 'ИП' : 'ОсОО'}
                </p>
              ) : null}
            </div>

            <div className="soft-card">
              <p className="soft-card-title">Telegram-бот</p>
              <p>{profile.telegram_id ? `Подключен: ${profile.telegram_id}` : 'Еще не подключен.'}</p>
              <button type="button" className="ghost-button" onClick={() => void fetchTelegramLink()}>
                Получить ссылку
              </button>
              {tgLink ? (
                <p className="muted">
                  <a href={tgLink} target="_blank" rel="noreferrer">
                    Открыть подключение в Telegram
                  </a>
                </p>
              ) : null}
            </div>

            {organizationProfile ? (
              <form className="stack-sm" onSubmit={(event) => void saveOrganizationSettings(event)}>
                <div className="field-grid two">
                  <label className="field">
                    <span>Тип налогового периода</span>
                    <select
                      value={organizationProfile.tax_period_type ?? ''}
                      onChange={(event) =>
                        setOrganizationProfile({
                          ...organizationProfile,
                          tax_period_type: (event.target.value || null) as TaxPeriodType | null,
                          tax_period_preset:
                            event.target.value === 'preset'
                              ? organizationProfile.tax_period_preset ?? 'monthly'
                              : null,
                          tax_period_custom_day:
                            event.target.value === 'preset'
                              ? organizationProfile.tax_period_custom_day ?? null
                              : event.target.value === 'custom'
                              ? organizationProfile.tax_period_custom_day ?? 1
                              : null,
                        })
                      }
                    >
                      <option value="">Не задан</option>
                      <option value="preset">Готовый период</option>
                      <option value="custom">Свой день</option>
                    </select>
                  </label>

                  {organizationProfile.tax_period_type === 'preset' ? (
                    <>
                    <label className="field">
                      <span>Период</span>
                      <select
                        value={organizationProfile.tax_period_preset ?? ''}
                        onChange={(event) =>
                          setOrganizationProfile({
                            ...organizationProfile,
                            tax_period_preset: (event.target.value || null) as TaxPeriodPreset | null,
                          })
                        }
                      >
                        <option value="monthly">Ежемесячно</option>
                        <option value="quarterly">Ежеквартально</option>
                        <option value="yearly">Ежегодно</option>
                      </select>
                    </label>
                    <label className="field">
                      <span>День начала периода</span>
                      <input
                        type="number"
                        min="1"
                        max="31"
                        placeholder="1"
                        value={organizationProfile.tax_period_custom_day ?? ''}
                        onChange={(event) =>
                          setOrganizationProfile({
                            ...organizationProfile,
                            tax_period_custom_day: event.target.value ? Number(event.target.value) : null,
                          })
                        }
                      />
                    </label>
                    </>
                  ) : null}

                  {organizationProfile.tax_period_type === 'custom' ? (
                    <label className="field">
                      <span>День месяца</span>
                      <input
                        type="number"
                        min="1"
                        max="31"
                        value={organizationProfile.tax_period_custom_day ?? ''}
                        onChange={(event) =>
                          setOrganizationProfile({
                            ...organizationProfile,
                            tax_period_custom_day: event.target.value ? Number(event.target.value) : null,
                          })
                        }
                      />
                    </label>
                  ) : null}
                </div>

                <button type="submit" className="secondary-button">
                  Сохранить настройки
                </button>
              </form>
            ) : null}
          </Section>
          ) : null}

          {activeTab === 'profile' ? (
          <Section title="Категории">
            <form className="stack-sm" onSubmit={(event) => void handleAddCategory(event)}>
              <div className="field-grid two">
                <label className="field">
                  <span>Название</span>
                  <input
                    value={newCategoryName}
                    onChange={(event) => setNewCategoryName(event.target.value)}
                    required
                  />
                </label>
                <label className="field">
                  <span>Тип</span>
                  <select
                    value={newCategoryType}
                    onChange={(event) => setNewCategoryType(event.target.value as TransactionType)}
                  >
                    <option value="expense">Расход</option>
                    <option value="income">Доход</option>
                  </select>
                </label>
              </div>
              <button type="submit" className="secondary-button">
                Добавить категорию
              </button>
            </form>

            <div className="stack-sm">
              {editableCategories.length ? (
                editableCategories.map((category) => (
                <div key={category.id} className="mini-table-row">
                  <div>
                    {categoryEditingId === category.id ? (
                      <input
                        value={categoryEditName}
                        onChange={(event) => setCategoryEditName(event.target.value)}
                      />
                    ) : (
                      <strong>{category.name}</strong>
                    )}
                    <p>
                      {category.category_type === 'income' ? 'Доход' : 'Расход'} {category.is_system ? '· системная' : ''}
                    </p>
                  </div>
                  <div className="mini-table-actions">
                    {category.is_system ? null : categoryEditingId === category.id ? (
                      <>
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => void handleUpdateCategory(category.id)}
                        >
                          Сохранить
                        </button>
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => {
                            setCategoryEditingId(null)
                            setCategoryEditName('')
                          }}
                        >
                          Отмена
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => {
                            setCategoryEditingId(category.id)
                            setCategoryEditName(category.name)
                          }}
                        >
                          Переименовать
                        </button>
                        <button
                          type="button"
                          className="ghost-button danger"
                          onClick={() => void handleDeleteCategory(category)}
                        >
                          Удалить
                        </button>
                      </>
                    )}
                  </div>
                </div>
                ))
              ) : (
                <div className="empty-state shallow">Пользовательских категорий пока нет.</div>
              )}
            </div>
          </Section>
          ) : null}

          {activeTab === 'profile' ? (
          <Section title="Виды деятельности">
            <form className="stack-sm activity-form" onSubmit={(event) => void handleAddActivity(event)}>
              <ActivityPicker
                searchValue={activitySearch}
                onSearchChange={(value) => {
                  setActivitySearch(value)
                  setSelectedActivityOption(null)
                  setActivityDraft((current) => ({ ...current, activity: 0 }))
                }}
                options={activityOptions}
                selectedActivity={selectedActivityOption}
                onSelect={(activity) => {
                  setSelectedActivityOption(activity)
                  setActivityDraft((current) => ({ ...current, activity: activity.id }))
                }}
                onClear={() => {
                  setActivitySearch('')
                  setSelectedActivityOption(null)
                  setActivityDraft((current) => ({ ...current, activity: 0 }))
                }}
                totalCount={activityOptionsCount}
                loading={activitySearchLoading}
              />
              <label className="field">
                <span>Поиск</span>
                <input
                  value={activitySearch}
                  onChange={(event) => setActivitySearch(event.target.value)}
                  placeholder="Поиск по коду или названию"
                />
              </label>

              <div className="field-grid two">
                <label className="field">
                  <span>Вид деятельности</span>
                  <select
                    value={activityDraft.activity || ''}
                    onChange={(event) =>
                      setActivityDraft({ ...activityDraft, activity: Number(event.target.value) })
                    }
                  >
                    <option value="">Выберите вид деятельности</option>
                    {activityOptions.map((activity) => (
                      <option key={activity.id} value={activity.id}>
                        {activity.code} - {activity.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>Ставка наличных</span>
                  <input
                    value={activityDraft.cash_tax_rate}
                    onChange={(event) =>
                      setActivityDraft({
                        ...activityDraft,
                        cash_tax_rate: event.target.value,
                      })
                    }
                  />
                </label>

                <label className="field">
                  <span>Ставка безнала</span>
                  <input
                    value={activityDraft.non_cash_tax_rate}
                    onChange={(event) =>
                      setActivityDraft({
                        ...activityDraft,
                        non_cash_tax_rate: event.target.value,
                      })
                    }
                  />
                </label>
              </div>

              {!activities.length ? <p className="muted">Первый добавленный вид станет основным.</p> : null}

              <button type="submit" className="secondary-button">
                Добавить вид
              </button>
            </form>

            <div className="stack-sm">
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
                        onClick={() => void togglePrimaryActivity(activity)}
                      >
                        Сделать основным
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="ghost-button danger"
                      onClick={() => void removeActivity(activity.id)}
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Section>
          ) : null}
        </aside>
        ) : null}
      </div>
      </div>

      {editingTransaction ? (
        <Dialog title="Изменить операцию" onClose={() => setEditingTransaction(null)}>
          <TransactionForm
            draft={{
              amount: editingTransaction.amount,
              transaction_type: editingTransaction.transaction_type,
              category: editingTransaction.category,
              description: editingTransaction.description,
              transaction_date: editingTransaction.transaction_date,
              payment_method: editingTransaction.payment_method,
              is_business: editingTransaction.is_business,
              is_taxable: editingTransaction.is_taxable,
              activity_code: editingTransaction.activity_code,
            }}
            setDraft={(value) =>
              setEditingTransaction({
                ...editingTransaction,
                amount: value.amount,
                transaction_type: value.transaction_type,
                category: value.category,
                description: value.description,
                transaction_date: value.transaction_date,
                payment_method: value.payment_method,
                is_business: value.is_business,
                is_taxable: value.is_taxable,
                activity_code: value.activity_code,
              })
            }
            categories={categories}
            activities={activities}
            submitting={transactionSubmitting}
            submitLabel="Сохранить"
            onSubmit={(event) => {
              event.preventDefault()
              void saveTransaction(
                {
                  amount: editingTransaction.amount,
                  transaction_type: editingTransaction.transaction_type,
                  category: editingTransaction.category,
                  description: editingTransaction.description,
                  transaction_date: editingTransaction.transaction_date,
                  payment_method: editingTransaction.payment_method,
                  is_business: editingTransaction.is_business,
                  is_taxable: editingTransaction.is_taxable,
                  activity_code: editingTransaction.activity_code,
                },
                editingTransaction.id,
              )
            }}
          />
        </Dialog>
      ) : null}

      {showComposerDialog ? (
        <Dialog title="Новая операция" onClose={() => setShowComposerDialog(false)}>
          <TransactionForm
            draft={composerDraft}
            setDraft={setComposerDraft}
            categories={categories}
            activities={activities}
            submitting={transactionSubmitting}
            submitLabel="Добавить"
            onSubmit={async (event) => {
              event.preventDefault()
              const saved = await saveTransaction(composerDraft)
              if (saved) {
                setShowComposerDialog(false)
              }
            }}
          />
        </Dialog>
      ) : null}
    </div>
  )
}
