import { Link } from 'react-router-dom'
import '@/styles/layout.css'

export function HomePage() {
  return (
    <>
      <h1 className="main-title">Главная</h1>
      <p className="main-subtitle">
        Система финансового учёта для индивидуальных предпринимателей.
      </p>

      <div className="main-grid">
        <Link to="/transactions" className="main-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h2 className="main-card-title">Операции</h2>
          <p className="main-card-desc">
            Учёт доходов и расходов, категоризация операций.
          </p>
        </Link>
        <div className="main-card">
          <h2 className="main-card-title">Отчёты</h2>
          <p className="main-card-desc">
            Формирование отчётности для налоговых органов.
          </p>
        </div>
        <Link to="/categories" className="main-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h2 className="main-card-title">Категории</h2>
          <p className="main-card-desc">
            Справочник категорий доходов и расходов.
          </p>
        </Link>
        <Link to="/aichat" className="main-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h2 className="main-card-title">AI-консультант</h2>
          <p className="main-card-desc">
            Вопросы по бухгалтерии и налогам КР.
          </p>
        </Link>
      </div>
    </>
  )
}
