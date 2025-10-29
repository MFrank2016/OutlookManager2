"""
Account仓储实现

基于SQLAlchemy的账户仓储具体实现
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constants import AccountStatus, RefreshStatus
from src.domain.entities import Account
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.value_objects import EmailAddress
from src.infrastructure.database.models import AccountModel

logger = logging.getLogger(__name__)


class AccountRepositoryImpl(IAccountRepository):
    """账户仓储实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self._session = session
    
    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """根据ID获取账户"""
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id == account_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_by_email(self, email: EmailAddress) -> Optional[Account]:
        """根据邮箱地址获取账户"""
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.email == str(email))
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        email_search: Optional[str] = None,
        tag_search: Optional[str] = None
    ) -> tuple[List[Account], int]:
        """获取所有账户（分页）"""
        # 构建查询
        query = select(AccountModel)
        
        # 邮箱搜索
        if email_search:
            query = query.where(AccountModel.email.contains(email_search))
        
        # 标签搜索（JSON数组搜索）
        if tag_search:
            # 注意：这里的实现取决于具体数据库
            # PostgreSQL可以使用JSON操作符，SQLite需要不同的方法
            pass  # 简化实现，实际需要根据数据库类型处理
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        accounts = [self._to_entity(model) for model in models]
        
        return accounts, total
    
    async def create(self, account: Account) -> Account:
        """创建账户"""
        model = self._to_model(account)
        
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        
        logger.info(f"Account created: {account.email_str}")
        
        return self._to_entity(model)
    
    async def update(self, account: Account) -> Account:
        """更新账户"""
        # 获取现有模型
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id == account.id)
        )
        model = result.scalar_one()
        
        # 更新字段
        model.email = account.email_str
        model.refresh_token = account.refresh_token
        model.client_id = account.client_id
        model.tags = account.tags
        model.status = account.status.value
        model.refresh_status = account.refresh_status.value
        model.last_refresh_time = account.last_refresh_time
        model.next_refresh_time = account.next_refresh_time
        model.refresh_error = account.refresh_error
        model.updated_at = account.updated_at
        
        await self._session.flush()
        await self._session.refresh(model)
        
        logger.info(f"Account updated: {account.email_str}")
        
        return self._to_entity(model)
    
    async def delete(self, account_id: UUID) -> bool:
        """删除账户"""
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id == account_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self._session.delete(model)
        await self._session.flush()
        
        logger.info(f"Account deleted: {account_id}")
        
        return True
    
    async def exists(self, email: EmailAddress) -> bool:
        """检查账户是否存在"""
        result = await self._session.execute(
            select(func.count()).select_from(AccountModel).where(
                AccountModel.email == str(email)
            )
        )
        count = result.scalar_one()
        
        return count > 0
    
    async def count(self) -> int:
        """获取账户总数"""
        result = await self._session.execute(
            select(func.count()).select_from(AccountModel)
        )
        return result.scalar_one()
    
    async def get_accounts_need_refresh(self) -> List[Account]:
        """获取需要刷新Token的账户列表"""
        from datetime import datetime
        
        now = datetime.utcnow()
        
        result = await self._session.execute(
            select(AccountModel).where(
                AccountModel.status == AccountStatus.ACTIVE.value,
                AccountModel.refresh_status != RefreshStatus.IN_PROGRESS.value,
                AccountModel.next_refresh_time <= now
            )
        )
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: AccountModel) -> Account:
        """将数据库模型转换为领域实体"""
        return Account(
            id=model.id,
            email=EmailAddress.create(model.email),
            refresh_token=model.refresh_token,
            client_id=model.client_id,
            tags=model.tags or [],
            status=AccountStatus(model.status),
            refresh_status=RefreshStatus(model.refresh_status),
            last_refresh_time=model.last_refresh_time,
            next_refresh_time=model.next_refresh_time,
            refresh_error=model.refresh_error,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, account: Account) -> AccountModel:
        """将领域实体转换为数据库模型"""
        return AccountModel(
            id=account.id,
            email=account.email_str,
            refresh_token=account.refresh_token,
            client_id=account.client_id,
            tags=account.tags,
            status=account.status.value,
            refresh_status=account.refresh_status.value,
            last_refresh_time=account.last_refresh_time,
            next_refresh_time=account.next_refresh_time,
            refresh_error=account.refresh_error,
            created_at=account.created_at,
            updated_at=account.updated_at
        )

