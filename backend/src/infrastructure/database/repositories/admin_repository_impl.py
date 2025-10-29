"""
Admin仓储实现

基于SQLAlchemy的管理员仓储具体实现
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Admin
from src.domain.repositories.admin_repository import IAdminRepository
from src.domain.value_objects import EmailAddress
from src.infrastructure.database.models import AdminModel

logger = logging.getLogger(__name__)


class AdminRepositoryImpl(IAdminRepository):
    """管理员仓储实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self._session = session
    
    async def get_by_id(self, admin_id: UUID) -> Optional[Admin]:
        """根据ID获取管理员"""
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == admin_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_by_username(self, username: str) -> Optional[Admin]:
        """根据用户名获取管理员"""
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.username == username)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> tuple[List[Admin], int]:
        """获取所有管理员（分页）"""
        # 构建查询
        query = select(AdminModel)
        
        if active_only:
            query = query.where(AdminModel.is_active == True)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        admins = [self._to_entity(model) for model in models]
        
        return admins, total
    
    async def create(self, admin: Admin) -> Admin:
        """创建管理员"""
        model = self._to_model(admin)
        
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        
        logger.info(f"Admin created: {admin.username}")
        
        return self._to_entity(model)
    
    async def update(self, admin: Admin) -> Admin:
        """更新管理员"""
        # 获取现有模型
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == admin.id)
        )
        model = result.scalar_one()
        
        # 更新字段
        model.username = admin.username
        model.password_hash = admin.password_hash
        model.email = admin.email_str
        model.is_active = admin.is_active
        model.last_login = admin.last_login
        model.updated_at = admin.updated_at
        
        await self._session.flush()
        await self._session.refresh(model)
        
        logger.info(f"Admin updated: {admin.username}")
        
        return self._to_entity(model)
    
    async def delete(self, admin_id: UUID) -> bool:
        """删除管理员"""
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == admin_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self._session.delete(model)
        await self._session.flush()
        
        logger.info(f"Admin deleted: {admin_id}")
        
        return True
    
    async def exists(self, username: str) -> bool:
        """检查管理员是否存在"""
        result = await self._session.execute(
            select(func.count()).select_from(AdminModel).where(
                AdminModel.username == username
            )
        )
        count = result.scalar_one()
        
        return count > 0
    
    async def count(self) -> int:
        """获取管理员总数"""
        result = await self._session.execute(
            select(func.count()).select_from(AdminModel)
        )
        return result.scalar_one()
    
    def _to_entity(self, model: AdminModel) -> Admin:
        """将数据库模型转换为领域实体"""
        email = EmailAddress.create(model.email) if model.email else None
        
        return Admin(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            email=email,
            is_active=model.is_active,
            last_login=model.last_login,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, admin: Admin) -> AdminModel:
        """将领域实体转换为数据库模型"""
        return AdminModel(
            id=admin.id,
            username=admin.username,
            password_hash=admin.password_hash,
            email=admin.email_str,
            is_active=admin.is_active,
            last_login=admin.last_login,
            created_at=admin.created_at,
            updated_at=admin.updated_at
        )

