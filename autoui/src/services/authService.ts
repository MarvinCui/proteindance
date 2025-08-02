/**
 * 用户认证服务
 */
import { getApiBaseUrl } from '../config/api-config'

export interface User {
  id: number
  email: string
  username: string
  status: string
  email_verified: boolean
  created_at?: string
  last_login?: string
}

export interface AuthResponse {
  success: boolean
  message?: string
  user?: User
  token?: string
  requires_verification?: boolean
  auto_activated?: boolean
  error?: string
  error_code?: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
}

export interface LoginData {
  email: string
  password: string
}

class AuthService {
  private token: string | null = null
  private user: User | null = null

  constructor() {
    this.token = localStorage.getItem('auth_token')
    const userData = localStorage.getItem('user_data')
    if (userData) {
      try {
        this.user = JSON.parse(userData)
      } catch (e) {
        localStorage.removeItem('user_data')
      }
    }
  }

  // 设置认证头
  private getAuthHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    
    return headers
  }

  // 保存认证信息
  private saveAuthInfo(token: string, user: User) {
    this.token = token
    this.user = user
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_data', JSON.stringify(user))
  }

  // 清除认证信息
  private clearAuthInfo() {
    this.token = null
    this.user = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!this.token && !!this.user
  }

  // 获取当前用户
  getCurrentUser(): User | null {
    return this.user
  }

  // 获取认证令牌
  getToken(): string | null {
    return this.token
  }

  // 用户注册
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '注册请求失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 用户登录
  async login(data: LoginData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      const result = await response.json()
      
      if (result.success && result.token && result.user) {
        this.saveAuthInfo(result.token, result.user)
      }
      
      return result
    } catch (error) {
      return {
        success: false,
        error: '登录请求失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 用户登出
  logout() {
    this.clearAuthInfo()
    // 不要重定向，让组件处理UI状态
  }

  // 验证邮箱
  async verifyEmail(token: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/verify-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
      })

      return await response.json()
    } catch (error) {
      return {
        success: false,
        error: '邮箱验证请求失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 请求密码重置
  async requestPasswordReset(email: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/request-password-reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      })

      return await response.json()
    } catch (error) {
      return {
        success: false,
        error: '密码重置请求失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 重置密码
  async resetPassword(token: string, newPassword: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          token,
          new_password: newPassword
        })
      })

      return await response.json()
    } catch (error) {
      return {
        success: false,
        error: '密码重置失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 获取当前用户信息
  async getCurrentUserInfo(): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
        headers: this.getAuthHeaders()
      })

      const result = await response.json()
      
      if (result.success && result.user) {
        this.user = result.user
        localStorage.setItem('user_data', JSON.stringify(result.user))
      }
      
      return result
    } catch (error) {
      return {
        success: false,
        error: '获取用户信息失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 重新发送验证邮件
  async resendVerificationEmail(): Promise<AuthResponse> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/resend-verification`, {
        method: 'POST',
        headers: this.getAuthHeaders()
      })

      return await response.json()
    } catch (error) {
      return {
        success: false,
        error: '重新发送验证邮件失败',
        error_code: 'NETWORK_ERROR'
      }
    }
  }

  // 为API请求添加认证头
  getApiHeaders(): Record<string, string> {
    return this.getAuthHeaders()
  }
}

export const authService = new AuthService()
export default authService