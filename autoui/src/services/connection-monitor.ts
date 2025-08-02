// 连接监控服务
import { apiConfigManager } from '../config/api-config';

export class ConnectionMonitor {
  private isMonitoring = false;
  private checkInterval: number | null = null;
  private callbacks: Set<(status: ConnectionStatus) => void> = new Set();
  private lastStatus: ConnectionStatus | null = null;

  public async startMonitoring(intervalMs: number = 30000): Promise<void> {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    console.log('🔍 开始监控后端连接状态...');

    // 立即检查一次
    await this.checkConnection();

    // 设置定期检查
    this.checkInterval = window.setInterval(async () => {
      await this.checkConnection();
    }, intervalMs);
  }

  public stopMonitoring(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.isMonitoring = false;
    console.log('⏹️  停止监控后端连接状态');
  }

  public onStatusChange(callback: (status: ConnectionStatus) => void): () => void {
    this.callbacks.add(callback);
    
    // 如果有上次的状态，立即调用回调
    if (this.lastStatus) {
      callback(this.lastStatus);
    }

    // 返回取消监听函数
    return () => {
      this.callbacks.delete(callback);
    };
  }

  private async checkConnection(): Promise<void> {
    try {
      const healthStatus = await apiConfigManager.getHealthStatus();
      const newStatus: ConnectionStatus = {
        connected: healthStatus.healthy,
        message: healthStatus.message,
        config: healthStatus.config,
        timestamp: Date.now(),
        autoDetected: false
      };

      // 如果连接失败，尝试自动检测
      if (!healthStatus.healthy) {
        console.log('🔍 连接失败，尝试自动检测后端服务...');
        const detectedConfig = await apiConfigManager.autoDetectBackend();
        if (detectedConfig) {
          newStatus.connected = true;
          newStatus.message = '已自动检测并切换到可用的后端服务';
          newStatus.config = detectedConfig;
          newStatus.autoDetected = true;
        }
      }

      // 只有状态发生变化时才通知
      if (!this.lastStatus || 
          this.lastStatus.connected !== newStatus.connected ||
          this.lastStatus.config?.baseUrl !== newStatus.config.baseUrl) {
        
        this.lastStatus = newStatus;
        this.notifyCallbacks(newStatus);
      }
    } catch (error) {
      const errorStatus: ConnectionStatus = {
        connected: false,
        message: `连接检查失败: ${error instanceof Error ? error.message : String(error)}`,
        config: apiConfigManager.getConfig(),
        timestamp: Date.now(),
        autoDetected: false
      };

      if (!this.lastStatus || this.lastStatus.connected !== false) {
        this.lastStatus = errorStatus;
        this.notifyCallbacks(errorStatus);
      }
    }
  }

  private notifyCallbacks(status: ConnectionStatus): void {
    this.callbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('连接状态回调执行错误:', error);
      }
    });
  }

  public getCurrentStatus(): ConnectionStatus | null {
    return this.lastStatus;
  }
}

export interface ConnectionStatus {
  connected: boolean;
  message: string;
  config: any;
  timestamp: number;
  autoDetected: boolean;
}

// 全局连接监控实例
export const connectionMonitor = new ConnectionMonitor();