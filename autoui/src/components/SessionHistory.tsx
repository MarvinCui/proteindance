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
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
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
              <span className="session-title">{session.title}</span>
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
          padding: 10px 12px;
          margin-bottom: 4px;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.2s, color 0.2s;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
          color: #374151;
        }
        .session-item:hover {
          background-color: #f3f4f6; /* Light gray hover */
        }
        .session-item.active {
          background-color: #eef2ff; /* Indigo light */
          color: #4338ca; /* Indigo dark text */
          font-weight: 600;
        }
        .session-title {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          flex-grow: 1;
          margin-right: 8px;
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
