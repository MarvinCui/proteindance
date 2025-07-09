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
                    session_data TEXT NOT NULL
                )
            ''')
            conn.commit()

    def save_session(self, session_data: SessionData, session_id: Optional[str] = None) -> Session:
        """Saves a new session or updates an existing one."""
        now = time.time()
        title = session_data.disease or f"Session {int(now)}"
        
        if session_id:
            # Update existing session
            with self._get_db_connection() as conn:
                conn.execute(
                    "UPDATE sessions SET title = ?, updated_at = ?, session_data = ? WHERE id = ?",
                    (title, now, json.dumps(session_data.dict()), session_id)
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
                session_data=session_data
            )
            with self._get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO sessions (id, title, created_at, updated_at, session_data) VALUES (?, ?, ?, ?, ?)",
                    (session.id, session.title, session.created_at, session.updated_at, json.dumps(session.session_data.dict()))
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
                return Session(
                    id=row['id'],
                    title=row['title'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    session_data=SessionData(**session_data_dict)
                )
        return None

    def list_sessions(self) -> List[SessionMetadata]:
        """Lists all sessions with minimal metadata, sorted by last updated."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [SessionMetadata(id=row['id'], title=row['title'], created_at=row['created_at'], updated_at=row['updated_at']) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session by its ID."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

session_manager = SessionManager()
