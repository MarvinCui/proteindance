// API配置管理
interface ApiConfig {
  baseUrl: string;
  host: string;
  port: number;
  timeout: number;
}

class ApiConfigManager {
  private config: ApiConfig;
  private fallbackPorts = [5001, 8000, 3001, 8080];
  private fallbackHosts = ['localhost', '127.0.0.1'];

  constructor() {
    this.config = this.initializeConfig();
  }

  private initializeConfig(): ApiConfig {
    // 1. 优先使用环境变量
    const envHost = import.meta.env.VITE_BACKEND_HOST || 'localhost';
    const envPort = parseInt(import.meta.env.VITE_BACKEND_PORT || '5001');
    const envBaseUrl = import.meta.env.VITE_API_BASE_URL;

    if (envBaseUrl) {
      const config = this.parseApiUrl(envBaseUrl);
      console.log('🔧 使用环境变量配置:', config);
      return config;
    }

    // 2. 构建默认配置
    const baseUrl = `http://${envHost}:${envPort}/api`;
    const config: ApiConfig = {
      baseUrl,
      host: envHost,
      port: envPort,
      timeout: 10000
    };

    console.log('🔧 使用默认配置:', config);
    return config;
  }

  private parseApiUrl(url: string): ApiConfig {
    try {
      const parsed = new URL(url);
      return {
        baseUrl: url,
        host: parsed.hostname,
        port: parseInt(parsed.port) || (parsed.protocol === 'https:' ? 443 : 80),
        timeout: 10000
      };
    } catch (error) {
      console.warn('⚠️  无法解析API URL，使用默认配置:', error);
      return {
        baseUrl: 'http://localhost:5001/api',
        host: 'localhost',
        port: 5001,
        timeout: 10000
      };
    }
  }

  public getConfig(): ApiConfig {
    return { ...this.config };
  }

  public getBaseUrl(): string {
    return this.config.baseUrl;
  }

  public updateConfig(newConfig: Partial<ApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // 更新baseUrl以保持一致性
    if (newConfig.host || newConfig.port) {
      this.config.baseUrl = `http://${this.config.host}:${this.config.port}/api`;
    }
    
    console.log('🔄 配置已更新:', this.config);
  }

  // 自动检测可用的后端服务
  public async autoDetectBackend(): Promise<ApiConfig | null> {
    console.log('🔍 开始自动检测后端服务...');
    
    for (const host of this.fallbackHosts) {
      for (const port of this.fallbackPorts) {
        const testUrl = `http://${host}:${port}/docs`;
        try {
          const response = await fetch(testUrl, { 
            method: 'HEAD', 
            signal: AbortSignal.timeout(3000)
          });
          
          if (response.ok) {
            const detectedConfig: ApiConfig = {
              baseUrl: `http://${host}:${port}/api`,
              host,
              port,
              timeout: 10000
            };
            
            console.log('✅ 检测到后端服务:', detectedConfig);
            this.updateConfig(detectedConfig);
            return detectedConfig;
          }
        } catch (error) {
          // 继续尝试下一个
        }
      }
    }
    
    console.warn('❌ 未检测到可用的后端服务');
    return null;
  }

  // 验证当前配置是否可用
  public async validateConfig(): Promise<boolean> {
    try {
      const testUrl = this.config.baseUrl.replace('/api', '/docs');
      const response = await fetch(testUrl, { 
        method: 'HEAD', 
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  // 获取健康检查结果
  public async getHealthStatus(): Promise<{
    healthy: boolean;
    message: string;
    config: ApiConfig;
  }> {
    const isValid = await this.validateConfig();
    
    if (isValid) {
      return {
        healthy: true,
        message: '后端服务连接正常',
        config: this.getConfig()
      };
    }

    // 尝试自动检测
    const detectedConfig = await this.autoDetectBackend();
    if (detectedConfig) {
      return {
        healthy: true,
        message: '已自动检测并切换到可用的后端服务',
        config: detectedConfig
      };
    }

    return {
      healthy: false,
      message: `无法连接到后端服务 (${this.config.baseUrl})`,
      config: this.getConfig()
    };
  }
}

// 全局配置管理器实例
export const apiConfigManager = new ApiConfigManager();

// 导出配置获取函数
export const getApiConfig = () => apiConfigManager.getConfig();
export const getApiBaseUrl = () => apiConfigManager.getBaseUrl();

// 导出类型
export type { ApiConfig };