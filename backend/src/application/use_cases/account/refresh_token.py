"""
刷新Token用例

处理账户Token刷新的业务逻辑
"""

import logging
from datetime import datetime
from uuid import UUID

from src.application.dto import RefreshTokenDTO
from src.application.interfaces import IOAuthClient
from src.config.settings import settings
from src.domain.exceptions import (
    AccountNotFoundException,
    TokenRefreshFailedException,
)
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.services import ITokenService
from src.domain.value_objects import Credentials

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    """刷新Token用例"""
    
    def __init__(
        self,
        account_repository: IAccountRepository,
        oauth_client: IOAuthClient,
        token_service: ITokenService
    ):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
            oauth_client: OAuth客户端
            token_service: Token服务
        """
        self._account_repository = account_repository
        self._oauth_client = oauth_client
        self._token_service = token_service
    
    async def execute(self, account_id: UUID) -> RefreshTokenDTO:
        """
        执行Token刷新
        
        Args:
            account_id: 账户ID
            
        Returns:
            RefreshTokenDTO: 刷新结果DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
            TokenRefreshFailedException: Token刷新失败
        """
        logger.info(f"Refreshing token for account: {account_id}")
        
        # 获取账户
        account = await self._account_repository.get_by_id(account_id)
        
        if not account:
            logger.warning(f"Account not found: {account_id}")
            raise AccountNotFoundException(str(account_id))
        
        # 检查是否可以刷新
        if not account.can_refresh():
            error_msg = "Account cannot be refreshed (inactive or already in progress)"
            logger.warning(f"{error_msg}: {account_id}")
            return RefreshTokenDTO(
                success=False,
                message=error_msg,
                refresh_time=datetime.utcnow()
            )
        
        try:
            # 标记为刷新中
            account.mark_refresh_in_progress()
            await self._account_repository.update(account)
            
            # 创建凭证对象
            credentials = Credentials.create(
                account.client_id,
                account.refresh_token
            )
            
            # 执行刷新
            access_token, new_refresh_token = await self._oauth_client.refresh_token(
                credentials
            )
            
            # 如果有新的refresh_token，更新它
            if new_refresh_token:
                account.update_refresh_token(new_refresh_token)
            else:
                # 标记刷新成功（即使没有新token）
                account.mark_refresh_in_progress()  # 重置状态
                account.update_refresh_token(account.refresh_token)
            
            # 计算下次刷新时间
            next_refresh_time = self._token_service.calculate_next_refresh_time(
                interval_days=settings.TOKEN_REFRESH_INTERVAL_DAYS
            )
            account.schedule_next_refresh(next_refresh_time)
            
            # 保存更新
            await self._account_repository.update(account)
            
            logger.info(f"Token refreshed successfully for account: {account_id}")
            
            return RefreshTokenDTO(
                success=True,
                message="Token refreshed successfully",
                refresh_time=datetime.utcnow(),
                next_refresh_time=next_refresh_time
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to refresh token for account {account_id}: {error_msg}")
            
            # 标记刷新失败
            account.mark_refresh_failed(error_msg)
            await self._account_repository.update(account)
            
            raise TokenRefreshFailedException(account.email_str, error_msg)

