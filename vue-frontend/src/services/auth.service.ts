import { apiService } from './api'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
}

export interface AuthResponse {
  success: boolean
  access_token?: string
  refresh_token?: string
  user?: any
  error?: string
  message?: string
}

export class AuthService {
  async login(username: string, password: string): Promise<AuthResponse> {
    return apiService.post<AuthResponse>('/api/auth/login', { username, password })
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    return apiService.post<AuthResponse>('/api/auth/register', data)
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return apiService.post<AuthResponse>('/api/auth/refresh', { refresh_token: refreshToken })
  }

  async getCurrentUser(): Promise<any> {
    return apiService.get('/api/auth/me')
  }

  async verifyToken(token: string): Promise<{ valid: boolean }> {
    try {
      const response = await apiService.post<{ valid: boolean }>('/api/auth/verify', { token })
      return response
    } catch {
      return { valid: false }
    }
  }

  async logout(): Promise<void> {
    try {
      await apiService.post('/api/auth/logout')
    } finally {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
    }
  }
}

export const authService = new AuthService()

