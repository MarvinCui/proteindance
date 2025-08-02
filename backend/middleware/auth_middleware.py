"""
认证中间件
提供JWT令牌验证和用户认证功能
"""
import logging
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.auth_service import AuthService
from ..models.user import User

logger = logging.getLogger(__name__)

# 创建HTTP Bearer令牌方案
security = HTTPBearer()

class AuthMiddleware:
    def __init__(self):
        self.auth_service = AuthService()
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """
        从JWT令牌中获取当前用户
        """
        try:
            token = credentials.credentials
            user = self.auth_service.get_current_user(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
            
        except Exception as e:
            logger.error(f"认证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_active_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """
        获取当前激活的用户（已验证邮箱）
        """
        current_user = self.get_current_user(credentials)
        
        if not current_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        
        return current_user
    
    def get_optional_user(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
        """
        可选的用户认证（允许未登录用户访问）
        """
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            return self.auth_service.get_current_user(token)
        except:
            return None

# 创建中间件实例
auth_middleware = AuthMiddleware()

# 常用的依赖注入函数
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户的依赖注入函数"""
    return auth_middleware.get_current_user(credentials)

def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前激活用户的依赖注入函数"""
    return auth_middleware.get_current_active_user(credentials)

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """可选用户认证的依赖注入函数"""
    return auth_middleware.get_optional_user(credentials)