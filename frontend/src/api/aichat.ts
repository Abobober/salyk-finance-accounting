import { apiFetch } from './client'

/** POST /api/aichat/consult/ - AI-консультант */
export function aiConsult(message: string, sessionId: string) {
  return apiFetch<{ assistant: string; session_id: string }>('/aichat/consult/', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  })
}
