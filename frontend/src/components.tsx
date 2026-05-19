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
  const normalized = text.replace(/\r\n/g, '\n').replace(/[\u00A0\u202F\u2009]/g, ' ').trim()
  if (!normalized) return []

  type ParagraphBlock = { type: 'paragraph'; text: string }
  type ListBlock = { type: 'list'; items: string[] }
  type TableBlock =
    | { type: 'table'; variant: 'table'; headers: string[]; rows: string[][] }
    | { type: 'table'; variant: 'pre'; raw: string }

  type Block = ParagraphBlock | ListBlock | TableBlock

  const splitRowByPipes = (line: string) => {
    // Keep empty cells inside, but drop "padding" pipes at ends.
    const trimmed = line.trim()
    const noEdgePipe = trimmed.startsWith('|') && trimmed.endsWith('|') ? trimmed.slice(1, -1) : trimmed
    return noEdgePipe
      .split('|')
      .map((c) => c.trim())
      .filter((_, idx, arr) => !(idx === 0 && arr.length > 1 && arr[0] === '') && !(idx === arr.length - 1 && arr.length > 1 && arr[arr.length - 1] === ''))
  }

  const isPipeRow = (line: string) => {
    const pipeCount = (line.match(/\|/g) ?? []).length
    return pipeCount >= 2 && /[A-Za-zА-Яа-я0-9]/.test(line)
  }

  const isMarkdownSeparatorRow = (line: string) => {
    // | --- | :---: | --: |
    const trimmed = line.trim()
    const sepRe = /^(\|)?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+(\|)?$/
    return sepRe.test(trimmed)
  }

  const tryParsePipeTableFromLines = (lines: string[]) => {
    const pipeRows = lines.filter((l) => isPipeRow(l))
    if (pipeRows.length < 3) return null

    // If it's a real markdown table, try strict parsing.
    const first = lines.findIndex((l) => isPipeRow(l))
    if (first === -1) return null
    const headerLine = lines[first]
    const separatorLine = lines[first + 1] ?? ''
    if (isMarkdownSeparatorRow(separatorLine)) {
      const headers = splitRowByPipes(headerLine)
      const bodyLines = []
      for (let i = first + 2; i < lines.length; i++) {
        const l = lines[i]
        if (!isPipeRow(l)) break
        bodyLines.push(l)
      }
      const maxCols = Math.max(headers.length, ...bodyLines.map((l) => splitRowByPipes(l).length))
      const normalizedHeaders = [...headers]
      while (normalizedHeaders.length < maxCols) normalizedHeaders.push('')

      const rows = bodyLines.map((l) => {
        const cells = splitRowByPipes(l)
        while (cells.length < maxCols) cells.push('')
        return cells
      })

      if (rows.length < 1) return null
      return { variant: 'table' as const, headers: normalizedHeaders, rows }
    }

    // Best-effort: assume "first row is header" even if separator is missing.
    const allRows = pipeRows.slice(0, Math.min(pipeRows.length, 40))
    const parsed = allRows.map((l) => splitRowByPipes(l))
    const maxCols = Math.max(...parsed.map((r) => r.length))
    if (maxCols < 2) return null

    const headers = parsed[0].slice(0, maxCols)
    while (headers.length < maxCols) headers.push('')

    const rows = parsed.slice(1).map((r) => {
      const cells = r.slice(0, maxCols)
      while (cells.length < maxCols) cells.push('')
      return cells
    })

    if (!rows.length) return null
    return { variant: 'table' as const, headers, rows }
  }

  const tryParseSpaceTableFromLines = (lines: string[]) => {
    const candidateRows = lines
      .map((l) => l.trim())
      .filter((l) => {
        if (l.length < 3) return false
        if (l.includes('|')) return false
        // Heuristic: at least 2 spaces split into "columns".
        const parts = l.split(/\s{2,}/g).filter(Boolean)
        return parts.length >= 2 && parts.length <= 8 && /[A-Za-zА-Яа-я0-9]/.test(l)
      })

    if (candidateRows.length < 3) return null

    const parsed = candidateRows.slice(0, 40).map((l) => l.split(/\s{2,}/g).filter(Boolean))
    const lens = parsed.map((r) => r.length).sort((a, b) => a - b)
    const median = lens[Math.floor(lens.length / 2)] ?? 0
    if (!median || lens.some((len) => Math.abs(len - median) > 1)) {
      // Too inconsistent: treat as a raw pre.
      return { variant: 'pre' as const, raw: lines.join('\n') }
    }

    const maxCols = Math.max(...parsed.map((r) => r.length))
    const headers = parsed[0].slice(0, maxCols)
    while (headers.length < maxCols) headers.push('')
    const rows = parsed.slice(1).map((r) => {
      const cells = r.slice(0, maxCols)
      while (cells.length < maxCols) cells.push('')
      return cells
    })

    if (!rows.length) return null
    return { variant: 'table' as const, headers, rows }
  }

  const tryParseTableBlock = (blockText: string): TableBlock | null => {
    const lines = blockText
      .replace(/\r\n/g, '\n')
      .split('\n')
      .map((l) => l.trimEnd())
      .filter(Boolean)

    if (lines.length < 3) return null

    const pipeTable = tryParsePipeTableFromLines(lines)
    if (pipeTable && pipeTable.variant === 'table') {
      return { type: 'table', variant: 'table', headers: pipeTable.headers, rows: pipeTable.rows }
    }

    const spaceTable = tryParseSpaceTableFromLines(lines)
    if (spaceTable) {
      if (spaceTable.variant === 'pre') return { type: 'table', variant: 'pre', raw: spaceTable.raw }
      return { type: 'table', variant: 'table', headers: spaceTable.headers, rows: spaceTable.rows }
    }

    // As a last resort, if it still "looks like" a table but isn't parseable, show as pre.
    const pipeLikeLines = lines.filter((l) => isPipeRow(l))
    if (pipeLikeLines.length >= 3) {
      return { type: 'table', variant: 'pre', raw: lines.join('\n') }
    }

    return null
  }

  // If the model returns a single-line "Вывод: ... Риски: ... Рекомендации: ...",
  // try to split by known headings first.
  const headingRe = /(Вывод|Итог|Риски|Рекомендации)\s*[:\-–—]\s*/gi
  const headingMatches: Array<{ heading: string; index: number; matchLen: number }> = []

  for (const match of normalized.matchAll(headingRe)) {
    if (typeof match.index === 'number') {
      headingMatches.push({ heading: match[1], index: match.index, matchLen: match[0].length })
    }
  }

  if (headingMatches.length) {
    const blocks: Block[] = []

    for (let i = 0; i < headingMatches.length; i++) {
      const { heading, index, matchLen } = headingMatches[i]
      const nextIndex = i + 1 < headingMatches.length ? headingMatches[i + 1].index : normalized.length
      const content = normalized.slice(index + matchLen, nextIndex).trim()
      if (!content) continue

      const tableBlock = tryParseTableBlock(content)
      if (tableBlock) {
        blocks.push({ type: 'paragraph', text: `${heading}:` })
        blocks.push(tableBlock)
        continue
      }

      // Heuristic: treat as a list if there are many bullet markers inside the section.
      const markerCount = (content.match(/(?:^|\s)(?:[-*\u2022]|\d+[.)])\s+/g) ?? []).length
      const items =
        markerCount >= 2
          ? content
              .split(/(?:^|\s)(?:[-*\u2022]|\d+[.)])\s+/g)
              .map((s) => s.trim())
              .filter((s) => s.length > 0)
          : []

      if (items.length >= 2) {
        blocks.push({ type: 'paragraph', text: `${heading}:` })
        blocks.push({ type: 'list', items })
      } else {
        blocks.push({ type: 'paragraph', text: `${heading}: ${content}` })
      }
    }

    return blocks
  }

  // Default mode: line-based parsing into paragraphs/lists.
  const blocks: Block[] = []
  let paragraph: string[] = []
  let list: string[] = []

  const flushParagraph = () => {
    if (!paragraph.length) return
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') })
    paragraph = []
  }

  const flushList = () => {
    if (!list.length) return
    blocks.push({ type: 'list', items: list })
    list = []
  }

  const lines = normalized.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]
    const line = rawLine.trim()

    if (!line) {
      flushParagraph()
      flushList()
      continue
    }

    // Try to detect table-like blocks first.
    const lookahead: string[] = []
    let j = i
    while (j < lines.length && lookahead.length < 60 && lines[j].trim()) {
      lookahead.push(lines[j])
      j++
    }

    const possibleTable = tryParseTableBlock(lookahead.join('\n'))
    if (possibleTable) {
      flushParagraph()
      flushList()
      blocks.push(possibleTable)
      i = j - 1
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
        ) : block.type === 'table' ? (
          block.variant === 'pre' ? (
            <pre key={`table-pre-${index}`} className="chat-table-pre">
              {block.raw}
            </pre>
          ) : (
            <div key={`table-${index}`} className="chat-table-wrap">
              <table className="chat-data-table">
                <thead>
                  <tr>
                    {block.headers.map((h, hIdx) => (
                      <th key={`th-${index}-${hIdx}`}>{renderInlineText(h)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rIdx) => (
                    <tr key={`tr-${index}-${rIdx}`}>
                      {row.map((cell, cIdx) => (
                        <td key={`td-${index}-${rIdx}-${cIdx}`}>{renderInlineText(cell)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
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
            required
          >
            <option value="">Выберите вид деятельности</option>
            {activities.map((activity) => (
              <option key={activity.id} value={activity.activity}>
                {getActivityLabel(activity)}
              </option>
            ))}
          </select>
        </label>
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
