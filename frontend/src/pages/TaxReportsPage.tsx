import { FormEvent, useState } from 'react'
import { generateUnifiedTaxReport, type UnifiedTaxReportResponse } from '@/api/taxReports'
import '@/styles/layout.css'
import '@/styles/login.css'

export function TaxReportsPage() {
  const currentYear = new Date().getFullYear()
  const [year, setYear] = useState(currentYear)
  const [quarter, setQuarter] = useState<1 | 2 | 3 | 4>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UnifiedTaxReportResponse | null>(null)

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await generateUnifiedTaxReport({ year, quarter })
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка генерации отчета')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1 className="main-title">Отчеты</h1>
      <p className="main-subtitle">Формирование единого налогового отчета</p>

      {error && (
        <p className="login-error" style={{ marginBottom: 16 }}>
          {error}
        </p>
      )}

      <div className="main-card" style={{ marginBottom: 24 }}>
        <h2 className="main-card-title">Сформировать отчет</h2>
        <form onSubmit={handleGenerate} className="login-form">
          <div className="form-row">
            <div className="login-field">
              <label>Год</label>
              <input
                type="number"
                min={2000}
                max={2100}
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                required
              />
            </div>
            <div className="login-field">
              <label>Квартал</label>
              <select
                className="select-field"
                value={quarter}
                onChange={(e) => setQuarter(Number(e.target.value) as 1 | 2 | 3 | 4)}
              >
                <option value={1}>1 квартал</option>
                <option value={2}>2 квартал</option>
                <option value={3}>3 квартал</option>
                <option value={4}>4 квартал</option>
              </select>
            </div>
          </div>
          <button type="submit" className="login-submit" disabled={loading}>
            {loading ? 'Формирование...' : 'Сформировать'}
          </button>
        </form>
      </div>

      {result && (
        <>
          <div className="main-card" style={{ marginBottom: 16 }}>
            <h2 className="main-card-title">PDF файл</h2>
            <a href={result.pdf_file} target="_blank" rel="noreferrer">
              Скачать отчет
            </a>
          </div>

          <div className="main-card" style={{ marginBottom: 16 }}>
            <h2 className="main-card-title">AI валидация</h2>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{result.ai_validation}</p>
          </div>

          <div className="main-card">
            <h2 className="main-card-title">Данные отчета</h2>
            <pre style={{ margin: 0, overflowX: 'auto' }}>
              {JSON.stringify(result.report_data, null, 2)}
            </pre>
          </div>
        </>
      )}
    </>
  )
}
