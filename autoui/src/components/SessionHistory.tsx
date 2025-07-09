import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SessionMetadata, Session } from '../services/api.types';

interface SessionHistoryProps {
  onSessionSelect: (session: Session) => void;
  currentSessionId: string | null;
  onNewSession: () => void;
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ onSessionSelect, currentSessionId, onNewSession }) => {
  const [sessions, setSessions] = useState<SessionMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Debounce function
  const debounce = <F extends (...args: any[]) => any>(func: F, waitFor: number) => {
    let timeout: ReturnType<typeof setTimeout> | null = null;

    return (...args: F extends (...args: infer P) => any ? P : never): Promise<ReturnType<F>> =>
      new Promise(resolve => {
        if (timeout) {
          clearTimeout(timeout);
        }

        timeout = setTimeout(() => resolve(func(...args)), waitFor);
      });
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
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
      setSessions([]); 
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionClick = async (sessionId: string) => {
    try {
      const session = await api.getSession(sessionId);
      onSessionSelect(session);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const handleNewSession = () => {
    onNewSession();
    // After creating a new session, we should probably reload the list
    // but the new session is only created on the first save.
    // For now, the UX is to just clear the state.
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the session from being selected
    if (window.confirm('Are you sure you want to delete this session?')) {
      try {
        await api.deleteSession(sessionId);
        loadSessions(); // Refresh the list
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };
  
  const debouncedLoadSessions = debounce(loadSessions, 500);

  useEffect(() => {
    // This could be used to refresh sessions from other tabs, for example.
    // For now, we only load once.
  }, [currentSessionId]);


  return (
    <div className="session-history-panel">
      <div className="panel-header">
        <h3>Sessions</h3>
        <button onClick={handleNewSession} className="new-session-btn" title="New Session">+</button>
      </div>
      {isLoading && sessions.length === 0 ? (
        <div className="loader">Loading...</div>
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
                    if (!session.created_at) return '刚刚';
                    const date = new Date(session.created_at * 1000); // Convert Unix timestamp to milliseconds
                    return isNaN(date.getTime()) ? '刚刚' : date.toLocaleString('zh-CN', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    });
                  })()}
                </span>
              </div>
              <button onClick={(e) => handleDeleteSession(session.id, e)} className="delete-btn" title="Delete Session">×</button>
            </li>
          ))}
        </ul>
      )}
      <style>{`
        .session-history-panel {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          background-color: #f8f9fc; /* Light, clean background */
          color: #374151; /* Darker text for readability */
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb; /* Subtle separator */
        }
        .panel-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
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
          transition: all 0.2s;
        }
        .new-session-btn:hover {
          background-color: #4f46e5;
          color: #fff;
          border-color: #4f46e5;
        }
        .loader {
          padding: 16px;
          text-align: center;
          color: #6b7280;
        }
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
          transition: opacity 0.2s, color 0.2s, background-color 0.2s;
        }
        .session-item:hover .delete-btn {
          visibility: visible;
          opacity: 1;
        }
        .delete-btn:hover {
          color: #ef4444; // Red for delete
          background-color: #fee2e2;
        }
      `}</style>
    </div>
  );
};
