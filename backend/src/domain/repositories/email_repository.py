"""
Email仓储接口

定义邮件数据访问的抽象接口
具体实现在基础设施层
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.config.constants import EmailFolder
from src.domain.entities.email_message import EmailMessage
from src.domain.value_objects import EmailAddress


class IEmailRepository(ABC):
    """
    邮件仓储接口
    
    定义邮件实体的数据访问方法
    注意：邮件数据主要从IMAP服务器获取，不持久化到本地数据库
    此接口主要用于缓存和临时存储
    """
    
    @abstractmethod
    async def get_by_id(self, email_id: UUID) -> Optional[EmailMessage]:
        """
        根据ID获取邮件
        
        Args:
            email_id: 邮件实体ID
            
        Returns:
            EmailMessage | None: 邮件实体或None
        """
        pass
    
    @abstractmethod
    async def get_by_message_id(self, message_id: str) -> Optional[EmailMessage]:
        """
        根据消息ID获取邮件
        
        Args:
            message_id: IMAP消息ID
            
        Returns:
            EmailMessage | None: 邮件实体或None
        """
        pass
    
    @abstractmethod
    async def get_emails_by_folder(
        self,
        account_email: EmailAddress,
        folder: EmailFolder,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[EmailMessage], int]:
        """
        获取指定文件夹的邮件列表
        
        Args:
            account_email: 账户邮箱地址
            folder: 邮件文件夹
            skip: 跳过记录数
            limit: 返回记录数
            start_date: 起始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            tuple[List[EmailMessage], int]: (邮件列表, 总数)
        """
        pass
    
    @abstractmethod
    async def search_emails(
        self,
        account_email: EmailAddress,
        query: str,
        folder: Optional[EmailFolder] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[EmailMessage], int]:
        """
        搜索邮件
        
        Args:
            account_email: 账户邮箱地址
            query: 搜索关键词
            folder: 邮件文件夹（可选）
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            tuple[List[EmailMessage], int]: (邮件列表, 总数)
        """
        pass
    
    @abstractmethod
    async def cache_email(self, email: EmailMessage, ttl: int = 3600) -> bool:
        """
        缓存邮件到临时存储
        
        Args:
            email: 邮件实体
            ttl: 缓存有效期（秒）
            
        Returns:
            bool: 是否缓存成功
        """
        pass
    
    @abstractmethod
    async def cache_emails(
        self,
        emails: List[EmailMessage],
        ttl: int = 3600
    ) -> int:
        """
        批量缓存邮件
        
        Args:
            emails: 邮件实体列表
            ttl: 缓存有效期（秒）
            
        Returns:
            int: 成功缓存的数量
        """
        pass
    
    @abstractmethod
    async def invalidate_cache(self, account_email: EmailAddress) -> bool:
        """
        清除指定账户的邮件缓存
        
        Args:
            account_email: 账户邮箱地址
            
        Returns:
            bool: 是否清除成功
        """
        pass

