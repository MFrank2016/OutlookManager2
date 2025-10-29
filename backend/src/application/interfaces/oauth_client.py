"""
OAuth客户端接口

定义OAuth操作的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.value_objects import AccessToken, Credentials


class IOAuthClient(ABC):
    """
    OAuth客户端接口
    
    定义OAuth2认证和Token刷新的方法
    具体实现在基础设施层
    """
    
    @abstractmethod
    async def refresh_token(
        self,
        credentials: Credentials
    ) -> tuple[AccessToken, Optional[str]]:
        """
        刷新访问令牌
        
        Args:
            credentials: OAuth凭证
            
        Returns:
            tuple[AccessToken, Optional[str]]: (访问令牌, 新的refresh_token如果有)
            
        Raises:
            OAuthException: OAuth操作失败
            InvalidRefreshTokenException: 刷新令牌无效
        """
        pass
    
    @abstractmethod
    async def validate_token(self, access_token: AccessToken) -> bool:
        """
        验证访问令牌是否有效
        
        Args:
            access_token: 访问令牌
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, refresh_token: str) -> bool:
        """
        撤销刷新令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            bool: 是否撤销成功
        """
        pass

