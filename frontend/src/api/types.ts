/**
 * API types - regenerate with: npm run generate:api
 * (Backend must be running: python manage.py runserver)
 *
 * If schema is at /api/schema/ (drf-spectacular), update package.json script.
 * Current: drf-yasg schema at /swagger.json/
 */

/** JWT Token pair from POST /api/token/ */
export interface TokenPair {
  access: string
  refresh: string
}

/** Login request body - email as USERNAME_FIELD */
export interface LoginRequest {
  email: string
  password: string
}

/** Register request - POST /api/users/register/ */
export interface RegisterRequest {
  email: string
  password: string
  password2: string
  first_name?: string
  last_name?: string
}

/** User profile from /api/users/me/ */
export interface UserProfile {
  id: number
  email: string
  first_name: string
  last_name: string
  telegram_id: string | null
  date_joined: string
}
