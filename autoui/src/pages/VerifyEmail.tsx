import React, { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { useSearchParams, useNavigate } from 'react-router-dom'
import authService from '../services/authService'

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f7;
  padding: 20px;
`

const Card = styled.div`
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  max-width: 500px;
  width: 100%;
  text-align: center;
`

const Title = styled.h1`
  font-size: 28px;
  color: #333;
  margin: 0 0 16px;
`

const Message = styled.p`
  font-size: 16px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 24px;
`

const StatusIcon = styled.div<{ status: 'loading' | 'success' | 'error' }>`
  font-size: 64px;
  margin: 0 0 24px;
  
  ${props => props.status === 'loading' && `
    animation: spin 1s linear infinite;
  `}
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`

const Button = styled.button`
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin: 0 8px;

  &:hover {
    background: #4338ca;
  }

  &.secondary {
    background: #6b7280;
  }

  &.secondary:hover {
    background: #374151;
  }
`

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get('token')
      
      if (!token) {
        setStatus('error')
        setMessage('无效的验证链接。验证令牌缺失。')
        return
      }

      try {
        const result = await authService.verifyEmail(token)
        
        if (result.success) {
          setStatus('success')
          setMessage(result.message || '邮箱验证成功！您现在可以正常使用所有功能。')
        } else {
          setStatus('error')
          setMessage(result.error || '邮箱验证失败，请检查验证链接是否正确。')
        }
      } catch (error) {
        setStatus('error')
        setMessage('验证过程中发生网络错误，请稍后重试。')
      }
    }

    verifyToken()
  }, [searchParams])

  const getStatusIcon = () => {
    switch (status) {
      case 'loading':
        return '⏳'
      case 'success':
        return '✅'
      case 'error':
        return '❌'
      default:
        return '⏳'
    }
  }

  const getTitle = () => {
    switch (status) {
      case 'loading':
        return '正在验证邮箱...'
      case 'success':
        return '邮箱验证成功！'
      case 'error':
        return '邮箱验证失败'
      default:
        return '邮箱验证'
    }
  }

  const handleGoHome = () => {
    navigate('/')
  }

  const handleResendEmail = async () => {
    try {
      const result = await authService.resendVerificationEmail()
      if (result.success) {
        alert('验证邮件已重新发送，请查收邮箱。')
      } else {
        alert(result.error || '发送失败，请稍后重试。')
      }
    } catch (error) {
      alert('网络错误，请稍后重试。')
    }
  }

  return (
    <Container>
      <Card>
        <StatusIcon status={status}>
          {getStatusIcon()}
        </StatusIcon>
        
        <Title>{getTitle()}</Title>
        
        <Message>{message}</Message>
        
        <div>
          <Button onClick={handleGoHome}>
            返回首页
          </Button>
          
          {status === 'error' && (
            <Button className="secondary" onClick={handleResendEmail}>
              重新发送验证邮件
            </Button>
          )}
        </div>
      </Card>
    </Container>
  )
}

export default VerifyEmail