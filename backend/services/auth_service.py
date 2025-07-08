"""
用户认证服务
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from ..database.db_manager import DatabaseManager
from ..models.user import User, UserCreate, UserLogin, UserStatus
from .email_service import EmailService

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.jwt_expire_hours = int(os.getenv('JWT_EXPIRE_HOURS', '24'))
        # 邮件验证控制
        self.email_verification_enabled = os.getenv('EMAIL_VERIFICATION_ENABLED', 'false').lower() == 'true'
    
    def generate_jwt_token(self, user: User) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expire_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT令牌无效: {e}")
            return None
    
    def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 检查邮箱是否已存在
            existing_user = self.db.get_user_by_email(user_data.email)
            if existing_user:
                return {
                    "success": False,
                    "error": "邮箱已被注册",
                    "error_code": "EMAIL_EXISTS"
                }
            
            # 创建用户
            user = self.db.create_user(user_data)
            if not user:
                return {
                    "success": False,
                    "error": "用户创建失败",
                    "error_code": "CREATE_FAILED"
                }
            
            if self.email_verification_enabled:
                # 启用邮件验证
                verification_token = self.db.create_verification_token(
                    user.id, 
                    'email_verification', 
                    expires_hours=24
                )
                
                if not verification_token:
                    return {
                        "success": False,
                        "error": "验证令牌生成失败",
                        "error_code": "TOKEN_FAILED"
                    }
                
                email_sent = self.email_service.send_verification_email(
                    user.email, 
                    user.username, 
                    verification_token
                )
                
                if not email_sent:
                    logger.warning(f"验证邮件发送失败: {user.email}")
                
                activated_user = user
                
            else:
                # 关闭邮件验证，直接激活用户
                logger.info(f"邮件验证已关闭，直接激活用户: {user.email}")
                
                activated_user = self.db.update_user_status(
                    user.id, 
                    UserStatus.ACTIVE, 
                    email_verified=True
                )
                
                if not activated_user:
                    logger.warning(f"用户激活失败: {user.email}")
                    activated_user = user
                
                email_sent = True
            
            message = "注册成功！" + (
                "请查收验证邮件" if self.email_verification_enabled 
                else "用户已自动激活（邮件验证已关闭）"
            )
            
            return {
                "success": True,
                "message": message,
                "user": {
                    "id": activated_user.id,
                    "email": activated_user.email,
                    "username": activated_user.username,
                    "status": activated_user.status,
                    "email_verified": activated_user.email_verified
                },
                "email_sent": email_sent,
                "auto_activated": not self.email_verification_enabled,
                "email_verification_enabled": self.email_verification_enabled
            }
            
        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            return {
                "success": False,
                "error": "注册过程中发生错误",
                "error_code": "REGISTRATION_ERROR"
            }
    
    def login(self, login_data: UserLogin) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 查找用户
            user = self.db.get_user_by_email(login_data.email)
            if not user:
                return {
                    "success": False,
                    "error": "邮箱或密码错误",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # 验证密码
            if not self.db.verify_password(login_data.password, user.password_hash):
                return {
                    "success": False,
                    "error": "邮箱或密码错误",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # 检查用户状态
            if user.status == UserStatus.SUSPENDED:
                return {
                    "success": False,
                    "error": "账户已被暂停",
                    "error_code": "ACCOUNT_SUSPENDED"
                }
            
            # 生成JWT令牌
            token = self.generate_jwt_token(user)
            
            # 更新最后登录时间
            self.db.update_last_login(user.id)
            
            return {
                "success": True,
                "message": "登录成功",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "status": user.status,
                    "email_verified": user.email_verified
                },
                "token": token,
                "requires_verification": self.email_verification_enabled and not user.email_verified
            }
            
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return {
                "success": False,
                "error": "登录过程中发生错误",
                "error_code": "LOGIN_ERROR"
            }
    
    def verify_email(self, token: str) -> Dict[str, Any]:
        """验证邮箱"""
        try:
            user_id = self.db.verify_token(token, 'email_verification')
            if not user_id:
                return {
                    "success": False,
                    "error": "验证链接无效或已过期",
                    "error_code": "INVALID_TOKEN"
                }
            
            # 验证用户邮箱
            success = self.db.verify_user_email(user_id)
            if not success:
                return {
                    "success": False,
                    "error": "邮箱验证失败",
                    "error_code": "VERIFICATION_FAILED"
                }
            
            return {
                "success": True,
                "message": "邮箱验证成功！"
            }
            
        except Exception as e:
            logger.error(f"邮箱验证失败: {e}")
            return {
                "success": False,
                "error": "验证过程中发生错误",
                "error_code": "VERIFICATION_ERROR"
            }
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """请求密码重置"""
        try:
            user = self.db.get_user_by_email(email)
            if not user:
                # 为了安全，即使用户不存在也返回成功
                return {
                    "success": True,
                    "message": "如果该邮箱已注册，您将收到密码重置邮件"
                }
            
            # 生成密码重置令牌
            reset_token = self.db.create_verification_token(
                user.id,
                'password_reset',
                expires_hours=2  # 密码重置链接2小时有效
            )
            
            if not reset_token:
                return {
                    "success": False,
                    "error": "重置令牌生成失败",
                    "error_code": "TOKEN_FAILED"
                }
            
            # 发送重置邮件
            email_sent = self.email_service.send_password_reset_email(
                user.email,
                user.username,
                reset_token
            )
            
            return {
                "success": True,
                "message": "如果该邮箱已注册，您将收到密码重置邮件",
                "email_sent": email_sent
            }
            
        except Exception as e:
            logger.error(f"密码重置请求失败: {e}")
            return {
                "success": False,
                "error": "重置请求过程中发生错误",
                "error_code": "RESET_REQUEST_ERROR"
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """重置密码"""
        try:
            user_id = self.db.verify_token(token, 'password_reset')
            if not user_id:
                return {
                    "success": False,
                    "error": "重置链接无效或已过期",
                    "error_code": "INVALID_TOKEN"
                }
            
            # 更新密码
            success = self.db.update_password(user_id, new_password)
            if not success:
                return {
                    "success": False,
                    "error": "密码更新失败",
                    "error_code": "UPDATE_FAILED"
                }
            
            return {
                "success": True,
                "message": "密码重置成功！"
            }
            
        except Exception as e:
            logger.error(f"密码重置失败: {e}")
            return {
                "success": False,
                "error": "重置过程中发生错误",
                "error_code": "RESET_ERROR"
            }
    
    def get_current_user(self, token: str) -> Optional[User]:
        """根据JWT令牌获取当前用户"""
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        return self.db.get_user_by_id(payload['user_id'])
    
    def resend_verification_email(self, user_id: int) -> Dict[str, Any]:
        """重新发送验证邮件"""
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error": "用户不存在",
                    "error_code": "USER_NOT_FOUND"
                }
            
            if user.email_verified:
                return {
                    "success": False,
                    "error": "邮箱已验证",
                    "error_code": "ALREADY_VERIFIED"
                }
            
            # 生成新的验证令牌
            verification_token = self.db.create_verification_token(
                user.id,
                'email_verification',
                expires_hours=24
            )
            
            if not verification_token:
                return {
                    "success": False,
                    "error": "验证令牌生成失败",
                    "error_code": "TOKEN_FAILED"
                }
            
            # 发送验证邮件
            email_sent = self.email_service.send_verification_email(
                user.email,
                user.username,
                verification_token
            )
            
            return {
                "success": True,
                "message": "验证邮件已重新发送",
                "email_sent": email_sent
            }
            
        except Exception as e:
            logger.error(f"重新发送验证邮件失败: {e}")
            return {
                "success": False,
                "error": "发送过程中发生错误",
                "error_code": "RESEND_ERROR"
            }