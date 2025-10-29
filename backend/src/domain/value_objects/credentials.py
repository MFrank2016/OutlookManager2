"""
OAuth凭证值对象

表示不可变的OAuth2认证凭证
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.exceptions import ValidationException


@dataclass(frozen=True)
class Credentials:
    """
    OAuth2凭证值对象
    
    特性：
    - 不可变（frozen=True）
    - 自动验证格式
    - 包含client_id和refresh_token
    """
    
    client_id: str
    refresh_token: str
    
    def __post_init__(self):
        """初始化后验证"""
        self._validate()
    
    def _validate(self) -> None:
        """验证凭证数据"""
        if not self.client_id or not self.client_id.strip():
            raise ValidationException(
                "Client ID cannot be empty",
                {"field": "client_id"}
            )
        
        if not self.refresh_token or not self.refresh_token.strip():
            raise ValidationException(
                "Refresh token cannot be empty",
                {"field": "refresh_token"}
            )
        
        # 基本长度验证
        if len(self.client_id) < 10:
            raise ValidationException(
                "Invalid client ID format",
                {"field": "client_id", "length": len(self.client_id)}
            )
        
        if len(self.refresh_token) < 10:
            raise ValidationException(
                "Invalid refresh token format",
                {"field": "refresh_token", "length": len(self.refresh_token)}
            )
    
    @classmethod
    def create(cls, client_id: str, refresh_token: str) -> "Credentials":
        """
        工厂方法创建Credentials
        
        Args:
            client_id: Azure客户端ID
            refresh_token: OAuth2刷新令牌
            
        Returns:
            Credentials: 凭证值对象
        """
        return cls(client_id=client_id, refresh_token=refresh_token)
    
    def mask_refresh_token(self, visible_chars: int = 10) -> str:
        """
        获取掩码后的refresh_token（用于日志等场景）
        
        Args:
            visible_chars: 可见字符数
            
        Returns:
            str: 掩码后的token
        """
        if len(self.refresh_token) <= visible_chars:
            return "***"
        
        return f"{self.refresh_token[:visible_chars]}...***"
    
    def __str__(self) -> str:
        return f"Credentials(client_id={self.client_id[:10]}..., refresh_token=***)"
    
    def __repr__(self) -> str:
        return f"Credentials(client_id='{self.client_id}', refresh_token='***')"

