import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { apiConfigManager } from '../config/api-config';
import { connectionMonitor, ConnectionStatus } from '../services/connection-monitor';

interface ApiConfigPanelProps {
  onClose?: () => void;
}

export const ApiConfigPanel: React.FC<ApiConfigPanelProps> = ({ onClose }) => {
  const [config, setConfig] = useState(apiConfigManager.getConfig());
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [isAutoDetecting, setIsAutoDetecting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    // 监听连接状态变化
    const unsubscribe = connectionMonitor.onStatusChange(setStatus);
    
    // 开始监控连接
    connectionMonitor.startMonitoring(10000);

    return () => {
      unsubscribe();
      connectionMonitor.stopMonitoring();
    };
  }, []);

  const handleConfigChange = (field: string, value: string) => {
    const newConfig = { ...config };
    if (field === 'host') {
      newConfig.host = value;
      newConfig.baseUrl = `http://${value}:${newConfig.port}/api`;
    } else if (field === 'port') {
      const port = parseInt(value);
      if (!isNaN(port)) {
        newConfig.port = port;
        newConfig.baseUrl = `http://${newConfig.host}:${port}/api`;
      }
    } else if (field === 'baseUrl') {
      newConfig.baseUrl = value;
    }
    setConfig(newConfig);
  };

  const handleSaveConfig = () => {
    apiConfigManager.updateConfig(config);
    console.log('📝 配置已保存:', config);
  };

  const handleAutoDetect = async () => {
    setIsAutoDetecting(true);
    try {
      const detectedConfig = await api.autoDetect();
      if (detectedConfig) {
        setConfig(detectedConfig);
        console.log('🔍 自动检测成功:', detectedConfig);
      } else {
        console.warn('❌ 未检测到可用的后端服务');
      }
    } catch (error) {
      console.error('自动检测失败:', error);
    } finally {
      setIsAutoDetecting(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      const healthStatus = await api.healthCheck();
      console.log('🧪 连接测试结果:', healthStatus);
    } catch (error) {
      console.error('连接测试失败:', error);
    }
  };

  const getStatusColor = () => {
    if (!status) return '#gray';
    return status.connected ? '#22c55e' : '#ef4444';
  };

  const getStatusText = () => {
    if (!status) return '检查中...';
    return status.connected ? '连接正常' : '连接失败';
  };

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: 'white',
      border: '1px solid #e2e8f0',
      borderRadius: '8px',
      padding: '20px',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      zIndex: 1000,
      minWidth: '350px',
      maxWidth: '500px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold' }}>API 配置</h3>
        {onClose && (
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            ×
          </button>
        )}
      </div>

      {/* 连接状态 */}
      <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div 
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: getStatusColor()
            }}
          />
          <span style={{ fontWeight: 'medium' }}>{getStatusText()}</span>
        </div>
        {status && (
          <div style={{ marginTop: '8px', fontSize: '14px', color: '#64748b' }}>
            {status.message}
            {status.autoDetected && <span style={{ color: '#22c55e' }}> (自动检测)</span>}
          </div>
        )}
      </div>

      {/* 基本配置 */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: 'medium' }}>
          后端主机地址:
        </label>
        <input
          type="text"
          value={config.host}
          onChange={(e) => handleConfigChange('host', e.target.value)}
          placeholder="localhost"
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: 'medium' }}>
          端口号:
        </label>
        <input
          type="number"
          value={config.port}
          onChange={(e) => handleConfigChange('port', e.target.value)}
          placeholder="5001"
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        />
      </div>

      {/* 高级配置 */}
      <div style={{ marginBottom: '16px' }}>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            background: 'none',
            border: 'none',
            color: '#3b82f6',
            fontSize: '14px',
            cursor: 'pointer',
            textDecoration: 'underline'
          }}
        >
          {showAdvanced ? '隐藏' : '显示'} 高级配置
        </button>
      </div>

      {showAdvanced && (
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: 'medium' }}>
            完整 API 地址:
          </label>
          <input
            type="text"
            value={config.baseUrl}
            onChange={(e) => handleConfigChange('baseUrl', e.target.value)}
            placeholder="http://localhost:5001/api"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
        </div>
      )}

      {/* 操作按钮 */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button
          onClick={handleAutoDetect}
          disabled={isAutoDetecting}
          style={{
            padding: '8px 16px',
            backgroundColor: isAutoDetecting ? '#9ca3af' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            cursor: isAutoDetecting ? 'not-allowed' : 'pointer'
          }}
        >
          {isAutoDetecting ? '检测中...' : '自动检测'}
        </button>

        <button
          onClick={handleTestConnection}
          style={{
            padding: '8px 16px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            cursor: 'pointer'
          }}
        >
          测试连接
        </button>

        <button
          onClick={handleSaveConfig}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f59e0b',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            cursor: 'pointer'
          }}
        >
          保存配置
        </button>
      </div>

      {/* 使用说明 */}
      <div style={{ 
        marginTop: '16px', 
        padding: '12px', 
        backgroundColor: '#fef3c7', 
        borderRadius: '6px',
        fontSize: '12px',
        color: '#92400e'
      }}>
        💡 <strong>提示:</strong> 修改配置后点击"保存配置"。如果不确定后端地址，可以点击"自动检测"。
      </div>
    </div>
  );
};