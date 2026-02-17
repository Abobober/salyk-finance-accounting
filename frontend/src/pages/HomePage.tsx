import { Link } from 'react-router-dom'
import '@/styles/layout.css'

const cardLinkStyle = { textDecoration: 'none', color: 'inherit' } as const

export function HomePage() {
  return (
    <>
      <h1 className="main-title">Главная</h1>
      <p className="main-subtitle">
        Система финансового учета для индивидуальных предпринимателей.
      </p>

      <div className="main-grid">
        <Link to="/transactions" className="main-card" style={cardLinkStyle}>
          <h2 className="main-card-title">Операции</h2>
          <p className="main-card-desc">
            Учет доходов и расходов, категоризация операций.
          </p>
        </Link>

        <Link to="/reports" className="main-card" style={cardLinkStyle}>
          <h2 className="main-card-title">Отчеты</h2>
          <p className="main-card-desc">
            Формирование отчетности для налоговых органов.
          </p>
        </Link>

        <Link to="/categories" className="main-card" style={cardLinkStyle}>
          <h2 className="main-card-title">Категории</h2>
          <p className="main-card-desc">
            Справочник категорий доходов и расходов.
          </p>
        </Link>

        <Link to="/aichat" className="main-card" style={cardLinkStyle}>
          <h2 className="main-card-title">AI-консультант</h2>
          <p className="main-card-desc">
            Вопросы по бухгалтерии и налогам КР.
          </p>
        </Link>
      </div>
    </>
  )
}
