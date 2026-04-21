import type { FormEvent, ReactNode } from 'react'
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
