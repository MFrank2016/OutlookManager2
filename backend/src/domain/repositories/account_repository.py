"""
Account仓储接口

定义账户数据访问的抽象接口
具体实现在基础设施层
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.account import Account
from src.domain.value_objects import EmailAddress


class IAccountRepository(ABC):
    """
    账户仓储接口
    
    定义账户实体的数据访问方法
    遵循仓储模式，隔离领域层和数据访问层
    """
    
    @abstractmethod
    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """
        根据ID获取账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            Account | None: 账户实体或None
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: EmailAddress) -> Optional[Account]:
        """
        根据邮箱地址获取账户
        
        Args:
            email: 邮箱地址值对象
            
        Returns:
            Account | None: 账户实体或None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        email_search: Optional[str] = None,
        tag_search: Optional[str] = None
    ) -> tuple[List[Account], int]:
        """
        获取所有账户（分页）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            email_search: 邮箱搜索关键词
            tag_search: 标签搜索关键词
            
        Returns:
            tuple[List[Account], int]: (账户列表, 总数)
        """
        pass
    
    @abstractmethod
    async def create(self, account: Account) -> Account:
        """
        创建账户
        
        Args:
            account: 账户实体
            
        Returns:
            Account: 创建后的账户实体
        """
        pass
    
    @abstractmethod
    async def update(self, account: Account) -> Account:
        """
        更新账户
        
        Args:
            account: 账户实体
            
        Returns:
            Account: 更新后的账户实体
        """
        pass
    
    @abstractmethod
    async def delete(self, account_id: UUID) -> bool:
        """
        删除账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, email: EmailAddress) -> bool:
        """
        检查账户是否存在
        
        Args:
            email: 邮箱地址值对象
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        获取账户总数
        
        Returns:
            int: 账户总数
        """
        pass
    
    @abstractmethod
    async def get_accounts_need_refresh(self) -> List[Account]:
        """
        获取需要刷新Token的账户列表
        
        Returns:
            List[Account]: 需要刷新的账户列表
        """
        pass

