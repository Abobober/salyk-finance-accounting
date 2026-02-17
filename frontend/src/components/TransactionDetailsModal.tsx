import { useState } from 'react'
import type { Transaction } from '@/api/finance'
import { deleteTransaction } from '@/api/finance'
import { Modal } from './Modal'

interface TransactionDetailsModalProps {
  transaction: Transaction | null
  isOpen: boolean
  onClose: () => void
  onDeleted?: () => void
}

export function TransactionDetailsModal({ transaction, isOpen, onClose, onDeleted }: TransactionDetailsModalProps) {
  const [deleting, setDeleting] = useState(false)
  if (!transaction) return null
  const t = transaction

  const handleDelete = async () => {
    if (!confirm('Удалить эту транзакцию?')) return
    setDeleting(true)
    try {
      await deleteTransaction(t.id)
      onClose()
      onDeleted?.()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Детали операции">
      <dl className="transaction-details">
        <div className="detail-row">
          <dt>Дата</dt>
          <dd>{t.transaction_date}</dd>
        </div>
        <div className="detail-row">
          <dt>Тип</dt>
          <dd>{t.transaction_type === 'income' ? 'Доход' : 'Расход'}</dd>
        </div>
        <div className="detail-row">
          <dt>Сумма</dt>
          <dd>{t.amount}</dd>
        </div>
        <div className="detail-row">
          <dt>Способ оплаты</dt>
          <dd>{t.payment_method === 'cash' ? 'Наличный' : 'Безналичный'}</dd>
        </div>
        <div className="detail-row">
          <dt>Категория</dt>
          <dd>{t.category_name || '—'}</dd>
        </div>
        <div className="detail-row">
          <dt>Описание</dt>
          <dd>{t.description || '—'}</dd>
        </div>
        <div className="detail-row">
          <dt>Бизнес</dt>
          <dd>{t.is_business ? 'Да' : 'Нет'}</dd>
        </div>
        <div className="detail-row">
          <dt>Учитывается в налоговой базе</dt>
          <dd>{t.is_taxable ? 'Да' : 'Нет'}</dd>
        </div>
        {t.activity_code_name && (
          <div className="detail-row">
            <dt>Вид деятельности</dt>
            <dd>{t.activity_code_name}</dd>
          </div>
        )}
        {(t.cash_tax_rate != null || t.non_cash_tax_rate != null) && (
          <div className="detail-row">
            <dt>Ставки налога</dt>
            <dd>
              наличные: {t.cash_tax_rate ?? '—'}% / безнал: {t.non_cash_tax_rate ?? '—'}%
            </dd>
          </div>
        )}
        <div className="detail-row">
          <dt>Создано</dt>
          <dd>{new Date(t.created_at).toLocaleString('ru')}</dd>
        </div>
      </dl>
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
        <button
          type="button"
          className="btn-sm danger"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? 'Удаление…' : 'Удалить'}
        </button>
      </div>
    </Modal>
  )
}
