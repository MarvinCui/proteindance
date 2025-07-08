/**
 * 错误处理和日志服务
 */

export interface ErrorLog {
  id: string
  timestamp: string
  level: 'error' | 'warn' | 'info' | 'debug'
  message: string
  stack?: string
  context?: any
  userAgent?: string
  url?: string
  userId?: string
}

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: any
}

class ErrorService {
  private logs: ErrorLog[] = []
  private maxLogs = 1000

  // 生成唯一ID
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  // 记录错误
  logError(error: Error | string, context?: any): void {
    const message = error instanceof Error ? error.message : error
    const stack = error instanceof Error ? error.stack : undefined
    
    const errorLog: ErrorLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      stack,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem('userId') || undefined
    }

    this.addLog(errorLog)
    
    // 控制台输出
    console.error('错误记录:', {
      message,
      stack,
      context,
      timestamp: errorLog.timestamp
    })
  }

  // 记录警告
  logWarning(message: string, context?: any): void {
    const warningLog: ErrorLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level: 'warn',
      message,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem('userId') || undefined
    }

    this.addLog(warningLog)
    console.warn('警告记录:', { message, context, timestamp: warningLog.timestamp })
  }

  // 记录信息
  logInfo(message: string, context?: any): void {
    const infoLog: ErrorLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level: 'info',
      message,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem('userId') || undefined
    }

    this.addLog(infoLog)
    console.info('信息记录:', { message, context, timestamp: infoLog.timestamp })
  }

  // 记录调试信息
  logDebug(message: string, context?: any): void {
    const debugLog: ErrorLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level: 'debug',
      message,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem('userId') || undefined
    }

    this.addLog(debugLog)
    console.debug('调试记录:', { message, context, timestamp: debugLog.timestamp })
  }

  // 添加日志到数组
  private addLog(log: ErrorLog): void {
    this.logs.push(log)
    
    // 限制日志数量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // 保存到localStorage
    this.saveToLocalStorage()
  }

  // 保存到localStorage
  private saveToLocalStorage(): void {
    try {
      const recentLogs = this.logs.slice(-100) // 只保存最近100条
      localStorage.setItem('errorLogs', JSON.stringify(recentLogs))
    } catch (error) {
      console.error('保存日志到localStorage失败:', error)
    }
  }

  // 从localStorage加载
  loadFromLocalStorage(): void {
    try {
      const saved = localStorage.getItem('errorLogs')
      if (saved) {
        const logs = JSON.parse(saved)
        this.logs = [...logs, ...this.logs]
      }
    } catch (error) {
      console.error('从localStorage加载日志失败:', error)
    }
  }

  // 获取所有日志
  getAllLogs(): ErrorLog[] {
    return [...this.logs]
  }

  // 获取特定级别的日志
  getLogsByLevel(level: ErrorLog['level']): ErrorLog[] {
    return this.logs.filter(log => log.level === level)
  }

  // 获取最近的日志
  getRecentLogs(count: number = 50): ErrorLog[] {
    return this.logs.slice(-count)
  }

  // 清空日志
  clearLogs(): void {
    this.logs = []
    localStorage.removeItem('errorLogs')
  }

  // 处理API错误
  handleApiError(error: any, context?: string): ApiError {
    let apiError: ApiError

    if (error.response) {
      // Axios错误响应
      apiError = {
        message: error.response.data?.message || error.response.data?.error || '服务器错误',
        status: error.response.status,
        code: error.response.data?.code,
        details: error.response.data
      }
    } else if (error.request) {
      // 网络错误
      apiError = {
        message: '网络连接失败，请检查网络连接',
        code: 'NETWORK_ERROR'
      }
    } else if (error.message) {
      // 其他错误
      apiError = {
        message: error.message,
        code: 'UNKNOWN_ERROR'
      }
    } else {
      // 未知错误
      apiError = {
        message: '未知错误',
        code: 'UNKNOWN_ERROR'
      }
    }

    // 记录错误
    this.logError(new Error(apiError.message), {
      context,
      apiError,
      originalError: error
    })

    return apiError
  }

  // 处理全局未捕获错误
  handleGlobalError(error: ErrorEvent): void {
    this.logError(new Error(error.message), {
      filename: error.filename,
      lineno: error.lineno,
      colno: error.colno,
      type: 'global'
    })
  }

  // 处理Promise拒绝
  handleUnhandledRejection(event: PromiseRejectionEvent): void {
    this.logError(new Error('Unhandled Promise Rejection'), {
      reason: event.reason,
      type: 'promise'
    })
  }

  // 导出日志
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  // 上传日志到服务器
  async uploadLogs(): Promise<void> {
    try {
      const logs = this.getLogsByLevel('error')
      if (logs.length === 0) return

      const response = await fetch('/api/logs/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logs)
      })

      if (response.ok) {
        this.logInfo('日志上传成功')
      } else {
        throw new Error('日志上传失败')
      }
    } catch (error) {
      console.error('日志上传失败:', error)
    }
  }
}

// 创建单例实例
const errorService = new ErrorService()

// 设置全局错误处理器
window.addEventListener('error', (event) => {
  errorService.handleGlobalError(event)
})

window.addEventListener('unhandledrejection', (event) => {
  errorService.handleUnhandledRejection(event)
})

// 从localStorage加载日志
errorService.loadFromLocalStorage()

export default errorService