"""
Token服务实现

实现Token管理的具体逻辑
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.application.interfaces import IOAuthClient
from src.domain.services import ITokenService
from src.domain.value_objects import AccessToken, Credentials

logger = logging.getLogger(__name__)


class TokenServiceImpl(ITokenService):
    """Token管理服务实现"""
    
    def __init__(self, oauth_client: IOAuthClient):
        """
        初始化Token服务
        
        Args:
            oauth_client: OAuth客户端
        """
        self._oauth_client = oauth_client
    
    async def refresh_access_token(
        self,
        credentials: Credentials
    ) -> tuple[AccessToken, Optional[str]]:
        """刷新访问令牌"""
        return await self._oauth_client.refresh_token(credentials)
    
    async def validate_access_token(self, token: AccessToken) -> bool:
        """验证访问令牌是否有效"""
        return await self._oauth_client.validate_token(token)
    
    def calculate_next_refresh_time(
        self,
        current_time: Optional[datetime] = None,
        interval_days: int = 3
    ) -> datetime:
        """计算下次刷新时间"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        return current_time + timedelta(days=interval_days)
    
    def should_refresh_token(
        self,
        last_refresh_time: Optional[datetime],
        next_refresh_time: Optional[datetime]
    ) -> bool:
        """判断是否应该刷新Token"""
        # 如果没有设置下次刷新时间，应该刷新
        if next_refresh_time is None:
            return True
        
        # 如果当前时间已超过下次刷新时间，应该刷新
        return datetime.utcnow() >= next_refresh_time

