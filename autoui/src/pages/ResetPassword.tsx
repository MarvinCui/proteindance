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
`

const Title = styled.h1`
  font-size: 28px;
  color: #333;
  margin: 0 0 24px;
  text-align: center;
`

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 16px;
`

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`

const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: #374151;
`

const Input = styled.input`
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:focus {
    outline: none;
    border-color: #4f46e5;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  }

  &:disabled {
    background: #f9fafb;
    color: #6b7280;
    cursor: not-allowed;
  }
`

const Button = styled.button`
  padding: 12px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 8px;

  &:hover:not(:disabled) {
    background: #4338ca;
  }

  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  &.secondary {
    background: #6b7280;
    margin-top: 16px;
  }

  &.secondary:hover:not(:disabled) {
    background: #374151;
  }
`

const ErrorMessage = styled.div`
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
`

const SuccessMessage = styled.div`
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  color: #16a34a;
  font-size: 14px;
`

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const resetToken = searchParams.get('token')
    if (!resetToken) {
      setError('无效的重置链接。重置令牌缺失。')
    } else {
      setToken(resetToken)
    }
  }, [searchParams])

  const validateForm = (): boolean => {
    if (!password) {
      setError('请输入新密码')
      return false
    }
    if (password.length < 6) {
      setError('密码长度至少6位')
      return false
    }
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!token) {
      setError('无效的重置令牌')
      return
    }

    if (!validateForm()) return

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const result = await authService.resetPassword(token, password)
      
      if (result.success) {
        setSuccess('密码重置成功！您现在可以使用新密码登录。')
        setTimeout(() => {
          navigate('/', { replace: true })
        }, 3000)
      } else {
        setError(result.error || '密码重置失败，请重试')
      }
    } catch (error) {
      setError('网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleGoHome = () => {
    navigate('/')
  }

  if (!token && !error) {
    return (
      <Container>
        <Card>
          <Title>验证重置链接...</Title>
        </Card>
      </Container>
    )
  }

  return (
    <Container>
      <Card>
        <Title>重置密码</Title>
        
        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        {token && !success && (
          <Form onSubmit={handleSubmit}>
            <FormGroup>
              <Label htmlFor="password">新密码</Label>
              <Input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                placeholder="请输入新密码（至少6位）"
                required
              />
            </FormGroup>

            <FormGroup>
              <Label htmlFor="confirmPassword">确认新密码</Label>
              <Input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                placeholder="请再次输入新密码"
                required
              />
            </FormGroup>

            <Button type="submit" disabled={loading}>
              {loading ? '正在重置...' : '重置密码'}
            </Button>
          </Form>
        )}

        <Button className="secondary" onClick={handleGoHome}>
          返回首页
        </Button>
      </Card>
    </Container>
  )
}

export default ResetPassword