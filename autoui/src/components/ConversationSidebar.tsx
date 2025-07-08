import React, { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { ConversationSession, conversationService } from '../services/conversationService'
import authService, { User } from '../services/authService'

const SidebarContainer = styled.div`
  width: 260px;
  height: 100vh;
  background: #f7f7f8;
  border-right: 1px solid #e5e5e7;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const Header = styled.div`
  padding: 16px;
  border-bottom: 1px solid #e5e5e7;
  background: white;
`

const NewChatButton = styled.button`
  width: 100%;
  padding: 10px 12px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;

  &:hover {
    background: #4338ca;
  }

  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
`

const SearchBox = styled.input`
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e5e7;
  border-radius: 6px;
  font-size: 14px;
  margin-top: 12px;
  outline: none;

  &:focus {
    border-color: #4f46e5;
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
  }
`

const ConversationList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 8px;
`

const ConversationItem = styled.div<{ isActive?: boolean }>`
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  background: ${props => props.isActive ? '#e0e7ff' : 'transparent'};
  border: 1px solid ${props => props.isActive ? '#c7d2fe' : 'transparent'};
  transition: all 0.2s;

  &:hover {
    background: ${props => props.isActive ? '#e0e7ff' : '#f3f4f6'};
  }
`

const ConversationTitle = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const ConversationPreview = styled.div`
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
`

const ConversationTime = styled.div`
  font-size: 11px;
  color: #9ca3af;
`

const UserSection = styled.div`
  padding: 16px;
  border-top: 1px solid #e5e5e7;
  background: white;
`

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
`

const UserAvatar = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
`

const UserDetails = styled.div`
  flex: 1;
  min-width: 0;
`

const UserName = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const UserEmail = styled.div`
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const AuthButtons = styled.div`
  display: flex;
  gap: 8px;
`

const AuthButton = styled.button`
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e5e5e7;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &.primary {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;

    &:hover {
      background: #4338ca;
    }
  }

  &.secondary {
    background: white;
    color: #374151;

    &:hover {
      background: #f3f4f6;
    }
  }
`

const LogoutButton = styled.button`
  width: 100%;
  padding: 8px 12px;
  background: white;
  color: #dc2626;
  border: 1px solid #e5e5e7;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  margin-top: 8px;

  &:hover {
    background: #fef2f2;
    border-color: #fecaca;
  }
`

const EmptyState = styled.div`
  padding: 32px 16px;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
`

const LoadingState = styled.div`
  padding: 16px;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
`

interface Props {
  onConversationSelect?: (sessionId: number) => void
  activeConversationId?: number
  onNewChat?: () => void
  onShowAuth?: (mode: 'login' | 'register') => void
}

const ConversationSidebar: React.FC<Props> = ({
  onConversationSelect,
  activeConversationId,
  onNewChat,
  onShowAuth
}) => {
  const [conversations, setConversations] = useState<ConversationSession[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    // 检查登录状态
    setUser(authService.getCurrentUser())
    
    if (authService.isAuthenticated()) {
      loadConversations()
    }
  }, [])

  const loadConversations = async () => {
    setLoading(true)
    try {
      const result = await conversationService.getConversations()
      if (result.success && result.sessions) {
        setConversations(result.sessions)
      }
    } catch (error) {
      console.error('加载对话失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    
    if (!query.trim()) {
      loadConversations()
      return
    }

    setLoading(true)
    try {
      const result = await conversationService.searchConversations(query)
      if (result.success && result.sessions) {
        setConversations(result.sessions)
      }
    } catch (error) {
      console.error('搜索对话失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = async () => {
    if (!authService.isAuthenticated()) {
      onShowAuth?.('login')
      return
    }

    try {
      const result = await conversationService.createConversation()
      if (result.success && result.session) {
        setConversations(prev => [result.session!, ...prev])
        onConversationSelect?.(result.session.id)
        onNewChat?.()
      }
    } catch (error) {
      console.error('创建对话失败:', error)
    }
  }

  const handleLogout = () => {
    authService.logout()
    setUser(null)
    setConversations([])
  }

  const getUserInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part.charAt(0))
      .join('')
      .substring(0, 2)
      .toUpperCase()
  }

  return (
    <SidebarContainer>
      <Header>
        <NewChatButton 
          onClick={handleNewChat}
          disabled={loading}
        >
          <span>➕</span>
          新建对话
        </NewChatButton>
        
        {authService.isAuthenticated() && (
          <SearchBox
            type="text"
            placeholder="搜索对话..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
          />
        )}
      </Header>

      <ConversationList>
        {loading ? (
          <LoadingState>加载中...</LoadingState>
        ) : conversations.length === 0 ? (
          <EmptyState>
            {authService.isAuthenticated() 
              ? '暂无对话记录' 
              : '登录后查看对话历史'
            }
          </EmptyState>
        ) : (
          conversations.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              isActive={conversation.id === activeConversationId}
              onClick={() => onConversationSelect?.(conversation.id)}
            >
              <ConversationTitle>{conversation.title}</ConversationTitle>
              {conversation.last_message && (
                <ConversationPreview>
                  {conversationService.truncateText(conversation.last_message.content, 50)}
                </ConversationPreview>
              )}
              <ConversationTime>
                {conversationService.formatTime(conversation.updated_at)}
              </ConversationTime>
            </ConversationItem>
          ))
        )}
      </ConversationList>

      <UserSection>
        {user ? (
          <>
            <UserInfo>
              <UserAvatar>
                {getUserInitials(user.username)}
              </UserAvatar>
              <UserDetails>
                <UserName>{user.username}</UserName>
                <UserEmail>{user.email}</UserEmail>
              </UserDetails>
            </UserInfo>
            <LogoutButton onClick={handleLogout}>
              退出登录
            </LogoutButton>
          </>
        ) : (
          <AuthButtons>
            <AuthButton 
              className="primary"
              onClick={() => onShowAuth?.('login')}
            >
              登录
            </AuthButton>
            <AuthButton 
              className="secondary"
              onClick={() => onShowAuth?.('register')}
            >
              注册
            </AuthButton>
          </AuthButtons>
        )}
      </UserSection>
    </SidebarContainer>
  )
}

export default ConversationSidebar