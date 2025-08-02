import sqlite3
import json
import uuid
import time
from backend.models.session import Session, SessionData, SessionMetadata
from typing import List, Optional

DB_PATH = 'proteindance.db'

class SessionManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._create_table()

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self):
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    session_data TEXT NOT NULL,
                    user_id INTEGER NULL
                )
            ''')
            # 添加user_id列（如果不存在）
            try:
                conn.execute('ALTER TABLE sessions ADD COLUMN user_id INTEGER NULL')
                conn.commit()
            except sqlite3.OperationalError:
                # 列已存在，忽略错误
                pass

    def save_session(self, session_data: SessionData, session_id: Optional[str] = None, user_id: Optional[int] = None) -> Session:
        """Saves a new session or updates an existing one."""
        now = time.time()
        title = session_data.disease or f"Session {int(now)}"
        
        if session_id:
            # Update existing session
            with self._get_db_connection() as conn:
                conn.execute(
                    "UPDATE sessions SET title = ?, updated_at = ?, session_data = ?, user_id = ? WHERE id = ?",
                    (title, now, json.dumps(session_data.dict()), user_id, session_id)
                )
                conn.commit()
            return self.get_session(session_id)
        else:
            # Create new session
            new_id = str(uuid.uuid4())
            session = Session(
                id=new_id,
                title=title,
                created_at=now,
                updated_at=now,
                session_data=session_data,
                user_id=user_id
            )
            with self._get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO sessions (id, title, created_at, updated_at, session_data, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (session.id, session.title, session.created_at, session.updated_at, json.dumps(session.session_data.dict()), user_id)
                )
                conn.commit()
            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieves a full session by its ID."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                session_data_dict = json.loads(row['session_data'])
                # 安全地获取user_id字段
                try:
                    user_id = row['user_id']
                except (KeyError, IndexError):
                    user_id = None
                    
                return Session(
                    id=row['id'],
                    title=row['title'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    session_data=SessionData(**session_data_dict),
                    user_id=user_id
                )
        return None

    def list_sessions(self, user_id: Optional[int] = None) -> List[SessionMetadata]:
        """Lists sessions with minimal metadata, sorted by last updated.
        If user_id is provided, only returns sessions for that user and public sessions."""
        with self._get_db_connection() as conn:
            if user_id is not None:
                # 只返回该用户的会话
                cursor = conn.execute(
                    "SELECT id, title, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,)
                )
            else:
                # 对于未登录用户，不返回任何会话（强制要求登录）
                return []
            rows = cursor.fetchall()
            return [SessionMetadata(id=row['id'], title=row['title'], created_at=row['created_at'], updated_at=row['updated_at']) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session by its ID."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

session_manager = SessionManager()
