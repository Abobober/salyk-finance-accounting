import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  listTransactions,
  getDashboard,
  getTimeSeries,
  getCategoryBreakdown,
  type Transaction,
  type TimeSeriesPoint,
  type CategoryBreakdownItem,
} from '@/api/finance'
import { Modal } from '@/components/Modal'
import { AddTransactionModal } from '@/components/AddTransactionModal'
import { TransactionDetailsModal } from '@/components/TransactionDetailsModal'
import '@/styles/layout.css'

type ChartView = 'line' | 'bar' | 'pie'

const CHART_COLORS = ['#22c55e', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']

export function DashboardPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [dashboardTotals, setDashboardTotals] = useState<{ total_income: string; total_expense: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [addTxOpen, setAddTxOpen] = useState(false)
  const [detailTx, setDetailTx] = useState<Transaction | null>(null)
  const [chartView, setChartView] = useState<ChartView>('line')
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesPoint[]>([])
  const [categoryData, setCategoryData] = useState<CategoryBreakdownItem[]>([])
  const [chartLoading, setChartLoading] = useState(true)
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    transaction_type: '',
    category: '',
  })

  const loadTransactions = () => {
    setLoading(true)
    const params: Record<string, string> = {}
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    if (filters.transaction_type) params.transaction_type = filters.transaction_type
    if (filters.category) params.category = filters.category
    listTransactions(params)
      .then(setTransactions)
      .finally(() => setLoading(false))
    loadDashboard()
  }

  const loadDashboard = () => {
    getDashboard()
      .then((d) => setDashboardTotals(d.totals))
      .catch(() => setDashboardTotals(null))
  }

  const loadChart = () => {
    setChartLoading(true)
    const params: { preset?: 'month' | 'year'; date_from?: string; date_to?: string } = {}
    if (filters.date_from || filters.date_to) {
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
    } else {
      params.preset = 'year'
    }
    Promise.all([
      getTimeSeries({ ...params, period: 'monthly' }),
      getCategoryBreakdown({ ...params, limit: 8 }),
    ])
      .then(([ts, cb]) => {
        // Убеждаемся, что income и expense есть в каждом элементе
        const safeTsData = (ts.data || []).map((d) => ({
          period: d.period,
          income: String(d.income ?? '0'),
          expense: String(d.expense ?? '0'),
          net: d.net ?? '0',
        }))
        setTimeSeriesData(safeTsData)
        setCategoryData(cb.data || [])
      })
      .catch(() => {
        setTimeSeriesData([])
        setCategoryData([])
      })
      .finally(() => setChartLoading(false))
  }

  useEffect(() => {
    loadTransactions()
  }, [filters.date_from, filters.date_to, filters.transaction_type, filters.category])

  useEffect(() => {
    loadDashboard()
  }, [])

  useEffect(() => {
    loadChart()
  }, [filters.date_from, filters.date_to])

  return (
    <>
      <div className="dashboard-header">
        <div>
          <h1 className="main-title">Дэшборд</h1>
          <p className="main-subtitle">Операции</p>
          {dashboardTotals && (
            <div className="dashboard-totals">
              <span>Доходы: {dashboardTotals.total_income}</span>
              <span>Расходы: {dashboardTotals.total_expense}</span>
            </div>
          )}
        </div>
        <button type="button" className="login-submit" onClick={() => setAddTxOpen(true)}>
          + Добавить операцию
        </button>
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-section dashboard-section-main">
          <div className="main-card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
              <h2 className="main-card-title" style={{ margin: 0 }}>График</h2>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  className={`btn-sm ${chartView === 'line' ? 'chart-btn-active' : ''}`}
                  onClick={() => setChartView('line')}
                >
                  Линейный
                </button>
                <button
                  type="button"
                  className={`btn-sm ${chartView === 'bar' ? 'chart-btn-active' : ''}`}
                  onClick={() => setChartView('bar')}
                >
                  Столбцы
                </button>
                <button
                  type="button"
                  className={`btn-sm ${chartView === 'pie' ? 'chart-btn-active' : ''}`}
                  onClick={() => setChartView('pie')}
                >
                  Круговая
                </button>
              </div>
            </div>
            {chartLoading ? (
              <p>Загрузка графика…</p>
            ) : chartView === 'pie' ? (
              categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={categoryData.map((d) => ({ name: d.category_name, value: parseFloat(d.total) }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    >
                      {categoryData.map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => `${Number(v ?? 0).toFixed(2)} сом`} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p style={{ color: 'var(--color-text-muted)', padding: 24 }}>Нет данных за период</p>
              )
            ) : timeSeriesData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                {chartView === 'line' ? (
                  <LineChart data={timeSeriesData.map((d) => ({ ...d, income: parseFloat(d.income || '0'), expense: parseFloat(d.expense || '0') }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="period" stroke="var(--color-text-muted)" fontSize={12} />
                    <YAxis stroke="var(--color-text-muted)" fontSize={12} tickFormatter={(v) => `${v}`} domain={[0, 'auto']} />
                    <Tooltip formatter={(v) => [`${Number(v ?? 0).toFixed(2)} сом`, '']} />
                    <Legend />
                    <Line type="monotone" dataKey="income" name="Доходы" stroke="#22c55e" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                    <Line type="monotone" dataKey="expense" name="Расходы" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                  </LineChart>
                ) : (
                  <BarChart data={timeSeriesData.map((d) => ({ ...d, income: parseFloat(d.income || '0'), expense: parseFloat(d.expense || '0') }))} barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="period" stroke="var(--color-text-muted)" fontSize={12} />
                    <YAxis stroke="var(--color-text-muted)" fontSize={12} tickFormatter={(v) => `${v}`} domain={[0, 'auto']} />
                    <Tooltip formatter={(v) => [`${Number(v ?? 0).toFixed(2)} сом`, '']} />
                    <Legend />
                    <Bar dataKey="income" name="Доходы" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expense" name="Расходы" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                )}
              </ResponsiveContainer>
            ) : (
              <p style={{ color: 'var(--color-text-muted)', padding: 24 }}>Нет данных за период</p>
            )}
          </div>

          <div className="main-card" style={{ marginBottom: 16 }}>
            <h2 className="main-card-title">Фильтры</h2>
            <div className="form-row">
              <div className="login-field">
                <label>Дата с</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))}
                />
              </div>
              <div className="login-field">
                <label>Дата по</label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))}
                />
              </div>
              <div className="login-field">
                <label>Тип</label>
                <select
                  className="select-field"
                  value={filters.transaction_type}
                  onChange={(e) => setFilters((p) => ({ ...p, transaction_type: e.target.value }))}
                >
                  <option value="">Все</option>
                  <option value="income">Доход</option>
                  <option value="expense">Расход</option>
                </select>
              </div>
            </div>
          </div>

          <div className="main-card">
            <h2 className="main-card-title">Операции</h2>
            {loading ? (
              <p>Загрузка…</p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Дата</th>
                      <th>Тип</th>
                      <th>Сумма</th>
                      <th>Категория</th>
                      <th>Способ</th>
                      <th>Описание</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((t) => (
                      <tr
                        key={t.id}
                        className="transaction-row-clickable"
                        onClick={() => setDetailTx(t)}
                      >
                        <td>{t.transaction_date}</td>
                        <td>{t.transaction_type === 'income' ? 'Доход' : 'Расход'}</td>
                        <td>{t.amount}</td>
                        <td>{t.category_name || '—'}</td>
                        <td>{t.payment_method === 'cash' ? 'Наличный' : 'Безнал'}</td>
                        <td>{t.description || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <aside className="dashboard-sidebar">
          <div className="main-card">
            <h2 className="main-card-title">AI-консультант</h2>
            <p className="main-card-desc">Вопросы по налогам и отчётности</p>
            <Link to="/aichat" className="btn-sm" style={{ display: 'inline-block', marginTop: 8 }}>
              Открыть чат
            </Link>
          </div>
        </aside>
      </div>

      <Modal isOpen={addTxOpen} onClose={() => setAddTxOpen(false)} title="Добавить операцию">
        <AddTransactionModal
          isOpen={addTxOpen}
          onClose={() => setAddTxOpen(false)}
          onSuccess={() => {
            loadTransactions()
            loadChart()
          }}
        />
      </Modal>

      <TransactionDetailsModal
        transaction={detailTx}
        isOpen={!!detailTx}
        onClose={() => setDetailTx(null)}
        onDeleted={() => {
          loadTransactions()
          loadChart()
        }}
      />
    </>
  )
}
