/**
 * 对话管理服务
 */
import authService from './authService'
import { getApiBaseUrl } from '../config/api-config'

export interface ConversationMessage {
  id: number
  message_type: 'user' | 'system'
  content: string
  disease_name?: string
  innovation_level?: number
  step?: number
  result_data?: any
  created_at: string
}

export interface ConversationSession {
  id: number
  title: string
  created_at: string
  updated_at: string
  is_active: boolean
  last_message?: {
    content: string
    created_at: string
    message_type: string
  }
}

export interface ConversationDetail {
  session: ConversationSession
  messages: ConversationMessage[]
}

class ConversationService {
  // 获取认证头
  private getHeaders() {
    return authService.getApiHeaders()
  }

  // 创建新对话
  async createConversation(title?: string): Promise<{ success: boolean; session?: ConversationSession; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ title: title || '新对话' })
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '创建对话失败'
      }
    }
  }

  // 获取对话列表
  async getConversations(limit: number = 50): Promise<{ success: boolean; sessions?: ConversationSession[]; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations?limit=${limit}`, {
        headers: this.getHeaders()
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '获取对话列表失败'
      }
    }
  }

  // 获取对话详情
  async getConversationDetail(sessionId: number): Promise<{ success: boolean; session?: ConversationSession; messages?: ConversationMessage[]; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations/${sessionId}`, {
        headers: this.getHeaders()
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '获取对话详情失败'
      }
    }
  }

  // 更新对话
  async updateConversation(sessionId: number, updates: { title?: string; is_active?: boolean }): Promise<{ success: boolean; session?: ConversationSession; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations/${sessionId}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(updates)
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '更新对话失败'
      }
    }
  }

  // 删除对话
  async deleteConversation(sessionId: number): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations/${sessionId}`, {
        method: 'DELETE',
        headers: this.getHeaders()
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '删除对话失败'
      }
    }
  }

  // 搜索对话
  async searchConversations(query: string, limit: number = 20): Promise<{ success: boolean; sessions?: ConversationSession[]; error?: string }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/conversations/search?q=${encodeURIComponent(query)}&limit=${limit}`, {
        headers: this.getHeaders()
      })

      const result = await response.json()
      return result
    } catch (error) {
      return {
        success: false,
        error: '搜索对话失败'
      }
    }
  }

  // 保存药物发现会话
  async saveDrugDiscoverySession(workflowData: any): Promise<{ success: boolean; session_id?: number; error?: string }> {
    try {
      // 首先创建一个新会话
      const createResult = await this.createConversation(`${workflowData.disease} - 药物发现`)
      
      if (!createResult.success || !createResult.session) {
        return {
          success: false,
          error: '创建会话失败'
        }
      }

      const sessionId = createResult.session.id

      // 然后保存工作流数据
      const response = await fetch(`${getApiBaseUrl()}/api/conversations/${sessionId}/save-workflow`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(workflowData)
      })

      const result = await response.json()
      
      if (result.success) {
        return {
          success: true,
          session_id: sessionId
        }
      } else {
        return result
      }
    } catch (error) {
      return {
        success: false,
        error: '保存药物发现会话失败'
      }
    }
  }

  // 格式化时间显示
  formatTime(timestamp: string): string {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffInSeconds < 60) {
      return '刚刚'
    } else if (diffInSeconds < 3600) {
      return `${Math.floor(diffInSeconds / 60)}分钟前`
    } else if (diffInSeconds < 86400) {
      return `${Math.floor(diffInSeconds / 3600)}小时前`
    } else if (diffInSeconds < 2592000) {
      return `${Math.floor(diffInSeconds / 86400)}天前`
    } else {
      return date.toLocaleDateString('zh-CN')
    }
  }

  // 截断长文本
  truncateText(text: string, maxLength: number = 100): string {
    if (text.length <= maxLength) {
      return text
    }
    return text.substring(0, maxLength) + '...'
  }
}

export const conversationService = new ConversationService()
export default conversationService