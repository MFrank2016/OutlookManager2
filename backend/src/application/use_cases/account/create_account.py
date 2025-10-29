"""
创建账户用例

处理新账户的创建逻辑
"""

import logging
from typing import Optional

from src.application.dto import AccountDTO, CreateAccountDTO
from src.config.constants import AccountStatus, RefreshStatus
from src.domain.entities import Account
from src.domain.exceptions import (
    AccountAlreadyExistsException,
    ValidationException,
)
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.value_objects import Credentials, EmailAddress

logger = logging.getLogger(__name__)


class CreateAccountUseCase:
    """创建账户用例"""
    
    def __init__(self, account_repository: IAccountRepository):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
        """
        self._account_repository = account_repository
    
    async def execute(self, dto: CreateAccountDTO) -> AccountDTO:
        """
        执行创建账户
        
        Args:
            dto: 创建账户DTO
            
        Returns:
            AccountDTO: 创建后的账户DTO
            
        Raises:
            ValidationException: 数据验证失败
            AccountAlreadyExistsException: 账户已存在
        """
        logger.info(f"Creating account for email: {dto.email}")
        
        try:
            # 创建邮箱地址值对象（自动验证格式）
            email = EmailAddress.create(dto.email)
            
            # 检查账户是否已存在
            if await self._account_repository.exists(email):
                logger.warning(f"Account already exists: {dto.email}")
                raise AccountAlreadyExistsException(dto.email)
            
            # 创建凭证值对象（自动验证）
            credentials = Credentials.create(dto.client_id, dto.refresh_token)
            
            # 创建账户实体
            account = Account(
                email=email,
                refresh_token=credentials.refresh_token,
                client_id=credentials.client_id,
                tags=dto.tags or [],
                status=AccountStatus.ACTIVE,
                refresh_status=RefreshStatus.PENDING
            )
            
            # 保存到仓储
            created_account = await self._account_repository.create(account)
            
            logger.info(f"Account created successfully: {dto.email}")
            
            # 转换为DTO返回
            return self._to_dto(created_account)
            
        except ValidationException:
            logger.error(f"Validation failed for account: {dto.email}")
            raise
        except AccountAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"Failed to create account {dto.email}: {str(e)}")
            raise ValidationException(f"Failed to create account: {str(e)}")
    
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

