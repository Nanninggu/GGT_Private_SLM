import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService, type LoginRequest, type RegisterRequest } from '@/services/auth.service'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<any>(JSON.parse(localStorage.getItem('user_info') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials: LoginRequest) {
    try {
      const response = await authService.login(credentials.username, credentials.password)
      if (response.success && response.access_token) {
        token.value = response.access_token
        refreshToken.value = response.refresh_token || null
        user.value = response.user || null

        localStorage.setItem('auth_token', response.access_token)
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token)
        }
        if (response.user) {
          localStorage.setItem('user_info', JSON.stringify(response.user))
        }

        return { success: true }
      }
      return { success: false, error: response.error || response.message }
    } catch (error: any) {
      return { success: false, error: error.message || '로그인에 실패했습니다.' }
    }
  }

  async function register(data: RegisterRequest) {
    try {
      const response = await authService.register(data)
      if (response.success && response.access_token) {
        token.value = response.access_token
        refreshToken.value = response.refresh_token || null
        user.value = response.user || null

        localStorage.setItem('auth_token', response.access_token)
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token)
        }
        if (response.user) {
          localStorage.setItem('user_info', JSON.stringify(response.user))
        }

        return { success: true }
      }
      return { success: false, error: response.error || response.message }
    } catch (error: any) {
      return { success: false, error: error.message || '회원가입에 실패했습니다.' }
    }
  }

  async function logout() {
    try {
      await authService.logout()
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      router.push('/login')
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      await logout()
      return false
    }

    try {
      const response = await authService.refreshToken(refreshToken.value)
      if (response.success && response.access_token) {
        token.value = response.access_token
        if (response.refresh_token) {
          refreshToken.value = response.refresh_token
        }
        localStorage.setItem('auth_token', response.access_token)
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token)
        }
        return true
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
    }

    await logout()
    return false
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    refreshAccessToken,
  }
})

