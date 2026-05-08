import { Fragment, type FormEvent, type ReactNode } from 'react'
import type { ActivityCode } from './api/activities'
import type { Category, TransactionDraft, TransactionType } from './api/finance'
import type { OrganizationActivity } from './api/organization'
import { getActivityLabel, getMatchingCategories } from './lib'

export function Section({
  id,
  title,
  eyebrow,
  actions,
  children,
}: {
  id?: string
  title: string
  eyebrow?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section id={id} className="panel">
      <div className="panel-header">
        <div>
          {eyebrow ? <p className="panel-eyebrow">{eyebrow}</p> : null}
          <h2>{title}</h2>
        </div>
        {actions}
      </div>
      {children}
    </section>
  )
}

export function Dialog({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: ReactNode
}) {
  return (
    <div className="dialog-backdrop" role="presentation" onClick={onClose}>
      <div
        className="dialog-card"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="dialog-header">
          <h3>{title}</h3>
          <button type="button" className="ghost-button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function renderInlineText(text: string) {
  const chunks = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean)

  return chunks.map((chunk, index) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      return <strong key={`${chunk}-${index}`}>{chunk.slice(2, -2)}</strong>
    }
    if (chunk.startsWith('`') && chunk.endsWith('`')) {
      return <code key={`${chunk}-${index}`}>{chunk.slice(1, -1)}</code>
    }
    return <Fragment key={`${chunk}-${index}`}>{chunk}</Fragment>
  })
}

function parseMessageBlocks(text: string) {
  const normalized = text.replace(/\r\n/g, '\n').trim()
  if (!normalized) {
    return []
  }

  const blocks: Array<{ type: 'paragraph'; text: string } | { type: 'list'; items: string[] }> = []
  let paragraph: string[] = []
  let list: string[] = []

  const flushParagraph = () => {
    if (!paragraph.length) {
      return
    }
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') })
    paragraph = []
  }

  const flushList = () => {
    if (!list.length) {
      return
    }
    blocks.push({ type: 'list', items: list })
    list = []
  }

  for (const rawLine of normalized.split('\n')) {
    const line = rawLine.trim()
    if (!line) {
      flushParagraph()
      flushList()
      continue
    }

    const listMatch = line.match(/^(?:[-*\u2022]|\d+[.)])\s+(.*)$/)
    if (listMatch) {
      flushParagraph()
      list.push(listMatch[1].trim())
      continue
    }

    flushList()
    paragraph.push(line)
  }

  flushParagraph()
  flushList()

  return blocks
}

export function ChatMessageBody({ text }: { text: string }) {
  const blocks = parseMessageBlocks(text)

  if (!blocks.length) {
    return null
  }

  return (
    <div className="chat-message-body">
      {blocks.map((block, index) =>
        block.type === 'list' ? (
          <ul key={`list-${index}`} className="chat-list">
            {block.items.map((item, itemIndex) => (
              <li key={`item-${index}-${itemIndex}`}>{renderInlineText(item)}</li>
            ))}
          </ul>
        ) : (
          <p key={`paragraph-${index}`}>{renderInlineText(block.text)}</p>
        ),
      )}
    </div>
  )
}

function formatActivityOptionLabel(activity: ActivityCode) {
  return `${activity.code} - ${activity.name}`
}

export function ActivityPicker({
  searchValue,
  onSearchChange,
  options,
  selectedActivity,
  onSelect,
  onClear,
  totalCount,
  loading,
  disabled = false,
}: {
  searchValue: string
  onSearchChange: (value: string) => void
  options: ActivityCode[]
  selectedActivity: ActivityCode | null
  onSelect: (activity: ActivityCode) => void
  onClear: () => void
  totalCount: number
  loading: boolean
  disabled?: boolean
}) {
  const hasSearch = searchValue.trim().length > 0

  return (
    <div className="activity-picker stack-sm">
      <label className="field">
        <span>Поиск по коду или названию</span>
        <input
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Например: 47.91 или торговля"
          disabled={disabled}
        />
      </label>

      {selectedActivity ? (
        <div className="activity-selection">
          <div>
            <span>Выбрано</span>
            <strong>{formatActivityOptionLabel(selectedActivity)}</strong>
            <p>Раздел: {selectedActivity.section}</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClear} disabled={disabled}>
            Сбросить
          </button>
        </div>
      ) : null}

      <div className="activity-results" role="list">
        {options.length ? (
          options.map((activity) => {
            const isActive = activity.id === selectedActivity?.id

            return (
              <button
                key={activity.id}
                type="button"
                className={isActive ? 'activity-result active' : 'activity-result'}
                onClick={() => onSelect(activity)}
                disabled={disabled}
              >
                <span className="activity-result-code">{activity.code}</span>
                <strong>{activity.name}</strong>
                <small>Раздел: {activity.section}</small>
              </button>
            )
          })
        ) : (
          <div className="empty-state shallow">
            {loading
              ? 'Ищем подходящие виды деятельности...'
              : hasSearch
                ? 'Ничего не найдено. Попробуйте код или другое ключевое слово.'
                : 'Справочник большой, начните вводить код или часть названия.'}
          </div>
        )}
      </div>

      <div className="activity-picker-footer">
        <p className="muted">
          {hasSearch
            ? `Найдено ${totalCount}. ${totalCount > options.length ? `Показаны первые ${options.length}. Уточните поиск, если нужно.` : 'Можно выбрать любой вариант из списка.'}`
            : 'Начните искать по коду или названию, чтобы быстро найти нужный вид деятельности.'}
        </p>
      </div>
    </div>
  )
}

export function TransactionForm({
  draft,
  setDraft,
  categories,
  activities,
  submitting,
  submitLabel,
  onSubmit,
}: {
  draft: TransactionDraft
  setDraft: (value: TransactionDraft) => void
  categories: Category[]
  activities: OrganizationActivity[]
  submitting: boolean
  submitLabel: string
  onSubmit: (event: FormEvent) => void
}) {
  const matchingCategories = getMatchingCategories(categories, draft.transaction_type as TransactionType)

  return (
    <form className="stack-sm" onSubmit={onSubmit}>
      <div className="field-grid two">
        <label className="field">
          <span>Тип</span>
          <select
            value={draft.transaction_type}
            onChange={(event) =>
              setDraft({
                ...draft,
                transaction_type: event.target.value as TransactionType,
                category: null,
              })
            }
          >
            <option value="income">Доход</option>
            <option value="expense">Расход</option>
          </select>
        </label>

        <label className="field">
          <span>Сумма</span>
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={draft.amount}
            onChange={(event) => setDraft({ ...draft, amount: event.target.value })}
            required
          />
        </label>

        <label className="field">
          <span>Дата</span>
          <input
            type="date"
            value={draft.transaction_date}
            onChange={(event) => setDraft({ ...draft, transaction_date: event.target.value })}
            required
          />
        </label>

        <label className="field">
          <span>Оплата</span>
          <select
            value={draft.payment_method}
            onChange={(event) =>
              setDraft({
                ...draft,
                payment_method: event.target.value as 'cash' | 'non_cash',
              })
            }
          >
            <option value="non_cash">Безналичный расчет</option>
            <option value="cash">Наличный расчет</option>
          </select>
        </label>

        <label className="field">
          <span>Категория</span>
          <select
            value={draft.category ?? ''}
            onChange={(event) =>
              setDraft({
                ...draft,
                category: event.target.value ? Number(event.target.value) : null,
              })
            }
          >
            <option value="">Без категории</option>
            {matchingCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>

        {draft.is_business ? (
          <label className="field">
            <span>Вид деятельности</span>
            <select
              value={draft.activity_code ?? ''}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  activity_code: event.target.value ? Number(event.target.value) : null,
                })
              }
              required={draft.is_business}
            >
              <option value="">Выберите вид деятельности</option>
              {activities.map((activity) => (
                <option key={activity.id} value={activity.activity}>
                  {getActivityLabel(activity)}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      <label className="field">
        <span>Описание</span>
        <textarea
          rows={3}
          value={draft.description}
          onChange={(event) => setDraft({ ...draft, description: event.target.value.slice(0, 100) })}
          placeholder="Краткое описание"
        />
      </label>

      <div className="toggle-row">
        <label className="check">
          <input
            type="checkbox"
            checked={draft.is_business}
            onChange={(event) =>
              setDraft({
                ...draft,
                is_business: event.target.checked,
                activity_code: event.target.checked ? draft.activity_code : null,
              })
            }
          />
          <span>Бизнес-операция</span>
        </label>

        <label className="check">
          <input
            type="checkbox"
            checked={draft.is_taxable}
            onChange={(event) => setDraft({ ...draft, is_taxable: event.target.checked })}
          />
          <span>Учитывать в налогах</span>
        </label>
      </div>

      <button type="submit" className="primary-button" disabled={submitting}>
        {submitting ? 'Сохранение...' : submitLabel}
      </button>
    </form>
  )
}
