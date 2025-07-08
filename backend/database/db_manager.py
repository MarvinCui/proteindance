"""
SQLite数据库管理器
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from ..models.user import (
    User, UserCreate, UserLogin, UserStatus,
    ConversationSession, ConversationMessage,
    VerificationToken
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "proteindance.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    status TEXT DEFAULT 'pending_verification',
                    email_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # 验证令牌表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    token_type TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 对话会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 对话消息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    disease_name TEXT,
                    innovation_level INTEGER,
                    step INTEGER,
                    result_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES conversation_sessions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def hash_password(self, password: str) -> str:
        """加密密码"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${password_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = hashed.split('$')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == stored_hash
        except ValueError:
            return False
    
    def generate_token(self) -> str:
        """生成验证令牌"""
        return secrets.token_urlsafe(32)
    
    # 用户管理方法
    def create_user(self, user_data: UserCreate) -> Optional[User]:
        """创建用户"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查邮箱是否已存在
                cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
                if cursor.fetchone():
                    return None
                
                password_hash = self.hash_password(user_data.password)
                
                cursor.execute('''
                    INSERT INTO users (email, username, password_hash)
                    VALUES (?, ?, ?)
                ''', (user_data.email, user_data.username, password_hash))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return self.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                
                if row:
                    return User(**dict(row))
                return None
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return User(**dict(row))
                return None
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
    
    def update_user_status(self, user_id: int, status: UserStatus, email_verified: bool = None) -> Optional[User]:
        """更新用户状态和邮件验证状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if email_verified is not None:
                    cursor.execute('''
                        UPDATE users 
                        SET status = ?, email_verified = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (status.value, email_verified, user_id))
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET status = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (status.value, user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return self.get_user_by_id(user_id)
                return None
                
        except Exception as e:
            logger.error(f"更新用户状态失败: {e}")
            return None
    
    def verify_user_email(self, user_id: int) -> bool:
        """验证用户邮箱"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET email_verified = TRUE, status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (UserStatus.ACTIVE.value, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"验证邮箱失败: {e}")
            return False
    
    def update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新登录时间失败: {e}")
            return False
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """更新密码"""
        try:
            password_hash = self.hash_password(new_password)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (password_hash, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新密码失败: {e}")
            return False
    
    # 验证令牌管理
    def create_verification_token(self, user_id: int, token_type: str, 
                                expires_hours: int = 24) -> str:
        """创建验证令牌"""
        try:
            token = self.generate_token()
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO verification_tokens 
                    (user_id, token, token_type, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, token, token_type, expires_at))
                conn.commit()
                
            return token
        except Exception as e:
            logger.error(f"创建验证令牌失败: {e}")
            return ""
    
    def verify_token(self, token: str, token_type: str) -> Optional[int]:
        """验证令牌并返回用户ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id FROM verification_tokens 
                    WHERE token = ? AND token_type = ? 
                    AND used = FALSE AND expires_at > CURRENT_TIMESTAMP
                ''', (token, token_type))
                
                row = cursor.fetchone()
                if row:
                    # 标记令牌为已使用
                    cursor.execute('''
                        UPDATE verification_tokens 
                        SET used = TRUE 
                        WHERE token = ?
                    ''', (token,))
                    conn.commit()
                    return row[0]
                
                return None
        except Exception as e:
            logger.error(f"验证令牌失败: {e}")
            return None
    
    # 对话会话管理
    def create_session(self, user_id: int, title: str) -> Optional[ConversationSession]:
        """创建对话会话"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversation_sessions (user_id, title)
                    VALUES (?, ?)
                ''', (user_id, title))
                
                session_id = cursor.lastrowid
                conn.commit()
                
                return self.get_session_by_id(session_id)
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def get_session_by_id(self, session_id: int) -> Optional[ConversationSession]:
        """根据ID获取会话"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM conversation_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return ConversationSession(**dict(row))
                return None
        except Exception as e:
            logger.error(f"查询会话失败: {e}")
            return None
    
    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[ConversationSession]:
        """获取用户的对话会话列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversation_sessions 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY updated_at DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                return [ConversationSession(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"查询用户会话失败: {e}")
            return []
    
    def update_session(self, session_id: int, title: Optional[str] = None, 
                      is_active: Optional[bool] = None) -> bool:
        """更新会话"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if title is not None:
                    updates.append("title = ?")
                    params.append(title)
                
                if is_active is not None:
                    updates.append("is_active = ?")
                    params.append(is_active)
                
                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(session_id)
                    
                    query = f"UPDATE conversation_sessions SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount > 0
                
                return False
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return False
    
    # 对话消息管理
    def add_message(self, session_id: int, user_id: int, message_type: str,
                   content: str, disease_name: Optional[str] = None,
                   innovation_level: Optional[int] = None,
                   step: Optional[int] = None,
                   result_data: Optional[dict] = None) -> Optional[ConversationMessage]:
        """添加对话消息"""
        try:
            import json
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversation_messages 
                    (session_id, user_id, message_type, content, disease_name, 
                     innovation_level, step, result_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, user_id, message_type, content, disease_name,
                      innovation_level, step, json.dumps(result_data) if result_data else None))
                
                message_id = cursor.lastrowid
                
                # 更新会话的更新时间
                cursor.execute('''
                    UPDATE conversation_sessions 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (session_id,))
                
                conn.commit()
                
                return self.get_message_by_id(message_id)
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return None
    
    def get_message_by_id(self, message_id: int) -> Optional[ConversationMessage]:
        """根据ID获取消息"""
        try:
            import json
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM conversation_messages WHERE id = ?", (message_id,))
                row = cursor.fetchone()
                
                if row:
                    data = dict(row)
                    if data.get('result_data'):
                        data['result_data'] = json.loads(data['result_data'])
                    return ConversationMessage(**data)
                return None
        except Exception as e:
            logger.error(f"查询消息失败: {e}")
            return None
    
    def get_session_messages(self, session_id: int, limit: int = 100) -> List[ConversationMessage]:
        """获取会话的消息列表"""
        try:
            import json
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversation_messages 
                    WHERE session_id = ? 
                    ORDER BY created_at ASC 
                    LIMIT ?
                ''', (session_id, limit))
                
                rows = cursor.fetchall()
                messages = []
                for row in rows:
                    data = dict(row)
                    if data.get('result_data'):
                        data['result_data'] = json.loads(data['result_data'])
                    messages.append(ConversationMessage(**data))
                
                return messages
        except Exception as e:
            logger.error(f"查询会话消息失败: {e}")
            return []