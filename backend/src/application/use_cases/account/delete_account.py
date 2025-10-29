"""
删除账户用例

处理账户删除的业务逻辑
"""

import logging
from uuid import UUID

from src.domain.exceptions import AccountNotFoundException, OperationFailedException
from src.domain.repositories.account_repository import IAccountRepository

logger = logging.getLogger(__name__)


class DeleteAccountUseCase:
    """删除账户用例"""
    
    def __init__(self, account_repository: IAccountRepository):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
        """
        self._account_repository = account_repository
    
    async def execute(self, account_id: UUID) -> bool:
        """
        执行删除账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            AccountNotFoundException: 账户不存在
            OperationFailedException: 删除操作失败
        """
        logger.info(f"Deleting account: {account_id}")
        
        # 检查账户是否存在
        account = await self._account_repository.get_by_id(account_id)
        
        if not account:
            logger.warning(f"Account not found: {account_id}")
            raise AccountNotFoundException(str(account_id))
        
        # 执行删除
        success = await self._account_repository.delete(account_id)
        
        if not success:
            logger.error(f"Failed to delete account: {account_id}")
            raise OperationFailedException(
                "delete_account",
                "Database operation failed"
            )
        
        logger.info(f"Account deleted successfully: {account_id}")
        
        return True

