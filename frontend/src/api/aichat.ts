import { apiRequest } from './client'

export function consultAi(message: string, sessionId: string) {
  return apiRequest<{ assistant: string; session_id: string }>('/aichat/consult/', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  })
}
