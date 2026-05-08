import { apiRequest } from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  password2: string
  first_name?: string
  last_name?: string
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface UserProfile {
  id: number
  email: string
  first_name: string
  last_name: string
  telegram_id: string | null
  date_joined: string
}

export function login(data: LoginRequest) {
  return apiRequest<TokenPair>('/token/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function register(data: RegisterRequest) {
  return apiRequest<{ message: string }>('/users/register/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getCurrentUser() {
  return apiRequest<UserProfile>('/users/me/')
}

export function updateProfile(data: Partial<Pick<UserProfile, 'email' | 'first_name' | 'last_name'>>) {
  return apiRequest<UserProfile>('/users/profile/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function logout(refresh: string) {
  return apiRequest<void>('/users/logout/', {
    method: 'POST',
    body: JSON.stringify({ refresh }),
  })
}
