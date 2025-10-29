"""
更新账户用例

处理账户信息的更新逻辑
"""

import logging
from uuid import UUID

from src.application.dto import AccountDTO, UpdateAccountDTO
from src.domain.entities import Account
from src.domain.exceptions import AccountNotFoundException
from src.domain.repositories.account_repository import IAccountRepository

logger = logging.getLogger(__name__)


class UpdateAccountUseCase:
    """更新账户用例"""
    
    def __init__(self, account_repository: IAccountRepository):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
        """
        self._account_repository = account_repository
    
    async def execute(
        self,
        account_id: UUID,
        dto: UpdateAccountDTO
    ) -> AccountDTO:
        """
        执行更新账户
        
        Args:
            account_id: 账户ID
            dto: 更新数据DTO
            
        Returns:
            AccountDTO: 更新后的账户DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
        """
        logger.info(f"Updating account: {account_id}")
        
        # 获取现有账户
        account = await self._account_repository.get_by_id(account_id)
        
        if not account:
            logger.warning(f"Account not found: {account_id}")
            raise AccountNotFoundException(str(account_id))
        
        # 更新标签
        if dto.tags is not None:
            account.update_tags(dto.tags)
            logger.info(f"Updated tags for account {account_id}")
        
        # 更新状态
        if dto.status is not None:
            if dto.status != account.status:
                # 根据状态调用相应方法
                if dto.status.value == "active":
                    account.activate()
                elif dto.status.value == "inactive":
                    account.deactivate()
                elif dto.status.value == "suspended":
                    account.suspend()
                
                logger.info(f"Updated status for account {account_id} to {dto.status.value}")
        
        # 保存更新
        updated_account = await self._account_repository.update(account)
        
        logger.info(f"Account updated successfully: {account_id}")
        
        return self._to_dto(updated_account)
    
    def _to_dto(self, account: Account) -> AccountDTO:
        """将实体转换为DTO"""
        return AccountDTO(
            id=account.id,
            email=account.email_str,
            client_id=account.client_id,
            tags=account.tags,
            status=account.status,
            refresh_status=account.refresh_status,
            last_refresh_time=account.last_refresh_time,
            next_refresh_time=account.next_refresh_time,
            refresh_error=account.refresh_error,
            created_at=account.created_at,
            updated_at=account.updated_at
        )

