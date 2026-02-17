import { useState, useRef, useEffect } from 'react'
import { aiConsult } from '@/api/aichat'
import '@/styles/layout.css'
import '@/styles/login.css'

function genSessionId() {
  return 'sess_' + Date.now().toString(36) + Math.random().toString(36).slice(2)
}

export function AiChatPage() {
  const [sessionId] = useState(() => genSessionId())
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', text }])
    setLoading(true)
    try {
      const res = await aiConsult(text, sessionId)
      setMessages((prev) => [...prev, { role: 'assistant', text: res.assistant }])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1 className="main-title">AI-консультант</h1>
      <p className="main-subtitle">Бухгалтерские вопросы по законодательству КР</p>

      {error && <p className="login-error" style={{ marginBottom: 16 }}>{error}</p>}

      <div className="main-card" style={{ display: 'flex', flexDirection: 'column', minHeight: 400, maxHeight: 600 }}>
        <div style={{ flex: 1, overflow: 'auto', paddingBottom: 16 }}>
          {messages.length === 0 && (
            <p style={{ color: 'var(--color-text-muted)', fontSize: 14 }}>
              Задайте вопрос по налогам, отчётности, ИП или ОсОО.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                marginBottom: 12,
                padding: 12,
                background: m.role === 'user' ? 'var(--color-bg)' : '#f0f4f8',
                border: '1px solid var(--color-border)',
                borderRadius: 2,
                whiteSpace: 'pre-wrap',
                fontSize: 14,
              }}
            >
              <strong style={{ color: 'var(--color-primary)', fontSize: 12 }}>{m.role === 'user' ? 'Вы' : 'Консультант'}</strong>
              <div style={{ marginTop: 6 }}>{m.text}</div>
            </div>
          ))}
          {loading && (
            <div style={{ padding: 12, color: 'var(--color-text-muted)', fontSize: 14 }}>Ответ формируется…</div>
          )}
          <div ref={bottomRef} />
        </div>
        <form
          onSubmit={(e) => { e.preventDefault(); send() }}
          style={{ display: 'flex', gap: 8, marginTop: 16, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Введите вопрос…"
            className="login-field"
            style={{ flex: 1, padding: 10 }}
          />
          <button type="submit" className="login-submit" disabled={loading}>
            Отправить
          </button>
        </form>
      </div>
    </>
  )
}
