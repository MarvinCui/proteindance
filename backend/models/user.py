"""
用户管理相关的数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"

class User(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    username: str
    password_hash: str
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerification(BaseModel):
    token: str

# 对话相关模型
class ConversationSession(BaseModel):
    id: Optional[int] = None
    user_id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

class ConversationMessage(BaseModel):
    id: Optional[int] = None
    session_id: int
    user_id: int
    message_type: str  # 'user' 或 'system'
    content: str
    disease_name: Optional[str] = None
    innovation_level: Optional[int] = None
    step: Optional[int] = None
    result_data: Optional[dict] = None
    created_at: Optional[datetime] = None

class SessionCreate(BaseModel):
    title: str

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

# 验证令牌模型
class VerificationToken(BaseModel):
    id: Optional[int] = None
    user_id: int
    token: str
    token_type: str  # 'email_verification' 或 'password_reset'
    expires_at: datetime
    used: bool = False
    created_at: Optional[datetime] = None