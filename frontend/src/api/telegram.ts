import { apiFetch } from './client'

/** GET /api/telegram/link-token/ - получить ссылку для привязки Telegram */
export function getTelegramLinkToken() {
  return apiFetch<{ link: string }>('/telegram/link-token/')
}
