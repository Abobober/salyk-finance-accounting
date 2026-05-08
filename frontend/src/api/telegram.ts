import { apiRequest } from './client'

export function getTelegramLinkToken() {
  return apiRequest<{ link: string }>('/telegram/link-token/')
}
