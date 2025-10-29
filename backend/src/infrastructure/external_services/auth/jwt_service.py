"""
JWT服务实现

处理JWT Token的生成和验证
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt

from src.config.settings import settings
from src.domain.exceptions import TokenExpiredException, TokenInvalidException

logger = logging.getLogger(__name__)


class JWTService:
    """JWT服务"""
    
    def __init__(self):
        """初始化JWT服务"""
        self._secret_key = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._access_token_expire_hours = settings.JWT_EXPIRE_HOURS
    
    def create_access_token(
        self,
        admin_id: UUID,
        username: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            admin_id: 管理员ID
            username: 用户名
            expires_delta: 过期时间差（可选）
            
        Returns:
            str: JWT Token字符串
        """
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self._access_token_expire_hours)
        
        # 构建载荷
        payload = {
            "sub": str(admin_id),  # subject (主题) - 管理员ID
            "username": username,
            "exp": expire,  # expiration time
            "iat": datetime.utcnow(),  # issued at
            "type": "access"
        }
        
        # 生成Token
        encoded_jwt = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        
        logger.debug(f"Created access token for user: {username}")
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """
        验证并解析Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            dict: Token载荷
            
        Raises:
            TokenExpiredException: Token已过期
            TokenInvalidException: Token无效
        """
        try:
            # 解码Token
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            
            # 检查Token类型
            if payload.get("type") != "access":
                raise TokenInvalidException("Invalid token type")
            
            logger.debug(f"Token verified for user: {payload.get('username')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise TokenExpiredException("Token has expired")
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise TokenInvalidException(f"Invalid token: {str(e)}")
    
    def get_admin_id_from_token(self, token: str) -> UUID:
        """
        从Token中提取管理员ID
        
        Args:
            token: JWT Token字符串
            
        Returns:
            UUID: 管理员ID
            
        Raises:
            TokenExpiredException: Token已过期
            TokenInvalidException: Token无效
        """
        payload = self.verify_token(token)
        
        try:
            admin_id = UUID(payload.get("sub"))
            return admin_id
        except (ValueError, TypeError) as e:
            raise TokenInvalidException(f"Invalid admin ID in token: {str(e)}")
    
    def get_username_from_token(self, token: str) -> str:
        """
        从Token中提取用户名
        
        Args:
            token: JWT Token字符串
            
        Returns:
            str: 用户名
            
        Raises:
            TokenExpiredException: Token已过期
            TokenInvalidException: Token无效
        """
        payload = self.verify_token(token)
        
        username = payload.get("username")
        if not username:
            raise TokenInvalidException("Username not found in token")
        
        return username
    
    def refresh_access_token(self, old_token: str) -> str:
        """
        刷新访问令牌
        
        Args:
            old_token: 旧的JWT Token
            
        Returns:
            str: 新的JWT Token
            
        Raises:
            TokenInvalidException: Token无效
        """
        # 验证旧Token（允许过期）
        try:
            payload = jwt.decode(
                old_token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False}  # 不验证过期时间
            )
        except JWTError as e:
            raise TokenInvalidException(f"Invalid token: {str(e)}")
        
        # 提取信息
        admin_id = UUID(payload.get("sub"))
        username = payload.get("username")
        
        # 生成新Token
        return self.create_access_token(admin_id, username)


# 单例实例
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """
    获取JWT服务实例（单例）
    
    Returns:
        JWTService: JWT服务实例
    """
    global _jwt_service
    
    if _jwt_service is None:
        _jwt_service = JWTService()
        logger.info("JWT service initialized")
    
    return _jwt_service

