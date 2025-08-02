import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SessionMetadata, Session } from '../services/api.types';
import authService, { User, LoginData, RegisterData } from '../services/authService';

interface SessionHistoryProps {
  onSessionSelect: (session: Session) => void;
  currentSessionId: string | null;
  onNewSession: () => void;
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ onSessionSelect, currentSessionId, onNewSession }) => {
  const [sessions, setSessions] = useState<SessionMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [showAuthPrompt, setShowAuthPrompt] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'forgot-password'>('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: ''
  });
  const [authError, setAuthError] = useState<string | null>(null);


  useEffect(() => {
    // 检查认证状态
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    
    if (currentUser) {
      loadSessions();
    } else {
      // Don't show prompt immediately, wait for user action
      // setShowAuthPrompt(true);
    }
  }, []);

  useEffect(() => {
    // 监听认证状态变化
    const checkAuth = () => {
      const currentUser = authService.getCurrentUser();
      setUser(currentUser);
      
      if (currentUser && showAuthPrompt) {
        setShowAuthPrompt(false);
        loadSessions();
      } else if (!currentUser) {
        // Don't force the prompt, let the user click
        // setShowAuthPrompt(true);
        setSessions([]);
      }
    };
    
    // 每隔1秒检查一次认证状态（用于检测其他组件的登录/注销）
    const interval = setInterval(checkAuth, 1000);
    
    return () => clearInterval(interval);
  }, [showAuthPrompt]);

  const loadSessions = async () => {
    if (!authService.isAuthenticated()) {
      // setShowAuthPrompt(true);
      setSessions([]);
      return;
    }

    setIsLoading(true);
    try {
      const sessionList = await api.listSessions();
      // Sort sessions by creation time, newest first
      const sortedSessions = sessionList.sort((a, b) => 
        (b.created_at || 0) - (a.created_at || 0)
      );
      setSessions(sortedSessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      
      // 如果是认证错误，提示用户重新登录
      if ((error as any)?.message?.includes('401') || (error as any)?.message?.includes('unauthorized')) {
        authService.logout();
        setUser(null);
        setShowAuthPrompt(true);
      }
      
      setSessions([]); 
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionClick = async (sessionId: string) => {
    if (!authService.isAuthenticated()) {
      setShowAuthPrompt(true);
      return;
    }

    try {
      const session = await api.getSession(sessionId);
      onSessionSelect(session);
    } catch (error) {
      console.error('Failed to load session:', error);
      
      // 如果是认证错误，提示用户重新登录
      if ((error as any)?.message?.includes('401') || (error as any)?.message?.includes('unauthorized')) {
        authService.logout();
        setUser(null);
        setShowAuthPrompt(true);
      }
    }
  };

  const handleNewSession = () => {
    if (!authService.isAuthenticated()) {
      setShowAuthPrompt(true);
      return;
    }
    
    onNewSession();
    // After creating a new session, we should probably reload the list
    // but the new session is only created on the first save.
    // For now, the UX is to just clear the state.
  };

  const handleLoginRegisterClick = () => {
    setAuthMode('login');
    setShowAuthPrompt(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAuthenticating(true);
    setAuthError(null);

    try {
      if (authMode === 'login') {
        const loginData: LoginData = {
          email: formData.email,
          password: formData.password
        };
        const result = await authService.login(loginData);
        
        if (!result.success) {
          throw new Error(result.error || '登录失败');
        }
      } else if (authMode === 'register') {
        const registerData: RegisterData = {
          email: formData.email,
          password: formData.password,
          username: formData.username
        };
        const result = await authService.register(registerData);
        
        if (result.success) {
          if (result.requires_verification) {
            setAuthError(`注册成功！验证邮件已发送到 ${formData.email}，请查收并点击邮件中的验证链接。`);
            setFormData({ email: '', password: '', confirmPassword: '', username: '' });
            return; // 不要继续处理，等待用户验证邮箱
          } else if (result.auto_activated) {
            setAuthError('注册成功！账户已自动激活。');
          }
        } else {
          throw new Error(result.error || '注册失败');
        }
      } else if (authMode === 'forgot-password') {
        await authService.requestPasswordReset(formData.email);
        setAuthError('密码重置邮件已发送，请检查您的邮箱');
        return;
      }

      // 成功后重新检查用户状态
      const currentUser = authService.getCurrentUser();
      setUser(currentUser);
      
      if (currentUser) {
        setShowAuthPrompt(false);
        setFormData({ email: '', password: '', confirmPassword: '', username: '' });
        setAuthError(null);
        loadSessions();
      } else {
        // 如果getCurrentUser()返回null，可能是异步问题，稍等片刻再试
        setTimeout(() => {
          const retryUser = authService.getCurrentUser();
          if (retryUser) {
            setUser(retryUser);
            setShowAuthPrompt(false);
            setFormData({ email: '', password: '', confirmPassword: '', username: '' });
            setAuthError(null);
            loadSessions();
          }
        }, 100);
      }
    } catch (error: any) {
      setAuthError(error.message || '操作失败，请重试');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the session from being selected
    
    if (!authService.isAuthenticated()) {
      setShowAuthPrompt(true);
      return;
    }
    
    if (window.confirm('确认删除这个会话记录？')) {
      try {
        await api.deleteSession(sessionId);
        loadSessions(); // Refresh the list
      } catch (error: any) {
        console.error('Failed to delete session:', error);
        
        // 如果是认证错误，提示用户重新登录
        if (error?.message?.includes('401') || error?.message?.includes('unauthorized')) {
          authService.logout();
          setUser(null);
          setShowAuthPrompt(true);
        }
      }
    }
  };
  
  useEffect(() => {
    // This could be used to refresh sessions from other tabs, for example.
    // For now, we only load once.
  }, [currentSessionId]);


  return (
    <div className="session-history-panel">
      <div className="panel-header">
        <h3>研发历史</h3>
        {user ? (
          <button type="button" onClick={handleNewSession} className="new-session-btn" title="新建会话">+</button>
        ) : (
          <button type="button" onClick={handleLoginRegisterClick} className="login-register-btn">
            登录 / 注册
          </button>
        )}
      </div>
      
      {showAuthPrompt && (
        <div className="auth-modal-overlay" onClick={() => setShowAuthPrompt(false)}>
          <div className="auth-container" onClick={(e) => e.stopPropagation()}>
            <div className="auth-header">
              <div className="auth-icon">
                <div className="icon-bg"></div>
                <span>🔐</span>
              </div>
              <h2 className="auth-title">
                {authMode === 'login' ? '登录' : authMode === 'register' ? '注册' : '重置密码'}
              </h2>
            </div>
            
            <form onSubmit={handleAuth} className="auth-form">
              <div className={`form-wrapper ${isAuthenticating ? 'authenticating' : ''}`}>
                {authMode === 'register' && (
                  <div className="input-group">
                    <input
                      type="text"
                      name="username"
                      placeholder="用户名"
                      value={formData.username}
                      onChange={handleInputChange}
                      className="auth-input"
                      required
                    />
                  </div>
                )}
                
                <div className="input-group">
                  <input
                    type="email"
                    name="email"
                    placeholder="邮箱地址"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="auth-input"
                    required
                  />
                </div>
                
                {authMode !== 'forgot-password' && (
                  <div className="input-group">
                    <input
                      type="password"
                      name="password"
                      placeholder="密码"
                      value={formData.password}
                      onChange={handleInputChange}
                      className="auth-input"
                      required
                    />
                  </div>
                )}
                
                {authMode === 'register' && (
                  <div className="input-group">
                    <input
                      type="password"
                      name="confirmPassword"
                      placeholder="确认密码"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className="auth-input"
                      required
                    />
                  </div>
                )}
                
                {authError && (
                  <div className={`auth-message ${authError.includes('成功') || authError.includes('已发送') ? 'success' : 'error'}`}>
                    {authError}
                  </div>
                )}
                
                <button 
                  type="submit" 
                  className={`auth-button ${isAuthenticating ? 'loading' : ''}`}
                  disabled={isAuthenticating}
                >
                  {isAuthenticating ? (
                    <div className="loading-spinner">
                      <div className="spinner"></div>
                      <span>处理中...</span>
                    </div>
                  ) : (
                    authMode === 'login' ? '登录' : authMode === 'register' ? '注册' : '发送重置邮件'
                  )}
                </button>
              </div>
            </form>
            
            <div className="auth-footer">
              {authMode === 'login' ? (
                <>
                  <button 
                    type="button" 
                    className="link-button"
                    onClick={() => setAuthMode('register')}
                  >
                    还没有账号？注册
                  </button>
                  <button 
                    type="button" 
                    className="link-button"
                    onClick={() => setAuthMode('forgot-password')}
                  >
                    忘记密码？
                  </button>
                </>
              ) : authMode === 'register' ? (
                <button 
                  type="button" 
                  className="link-button"
                  onClick={() => setAuthMode('login')}
                >
                  已有账号？登录
                </button>
              ) : (
                <button 
                  type="button" 
                  className="link-button"
                  onClick={() => setAuthMode('login')}
                >
                  返回登录
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      
      {isLoading && sessions.length === 0 ? (
        <div className="loading-container">
          <div className="loading-animation">
            <div className="loading-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
            <span className="loading-text">加载会话中...</span>
          </div>
        </div>
      ) : user ? (
        <div className="sessions-container">
          <div className="user-info">
            <div className="user-avatar">👤</div>
            <div className="user-details">
              <span className="user-name">{user.email}</span>
              <button 
                type="button" 
                className="logout-btn"
                onClick={() => {
                  authService.logout();
                  setUser(null);
                  // setShowAuthPrompt(true);
                }}
              >
                退出
              </button>
            </div>
          </div>
          {sessions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <p>还没有研发记录</p>
              <span>开始您的第一个药物研发项目吧！</span>
            </div>
          ) : (
            <ul className="session-list">
              {sessions.map(session => (
                <li 
                  key={session.id} 
                  className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                  onClick={() => handleSessionClick(session.id)}
                  title={session.title}
                >
                  <div className="session-content">
                    <span className="session-title">{session.title}</span>
                    <span className="session-timestamp">
                      {(() => {
                        if (!session.created_at) return null;
                        const date = new Date(session.created_at * 1000);
                        return isNaN(date.getTime()) ? 'Invalid date' : date.toLocaleString('zh-CN', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        });
                      })()}
                    </span>
                  </div>
                  <button type="button" onClick={(e) => handleDeleteSession(session.id, e)} className="delete-btn" title="删除会话">×</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon">🔑</div>
          <p>请登录以查看研发历史</p>
          <span>登录后，您的所有会话都将安全地保存在这里。</span>
          <button type="button" onClick={handleLoginRegisterClick} className="primary-login-btn">
            立即登录
          </button>
        </div>
      )}
      <style>{`
        .session-history-panel {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          background-color: #f8f9fc;
          color: #374151;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(10px);
        }

        .panel-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
        }

        .login-register-btn {
          background: #4f46e5;
          color: white;
          border: none;
          padding: 6px 14px;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .login-register-btn:hover {
          background: #4338ca;
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
          transform: translateY(-1px);
        }

        .new-session-btn {
          background: #fff;
          color: #4f46e5;
          border: 1px solid #d1d5db;
          border-radius: 50%;
          width: 28px;
          height: 28px;
          font-size: 20px;
          line-height: 26px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }

        .new-session-btn::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: linear-gradient(45deg, transparent, rgba(79, 70, 229, 0.1), transparent);
          transform: rotate(45deg);
          transition: all 0.6s;
          opacity: 0;
        }

        .new-session-btn:hover::before {
          animation: shimmer 1.5s infinite;
          opacity: 1;
        }

        .new-session-btn:hover {
          background-color: #4f46e5;
          color: #fff;
          border-color: #4f46e5;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
        }

        @keyframes shimmer {
          0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
          100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }

        .user-status {
          font-size: 12px;
          color: #9ca3af;
          font-weight: 400;
        }

        /* Auth Modal Styles */
        .auth-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .auth-container {
          width: 360px;
          padding: 32px;
          border-radius: 24px;
          
          /* Enhanced Liquid Glass Effect */
          background: rgba(255, 255, 255, 0.15);
          -webkit-backdrop-filter: blur(20px) saturate(180%);
          backdrop-filter: blur(20px) saturate(180%);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-right-color: rgba(255, 255, 255, 0.15);
          border-bottom-color: rgba(255, 255, 255, 0.15);
          box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
          
          color: #2d3748;
          animation: slideIn 0.4s cubic-bezier(0.25, 1, 0.5, 1);
          position: relative;
          overflow: hidden;
        }

        .auth-container::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.05) 50%, rgba(255, 255, 255, 0) 100%);
          pointer-events: none;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .auth-header {
          text-align: center;
          margin-bottom: 28px;
        }

        .auth-icon {
          font-size: 28px;
          width: 64px;
          height: 64px;
          border-radius: 50%;
          margin: 0 auto 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          background: linear-gradient(145deg, rgba(79, 70, 229, 0.4), rgba(129, 140, 248, 0.4));
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .auth-icon .icon-bg {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 70%);
          animation: pulse 3s infinite ease-in-out;
        }

        .auth-title {
          margin: 0;
          font-size: 22px;
          font-weight: 600;
          color: #1a202c;
        }

        .auth-form {
          width: 100%;
        }

        .form-wrapper {
          transition: all 0.3s ease;
        }

        .input-group {
          margin-bottom: 18px;
        }

        .auth-input {
          width: 100%;
          padding: 12px 16px;
          border: 1px solid rgba(45, 55, 72, 0.3);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.2);
          color: #1a202c;
          font-size: 14px;
          transition: all 0.2s ease;
          box-sizing: border-box;
        }

        .auth-input::placeholder {
          color: rgba(45, 55, 72, 0.6);
        }

        .auth-input:focus {
          outline: none;
          border-color: rgba(79, 70, 229, 0.6);
          background: rgba(255, 255, 255, 0.3);
          box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
        }

        .auth-message {
          padding: 12px;
          margin-bottom: 16px;
          border-radius: 6px;
          font-size: 14px;
          text-align: center;
          border: 1px solid transparent;
        }
        
        .auth-message.error {
          background: rgba(239, 68, 68, 0.15);
          border-color: rgba(239, 68, 68, 0.4);
          color: #c53030;
        }
        
        .auth-message.success {
          background: rgba(34, 197, 94, 0.15);
          border-color: rgba(34, 197, 94, 0.4);
          color: #38a169;
        }

        .auth-button {
          width: 100%;
          padding: 12px;
          border: none;
          border-radius: 8px;
          background: #4f46e5;
          color: #ffffff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
          overflow: hidden;
        }

        .auth-button.loading {
          background: #6366f1;
        }

        .auth-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .auth-button:not(:disabled):hover {
          background: #4338ca;
          transform: translateY(-1px);
          box-shadow: 0 4px 20px rgba(79, 70, 229, 0.5);
        }

        .loading-spinner {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top: 2px solid #ffffff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .auth-footer {
          margin-top: 24px;
          text-align: center;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .link-button {
          background: none;
          border: none;
          color: #4f46e5;
          cursor: pointer;
          font-size: 14px;
          text-decoration: none;
          transition: color 0.2s ease;
          padding: 4px 0;
        }

        .link-button:hover {
          color: #4338ca;
          text-decoration: underline;
        }

        /* Loading Container */
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex: 1;
          padding: 40px 20px;
        }

        .loading-animation {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }

        .loading-dots {
          display: flex;
          gap: 8px;
        }

        .dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #4f46e5;
          animation: dotPulse 1.4s ease-in-out infinite both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        .dot:nth-child(3) { animation-delay: 0s; }

        @keyframes dotPulse {
          0%, 80%, 100% {
            transform: scale(0.6);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }

        /* Sessions Container */
        .sessions-container {
          display: flex;
          flex-direction: column;
          height: calc(100% - 57px);
          animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .user-info {
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
          background: #f9fafb;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .user-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: #4f46e5;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          color: white;
        }

        .user-details {
          flex: 1;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .user-name {
          font-size: 13px;
          color: #374151;
          font-weight: 500;
        }

        .logout-btn {
          background: none;
          border: 1px solid #d1d5db;
          color: #6b7280;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .logout-btn:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
          color: #374151;
        }

        /* Session List */
        .session-list {
          list-style: none;
          padding: 8px;
          margin: 0;
          overflow-y: auto;
          flex-grow: 1;
        }

        .session-item {
          padding: 12px 14px;
          margin-bottom: 6px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          font-size: 14px;
          color: #374151;
          border: 1px solid transparent;
          position: relative;
          background: #ffffff;
        }

        .session-item::after {
          content: '';
          position: absolute;
          bottom: -3px;
          left: 14px;
          right: 14px;
          height: 1px;
          background: linear-gradient(to right, transparent, #e5e7eb 20%, #e5e7eb 80%, transparent);
          opacity: 0.6;
        }

        .session-item:last-child::after {
          display: none;
        }

        .session-item::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(79, 70, 229, 0.05), transparent);
          transition: left 0.6s ease;
        }

        .session-item:hover::before {
          left: 100%;
        }

        .session-item:hover {
          background-color: #f3f4f6;
          border-color: #d1d5db;
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .session-item.active {
          background-color: #eef2ff;
          border-color: #a5b4fc;
          color: #4338ca;
          font-weight: 600;
          box-shadow: 0 2px 12px rgba(79, 70, 229, 0.15);
        }

        .session-content {
          display: flex;
          flex-direction: column;
          flex-grow: 1;
          margin-right: 8px;
          min-width: 0;
        }

        .session-title {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.3;
          margin-bottom: 2px;
        }

        .session-timestamp {
          font-size: 11px;
          color: #9ca3af;
          font-weight: 400;
          line-height: 1.2;
        }

        .session-item.active .session-timestamp {
          color: #6366f1;
        }

        .delete-btn {
          background: transparent;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          font-size: 18px;
          line-height: 1;
          padding: 2px 4px;
          border-radius: 4px;
          visibility: hidden;
          opacity: 0;
          transition: all 0.2s ease;
        }

        .session-item:hover .delete-btn {
          visibility: visible;
          opacity: 1;
        }

        .delete-btn:hover {
          color: #ef4444;
          background-color: #fee2e2;
          transform: scale(1.1);
        }

        /* Empty State */
        .empty-state {
          padding: 32px 16px;
          text-align: center;
          color: #9ca3af;
          animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.7;
        }

        .empty-state p {
          margin: 0 0 8px;
          font-size: 16px;
          color: #6b7280;
          font-weight: 500;
        }

        .empty-state span {
          font-size: 14px;
          color: #9ca3af;
          max-width: 220px;
          margin-bottom: 20px;
        }

        .primary-login-btn {
          background: #4f46e5;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .primary-login-btn:hover {
          background: #4338ca;
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
          transform: translateY(-1px);
        }

        /* Animations */
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.1);
            opacity: 0.7;
          }
        }

        /* Scrollbar Styling */
        .session-list::-webkit-scrollbar {
          width: 4px;
        }

        .session-list::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 2px;
        }

        .session-list::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 2px;
        }

        .session-list::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
};
