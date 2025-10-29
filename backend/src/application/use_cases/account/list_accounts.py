"""
列表查询账户用例

处理账户列表的查询逻辑
"""

import logging
from typing import Optional

from src.application.dto import AccountDTO, AccountListDTO
from src.domain.entities import Account
from src.domain.repositories.account_repository import IAccountRepository

logger = logging.getLogger(__name__)


class ListAccountsUseCase:
    """列表查询账户用例"""
    
    def __init__(self, account_repository: IAccountRepository):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
        """
        self._account_repository = account_repository
    
    async def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        email_search: Optional[str] = None,
        tag_search: Optional[str] = None
    ) -> AccountListDTO:
        """
        执行查询账户列表
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            email_search: 邮箱搜索关键词
            tag_search: 标签搜索关键词
            
        Returns:
            AccountListDTO: 账户列表DTO
        """
        logger.info(f"Listing accounts: page={page}, page_size={page_size}")
        
        # 计算跳过的记录数
        skip = (page - 1) * page_size
        
        # 从仓储获取账户列表
        accounts, total = await self._account_repository.get_all(
            skip=skip,
            limit=page_size,
            email_search=email_search,
            tag_search=tag_search
        )
        
        logger.info(f"Found {len(accounts)} accounts, total: {total}")
        
        # 转换为DTO
        account_dtos = [self._to_dto(account) for account in accounts]
        
        return AccountListDTO(
            accounts=account_dtos,
            total=total,
            page=page,
            page_size=page_size
        )
    
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

