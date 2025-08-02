import React, { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import errorService, { ErrorLog } from '../services/errorService'

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`

const ModalContent = styled.div`
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
`

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e5e7;
`

const ModalTitle = styled.h2`
  margin: 0;
  font-size: 18px;
  color: #333;
`

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  
  &:hover {
    color: #333;
  }
`

const TabContainer = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
`

const Tab = styled.button<{ active: boolean }>`
  padding: 8px 16px;
  border: none;
  background: ${props => props.active ? '#4f46e5' : '#f3f4f6'};
  color: ${props => props.active ? 'white' : '#374151'};
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  
  &:hover {
    background: ${props => props.active ? '#4338ca' : '#e5e7eb'};
  }
`

const LogContainer = styled.div`
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e5e5e7;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
  font-family: monospace;
  font-size: 12px;
`

const LogEntry = styled.div<{ level: string }>`
  padding: 8px;
  margin-bottom: 4px;
  border-left: 4px solid ${props => {
    switch (props.level) {
      case 'error': return '#dc2626'
      case 'warn': return '#f59e0b'
      case 'info': return '#3b82f6'
      case 'debug': return '#6b7280'
      default: return '#9ca3af'
    }
  }};
  background: white;
  border-radius: 4px;
  font-size: 11px;
`

const LogTime = styled.div`
  color: #6b7280;
  font-size: 10px;
  margin-bottom: 4px;
`

const LogMessage = styled.div`
  color: #374151;
  font-weight: 500;
  margin-bottom: 4px;
  word-break: break-word;
`

const LogDetails = styled.div`
  color: #6b7280;
  font-size: 10px;
  margin-top: 4px;
`

const ButtonContainer = styled.div`
  display: flex;
  gap: 8px;
  margin-top: 16px;
  justify-content: flex-end;
`

const Button = styled.button`
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  
  &.primary {
    background: #4f46e5;
    color: white;
    
    &:hover {
      background: #4338ca;
    }
  }
  
  &.secondary {
    background: #f3f4f6;
    color: #374151;
    
    &:hover {
      background: #e5e7eb;
    }
  }
  
  &.danger {
    background: #dc2626;
    color: white;
    
    &:hover {
      background: #b91c1c;
    }
  }
`

const StatsContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
`

const StatItem = styled.div`
  text-align: center;
`

const StatValue = styled.div`
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
`

const StatLabel = styled.div`
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
`

interface Props {
  isOpen: boolean
  onClose: () => void
}

const ErrorReportModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<ErrorLog[]>([])
  const [activeTab, setActiveTab] = useState<'all' | 'error' | 'warn' | 'info' | 'debug'>('all')
  const [filteredLogs, setFilteredLogs] = useState<ErrorLog[]>([])

  useEffect(() => {
    if (isOpen) {
      loadLogs()
    }
  }, [isOpen])

  useEffect(() => {
    if (activeTab === 'all') {
      setFilteredLogs(logs)
    } else {
      setFilteredLogs(logs.filter(log => log.level === activeTab))
    }
  }, [logs, activeTab])

  const loadLogs = () => {
    const allLogs = errorService.getAllLogs()
    setLogs(allLogs)
  }

  const handleExport = () => {
    const data = errorService.exportLogs()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `error-logs-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleClear = () => {
    if (window.confirm('确定要清空所有日志吗？此操作不可恢复。')) {
      errorService.clearLogs()
      setLogs([])
    }
  }

  const handleUpload = async () => {
    try {
      await errorService.uploadLogs()
      alert('日志上传成功')
    } catch (error) {
      alert('日志上传失败')
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const getStats = () => {
    const errorCount = logs.filter(log => log.level === 'error').length
    const warnCount = logs.filter(log => log.level === 'warn').length
    const infoCount = logs.filter(log => log.level === 'info').length
    const debugCount = logs.filter(log => log.level === 'debug').length
    
    return { errorCount, warnCount, infoCount, debugCount }
  }

  if (!isOpen) return null

  const stats = getStats()

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>错误报告和日志</ModalTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>

        <StatsContainer>
          <StatItem>
            <StatValue>{stats.errorCount}</StatValue>
            <StatLabel>错误</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue>{stats.warnCount}</StatValue>
            <StatLabel>警告</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue>{stats.infoCount}</StatValue>
            <StatLabel>信息</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue>{stats.debugCount}</StatValue>
            <StatLabel>调试</StatLabel>
          </StatItem>
          <StatItem>
            <StatValue>{logs.length}</StatValue>
            <StatLabel>总计</StatLabel>
          </StatItem>
        </StatsContainer>

        <TabContainer>
          <Tab active={activeTab === 'all'} onClick={() => setActiveTab('all')}>
            全部 ({logs.length})
          </Tab>
          <Tab active={activeTab === 'error'} onClick={() => setActiveTab('error')}>
            错误 ({stats.errorCount})
          </Tab>
          <Tab active={activeTab === 'warn'} onClick={() => setActiveTab('warn')}>
            警告 ({stats.warnCount})
          </Tab>
          <Tab active={activeTab === 'info'} onClick={() => setActiveTab('info')}>
            信息 ({stats.infoCount})
          </Tab>
          <Tab active={activeTab === 'debug'} onClick={() => setActiveTab('debug')}>
            调试 ({stats.debugCount})
          </Tab>
        </TabContainer>

        <LogContainer>
          {filteredLogs.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#6b7280', padding: '20px' }}>
              没有找到日志记录
            </div>
          ) : (
            filteredLogs.map(log => (
              <LogEntry key={log.id} level={log.level}>
                <LogTime>{formatTime(log.timestamp)}</LogTime>
                <LogMessage>{log.message}</LogMessage>
                {log.context && (
                  <LogDetails>
                    上下文: {JSON.stringify(log.context)}
                  </LogDetails>
                )}
                {log.stack && (
                  <LogDetails>
                    堆栈: {log.stack}
                  </LogDetails>
                )}
                <LogDetails>
                  URL: {log.url} | 用户: {log.userId || '未知'}
                </LogDetails>
              </LogEntry>
            ))
          )}
        </LogContainer>

        <ButtonContainer>
          <Button className="secondary" onClick={handleClear}>
            清空日志
          </Button>
          <Button className="secondary" onClick={handleExport}>
            导出日志
          </Button>
          <Button className="primary" onClick={handleUpload}>
            上传日志
          </Button>
        </ButtonContainer>
      </ModalContent>
    </ModalOverlay>
  )
}

export default ErrorReportModal