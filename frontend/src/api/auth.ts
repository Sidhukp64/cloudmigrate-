import { api } from './client'

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    role: 'admin' | 'operator' | 'viewer'
    is_active: boolean
    created_at: string
  }
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { email, password }).then((r) => r.data),

  me: () =>
    api.get<LoginResponse['user']>('/auth/me').then((r) => r.data),
}
