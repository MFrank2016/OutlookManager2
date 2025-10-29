"""
获取账户详情用例

处理单个账户的查询逻辑
"""

import logging
from uuid import UUID

from src.application.dto import AccountDTO
from src.domain.entities import Account
from src.domain.exceptions import AccountNotFoundException
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.value_objects import EmailAddress

logger = logging.getLogger(__name__)


class GetAccountUseCase:
    """获取账户详情用例"""
    
    def __init__(self, account_repository: IAccountRepository):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
        """
        self._account_repository = account_repository
    
    async def execute_by_id(self, account_id: UUID) -> AccountDTO:
        """
        根据ID获取账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            AccountDTO: 账户DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
        """
        logger.info(f"Getting account by ID: {account_id}")
        
        account = await self._account_repository.get_by_id(account_id)
        
        if not account:
            logger.warning(f"Account not found: {account_id}")
            raise AccountNotFoundException(str(account_id))
        
        return self._to_dto(account)
    
    async def execute_by_email(self, email: str) -> AccountDTO:
        """
        根据邮箱地址获取账户
        
        Args:
            email: 邮箱地址
            
        Returns:
            AccountDTO: 账户DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
        """
        logger.info(f"Getting account by email: {email}")
        
        email_vo = EmailAddress.create(email)
        account = await self._account_repository.get_by_email(email_vo)
        
        if not account:
            logger.warning(f"Account not found: {email}")
            raise AccountNotFoundException(email)
        
        return self._to_dto(account)
    
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

