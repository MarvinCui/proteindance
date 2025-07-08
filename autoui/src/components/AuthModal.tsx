import React, { useState } from 'react'
import styled from '@emotion/styled'
import authService, { RegisterData, LoginData } from '../services/authService'

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
`

const Modal = styled.div`
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 420px;
  max-height: 90vh;
  overflow: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
`

const Header = styled.div`
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
  text-align: center;
`

const Title = styled.h2`
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #111827;
`

const Subtitle = styled.p`
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 14px;
`

const CloseButton = styled.button`
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;

  &:hover {
    background: #f3f4f6;
    color: #374151;
  }
`

const Content = styled.div`
  padding: 24px;
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
  }
`

const SubmitButton = styled.button`
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
`

const ErrorMessage = styled.div`
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 16px;
`

const SuccessMessage = styled.div`
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  color: #16a34a;
  font-size: 14px;
  margin-bottom: 16px;
`

const SwitchMode = styled.div`
  text-align: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  font-size: 14px;
  color: #6b7280;
`

const SwitchLink = styled.button`
  background: none;
  border: none;
  color: #4f46e5;
  cursor: pointer;
  font-weight: 500;
  text-decoration: underline;

  &:hover {
    color: #4338ca;
  }
`

const ForgotPassword = styled.button`
  background: none;
  border: none;
  color: #4f46e5;
  cursor: pointer;
  font-size: 12px;
  text-decoration: underline;
  align-self: flex-end;
  margin-top: -8px;

  &:hover {
    color: #4338ca;
  }
`

interface Props {
  isOpen: boolean
  onClose: () => void
  mode: 'login' | 'register' | 'forgot-password'
  onModeChange: (mode: 'login' | 'register' | 'forgot-password') => void
  onSuccess?: () => void
}

const AuthModal: React.FC<Props> = ({
  isOpen,
  onClose,
  mode,
  onModeChange,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  if (!isOpen) return null

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setError('')
    setSuccess('')
  }

  const validateForm = (): boolean => {
    if (mode === 'register') {
      if (!formData.email || !formData.username || !formData.password) {
        setError('请填写所有必填字段')
        return false
      }
      if (formData.password !== formData.confirmPassword) {
        setError('两次输入的密码不一致')
        return false
      }
      if (formData.password.length < 6) {
        setError('密码长度至少6位')
        return false
      }
    } else if (mode === 'login') {
      if (!formData.email || !formData.password) {
        setError('请输入邮箱和密码')
        return false
      }
    } else if (mode === 'forgot-password') {
      if (!formData.email) {
        setError('请输入邮箱地址')
        return false
      }
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      if (mode === 'register') {
        const registerData: RegisterData = {
          email: formData.email,
          username: formData.username,
          password: formData.password
        }
        
        const result = await authService.register(registerData)
        
        if (result.success) {
          const message = result.auto_activated 
            ? '注册成功！用户已自动激活，可以直接登录。' 
            : '注册成功！请查收邮箱验证邮件。'
          setSuccess(message)
          setTimeout(() => {
            onModeChange('login')
            setSuccess('')
          }, 2000)
        } else {
          setError(result.error || '注册失败')
        }
      } else if (mode === 'login') {
        const loginData: LoginData = {
          email: formData.email,
          password: formData.password
        }
        
        const result = await authService.login(loginData)
        
        if (result.success) {
          setSuccess('登录成功！')
          setTimeout(() => {
            onSuccess?.()
            onClose()
          }, 1000)
        } else {
          setError(result.error || '登录失败')
        }
      } else if (mode === 'forgot-password') {
        const result = await authService.requestPasswordReset(formData.email)
        
        if (result.success) {
          setSuccess('密码重置邮件已发送，请查收邮箱。')
        } else {
          setError(result.error || '发送失败')
        }
      }
    } catch (error) {
      setError('网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const resetForm = () => {
    setFormData({
      email: '',
      username: '',
      password: '',
      confirmPassword: ''
    })
    setError('')
    setSuccess('')
  }

  const switchMode = (newMode: 'login' | 'register' | 'forgot-password') => {
    resetForm()
    onModeChange(newMode)
  }

  const getTitle = () => {
    switch (mode) {
      case 'register': return '注册账户'
      case 'login': return '用户登录'
      case 'forgot-password': return '忘记密码'
      default: return ''
    }
  }

  const getSubtitle = () => {
    switch (mode) {
      case 'register': return '创建您的 ProteinDance 账户'
      case 'login': return '登录到您的 ProteinDance 账户'
      case 'forgot-password': return '输入邮箱地址获取重置链接'
      default: return ''
    }
  }

  return (
    <Overlay onClick={handleOverlayClick}>
      <Modal>
        <CloseButton onClick={onClose}>×</CloseButton>
        
        <Header>
          <Title>{getTitle()}</Title>
          <Subtitle>{getSubtitle()}</Subtitle>
        </Header>

        <Content>
          {error && <ErrorMessage>{error}</ErrorMessage>}
          {success && <SuccessMessage>{success}</SuccessMessage>}

          <Form onSubmit={handleSubmit}>
            <FormGroup>
              <Label htmlFor="email">邮箱地址</Label>
              <Input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                disabled={loading}
                required
                placeholder="请输入邮箱地址"
              />
            </FormGroup>

            {mode === 'register' && (
              <FormGroup>
                <Label htmlFor="username">用户名</Label>
                <Input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  disabled={loading}
                  required
                  placeholder="请输入用户名"
                />
              </FormGroup>
            )}

            {(mode === 'login' || mode === 'register') && (
              <FormGroup>
                <Label htmlFor="password">密码</Label>
                <Input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  disabled={loading}
                  required
                  placeholder={mode === 'register' ? '请输入密码（至少6位）' : '请输入密码'}
                />
                {mode === 'login' && (
                  <ForgotPassword 
                    type="button"
                    onClick={() => switchMode('forgot-password')}
                  >
                    忘记密码？
                  </ForgotPassword>
                )}
              </FormGroup>
            )}

            {mode === 'register' && (
              <FormGroup>
                <Label htmlFor="confirmPassword">确认密码</Label>
                <Input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  disabled={loading}
                  required
                  placeholder="请再次输入密码"
                />
              </FormGroup>
            )}

            <SubmitButton type="submit" disabled={loading}>
              {loading ? '处理中...' : 
                mode === 'register' ? '注册' :
                mode === 'login' ? '登录' :
                '发送重置邮件'
              }
            </SubmitButton>
          </Form>

          <SwitchMode>
            {mode === 'login' && (
              <>
                还没有账户？{' '}
                <SwitchLink onClick={() => switchMode('register')}>
                  立即注册
                </SwitchLink>
              </>
            )}
            {mode === 'register' && (
              <>
                已有账户？{' '}
                <SwitchLink onClick={() => switchMode('login')}>
                  立即登录
                </SwitchLink>
              </>
            )}
            {mode === 'forgot-password' && (
              <>
                记起密码了？{' '}
                <SwitchLink onClick={() => switchMode('login')}>
                  返回登录
                </SwitchLink>
              </>
            )}
          </SwitchMode>
        </Content>
      </Modal>
    </Overlay>
  )
}

export default AuthModal