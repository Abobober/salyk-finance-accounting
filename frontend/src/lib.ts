import type { OrganizationActivity } from './api/organization'
import type { Category, TransactionDraft, TransactionType } from './api/finance'

export type NoticeTone = 'success' | 'error' | 'info'
export type AuthMode = 'login' | 'register'
export type DashboardPreset = 'week' | 'month' | 'year' | 'all_time' | 'custom'
export type ChartMode = 'area' | 'bar' | 'pie'
export type ChartGranularity = 'daily' | 'monthly' | 'yearly'
export type ReportMode = 'org' | 'preset' | 'custom'

export interface NoticeState {
  tone: NoticeTone
  text: string
}

export interface DashboardFilters {
  preset: DashboardPreset
  date_from: string
  date_to: string
  transaction_type: '' | TransactionType
  category: string
  activity_code: string
  payment_method: '' | 'cash' | 'non_cash'
  is_business: '' | 'true' | 'false'
  is_taxable: '' | 'true' | 'false'
  search: string
  ordering: string
}

export interface ReportControls {
  mode: ReportMode
  preset: 'week' | 'month' | 'year' | 'all_time'
  date_from: string
  date_to: string
  year: number
  quarter: 1 | 2 | 3 | 4
}

export interface OrganizationActivityDraft {
  activity: number
  cash_tax_rate: string
  non_cash_tax_rate: string
  is_primary: boolean
}

export const PIE_COLORS = ['#1d7f5f', '#d97706', '#21538f', '#7c3aed', '#bb3e03', '#3f8f96']
export const TRANSACTION_PAGE_SIZE = 12
export const TAX_TRANSACTION_PAGE_SIZE = 8

export function formatCurrency(value: string | number) {
  const amount = typeof value === 'number' ? value : Number(value || 0)
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'KGS',
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0)
}

export function formatDateLabel(value: string) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatDateInput(date: Date) {
  return date.toISOString().slice(0, 10)
}

export function createAiSessionId() {
  return `sess_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`
}

function cleanupAiLine(line: string) {
  return line
    .replace(/\\text\{([^}]*)\}/g, '$1')
    .replace(/\\sum_\{([^}]*)\}\s*/g, 'сумма по ')
    .replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, '$1 / $2')
    .replace(/\\cdot/g, ' * ')
    .replace(/\\times/g, ' * ')
    .replace(/\\%/g, '%')
    .replace(/[{}]/g, '')
    // Strip CJK chars/noise that sometimes appears in model output.
    .replace(/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/g, '')
    .replace(/^#{1,6}\s*/, '')
    .replace(/^\*+\s*/, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\\\[/g, '')
    .replace(/\\\]/g, '')
    .replace(/\\\(/g, '')
    .replace(/\\\)/g, '')
    .replace(/\bcash\b/gi, 'наличные')
    .replace(/\bnon[- ]?cash\b/gi, 'безнал')
    .replace(/Cash_доход/gi, 'Наличный доход')
    .replace(/NonCash_доход/gi, 'Безналичный доход')
    .replace(/[ \t]+/g, ' ')
    .trim()
}

function shortenAiLine(line: string, maxLength = 170) {
  if (line.length <= maxLength) {
    return line
  }

  const shortened = line.slice(0, maxLength).trim()
  const lastSpace = shortened.lastIndexOf(' ')
  return `${(lastSpace > 60 ? shortened.slice(0, lastSpace) : shortened).trim()}...`
}

export function formatAiAssistantReply(raw: string) {
  const normalized = raw.replace(/\r\n/g, '\n').replace(/[\u00A0\u202F\u2009]/g, ' ')
  const lines = normalized
    .split('\n')
    .map((line) => cleanupAiLine(line))
    .filter(Boolean)

  if (!lines.length) {
    return cleanupAiLine(raw)
  }

  const deduped = lines.filter((line, index) => {
    if (line.length < 2) {
      return false
    }
    return line.toLowerCase() !== (lines[index - 1] ?? '').toLowerCase()
  })

  // Keep the full answer body and only trim very long individual lines.
  return deduped.map((line) => shortenAiLine(line, 500)).join('\n')
}

export function getPresetRange(preset: Exclude<DashboardPreset, 'custom'>) {
  const today = new Date()
  const end = formatDateInput(today)

  if (preset === 'all_time') {
    return { date_from: '', date_to: '' }
  }

  const start = new Date(today)
  if (preset === 'week') {
    start.setDate(today.getDate() - 6)
  } else if (preset === 'month') {
    start.setDate(1)
  } else {
    start.setMonth(0, 1)
  }

  return {
    date_from: formatDateInput(start),
    date_to: end,
  }
}

export function buildDashboardParams(filters: DashboardFilters) {
  const range =
    filters.preset === 'custom'
      ? { date_from: filters.date_from, date_to: filters.date_to }
      : getPresetRange(filters.preset)

  return {
    ...range,
    transaction_type: filters.transaction_type || undefined,
    category: filters.category || undefined,
    activity_code: filters.activity_code || undefined,
    payment_method: filters.payment_method || undefined,
    is_business: filters.is_business || undefined,
    is_taxable: filters.is_taxable || undefined,
    search: filters.search || undefined,
    ordering: filters.ordering || undefined,
  }
}

export function buildAnalyticsParams(filters: DashboardFilters) {
  const base = {
    transaction_type: filters.transaction_type || undefined,
    category: filters.category || undefined,
    activity_code: filters.activity_code || undefined,
    payment_method: filters.payment_method || undefined,
    is_business: filters.is_business || undefined,
    is_taxable: filters.is_taxable || undefined,
    search: filters.search || undefined,
  }

  if (filters.preset === 'custom') {
    return {
      ...base,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
    }
  }

  return {
    ...base,
    preset: filters.preset,
  }
}

export function buildReportParams(
  controls: ReportControls,
  filters: DashboardFilters,
  taxOffset = 0,
) {
  const shared = {
    transaction_type: filters.transaction_type || undefined,
    category: filters.category || undefined,
    activity_code: filters.activity_code || undefined,
    payment_method: filters.payment_method || undefined,
    is_business: filters.is_business || undefined,
    is_taxable: filters.is_taxable || undefined,
    ordering: filters.ordering || '-transaction_date',
    limit: TAX_TRANSACTION_PAGE_SIZE,
    offset: taxOffset,
  }

  if (controls.mode === 'org') {
    return {
      taxParams: {
        ...shared,
        use_org_tax_period: 'true',
      },
      transactionParams: shared,
    }
  }

  if (controls.mode === 'preset') {
    const range = getPresetRange(controls.preset)
    return {
      taxParams: {
        ...shared,
        preset: controls.preset,
      },
      transactionParams: {
        ...shared,
        ...range,
      },
    }
  }

  return {
    taxParams: {
      ...shared,
      date_from: controls.date_from,
      date_to: controls.date_to,
    },
    transactionParams: {
      ...shared,
      date_from: controls.date_from,
      date_to: controls.date_to,
    },
  }
}

export function makeDefaultTransactionDraft(): TransactionDraft {
  return {
    amount: '',
    transaction_type: 'income',
    category: null,
    description: '',
    transaction_date: formatDateInput(new Date()),
    payment_method: 'non_cash',
    is_business: true,
    is_taxable: true,
    activity_code: null,
  }
}

export function getMatchingCategories(
  categories: Category[],
  transactionType: TransactionType,
) {
  return categories.filter((category) => category.category_type === transactionType)
}

export function getActivityLabel(activity: OrganizationActivity) {
  return `${activity.activity_name}${activity.is_primary ? ' - Основной' : ''}`
}
