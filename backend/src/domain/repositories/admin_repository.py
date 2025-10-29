"""
Admin仓储接口

定义管理员数据访问的抽象接口
具体实现在基础设施层
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.admin import Admin


class IAdminRepository(ABC):
    """
    管理员仓储接口
    
    定义管理员实体的数据访问方法
    遵循仓储模式，隔离领域层和数据访问层
    """
    
    @abstractmethod
    async def get_by_id(self, admin_id: UUID) -> Optional[Admin]:
        """
        根据ID获取管理员
        
        Args:
            admin_id: 管理员ID
            
        Returns:
            Admin | None: 管理员实体或None
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Admin]:
        """
        根据用户名获取管理员
        
        Args:
            username: 用户名
            
        Returns:
            Admin | None: 管理员实体或None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> tuple[List[Admin], int]:
        """
        获取所有管理员（分页）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            active_only: 仅返回激活的管理员
            
        Returns:
            tuple[List[Admin], int]: (管理员列表, 总数)
        """
        pass
    
    @abstractmethod
    async def create(self, admin: Admin) -> Admin:
        """
        创建管理员
        
        Args:
            admin: 管理员实体
            
        Returns:
            Admin: 创建后的管理员实体
        """
        pass
    
    @abstractmethod
    async def update(self, admin: Admin) -> Admin:
        """
        更新管理员
        
        Args:
            admin: 管理员实体
            
        Returns:
            Admin: 更新后的管理员实体
        """
        pass
    
    @abstractmethod
    async def delete(self, admin_id: UUID) -> bool:
        """
        删除管理员
        
        Args:
            admin_id: 管理员ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, username: str) -> bool:
        """
        检查管理员是否存在
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        获取管理员总数
        
        Returns:
            int: 管理员总数
        """
        pass

