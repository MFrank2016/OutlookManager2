"""
访问令牌值对象

表示不可变的OAuth2访问令牌及其元数据
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.domain.exceptions import ValidationException


@dataclass(frozen=True)
class AccessToken:
    """
    访问令牌值对象
    
    特性：
    - 不可变（frozen=True）
    - 包含token和过期时间
    - 提供过期判断方法
    """
    
    value: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    def __post_init__(self):
        """初始化后验证"""
        self._validate()
    
    def _validate(self) -> None:
        """验证令牌数据"""
        if not self.value or not self.value.strip():
            raise ValidationException(
                "Access token cannot be empty",
                {"field": "value"}
            )
        
        if len(self.value) < 10:
            raise ValidationException(
                "Invalid access token format",
                {"field": "value", "length": len(self.value)}
            )
        
        if not self.token_type or not self.token_type.strip():
            raise ValidationException(
                "Token type cannot be empty",
                {"field": "token_type"}
            )
    
    @classmethod
    def create(
        cls,
        value: str,
        expires_in: int,
        token_type: str = "Bearer"
    ) -> "AccessToken":
        """
        工厂方法创建AccessToken
        
        Args:
            value: 访问令牌字符串
            expires_in: 过期秒数（从现在开始）
            token_type: 令牌类型（默认Bearer）
            
        Returns:
            AccessToken: 访问令牌值对象
        """
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return cls(value=value, expires_at=expires_at, token_type=token_type)
    
    @classmethod
    def create_with_expiry(
        cls,
        value: str,
        expires_at: datetime,
        token_type: str = "Bearer"
    ) -> "AccessToken":
        """
        使用具体过期时间创建AccessToken
        
        Args:
            value: 访问令牌字符串
            expires_at: 具体过期时间
            token_type: 令牌类型（默认Bearer）
            
        Returns:
            AccessToken: 访问令牌值对象
        """
        return cls(value=value, expires_at=expires_at, token_type=token_type)
    
    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        判断令牌是否已过期
        
        Args:
            buffer_seconds: 缓冲时间（秒），提前判定过期以避免边界情况
            
        Returns:
            bool: 是否已过期
        """
        now = datetime.utcnow()
        expiry_with_buffer = self.expires_at - timedelta(seconds=buffer_seconds)
        return now >= expiry_with_buffer
    
    def is_valid(self) -> bool:
        """
        判断令牌是否有效
        
        Returns:
            bool: 是否有效（未过期）
        """
        return not self.is_expired()
    
    def time_until_expiry(self) -> timedelta:
        """
        获取距离过期的时间
        
        Returns:
            timedelta: 距离过期的时间差
        """
        return self.expires_at - datetime.utcnow()
    
    def seconds_until_expiry(self) -> int:
        """
        获取距离过期的秒数
        
        Returns:
            int: 距离过期的秒数（可能为负数表示已过期）
        """
        delta = self.time_until_expiry()
        return int(delta.total_seconds())
    
    def mask_value(self, visible_chars: int = 10) -> str:
        """
        获取掩码后的token值（用于日志等场景）
        
        Args:
            visible_chars: 可见字符数
            
        Returns:
            str: 掩码后的token
        """
        if len(self.value) <= visible_chars:
            return "***"
        
        return f"{self.value[:visible_chars]}...***"
    
    def __str__(self) -> str:
        status = "valid" if self.is_valid() else "expired"
        return f"AccessToken(type={self.token_type}, status={status})"
    
    def __repr__(self) -> str:
        return (
            f"AccessToken(value='***', expires_at={self.expires_at.isoformat()}, "
            f"token_type='{self.token_type}')"
        )

