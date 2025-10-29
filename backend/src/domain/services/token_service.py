"""
Token服务

处理Token刷新和验证的领域服务
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from src.domain.value_objects import AccessToken, Credentials


class ITokenService(ABC):
    """
    Token管理服务接口
    
    定义Token刷新和验证的业务逻辑
    具体实现在基础设施层
    """
    
    @abstractmethod
    async def refresh_access_token(
        self,
        credentials: Credentials
    ) -> tuple[AccessToken, Optional[str]]:
        """
        刷新访问令牌
        
        Args:
            credentials: OAuth凭证
            
        Returns:
            tuple[AccessToken, Optional[str]]: (访问令牌, 新的refresh_token如果有更新)
            
        Raises:
            OAuthException: OAuth刷新失败
            InvalidRefreshTokenException: 刷新令牌无效
        """
        pass
    
    @abstractmethod
    async def validate_access_token(self, token: AccessToken) -> bool:
        """
        验证访问令牌是否有效
        
        Args:
            token: 访问令牌
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    def calculate_next_refresh_time(
        self,
        current_time: Optional[datetime] = None,
        interval_days: int = 3
    ) -> datetime:
        """
        计算下次刷新时间
        
        Args:
            current_time: 当前时间（默认为utcnow）
            interval_days: 刷新间隔天数
            
        Returns:
            datetime: 下次刷新时间
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        return current_time + timedelta(days=interval_days)
    
    @abstractmethod
    def should_refresh_token(
        self,
        last_refresh_time: Optional[datetime],
        next_refresh_time: Optional[datetime]
    ) -> bool:
        """
        判断是否应该刷新Token
        
        Args:
            last_refresh_time: 最后刷新时间
            next_refresh_time: 下次刷新时间
            
        Returns:
            bool: 是否应该刷新
        """
        # 如果没有设置下次刷新时间，应该刷新
        if next_refresh_time is None:
            return True
        
        # 如果当前时间已超过下次刷新时间，应该刷新
        return datetime.utcnow() >= next_refresh_time

