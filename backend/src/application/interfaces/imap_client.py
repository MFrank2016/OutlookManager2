"""
IMAP客户端接口

定义IMAP操作的抽象接口
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.config.constants import EmailFolder
from src.domain.entities.email_message import EmailMessage
from src.domain.value_objects import AccessToken, EmailAddress


class IIMAPClient(ABC):
    """
    IMAP客户端接口
    
    定义与IMAP服务器交互的方法
    具体实现在基础设施层
    """
    
    @abstractmethod
    async def connect(
        self,
        email: EmailAddress,
        access_token: AccessToken
    ) -> bool:
        """
        连接到IMAP服务器
        
        Args:
            email: 邮箱地址
            access_token: 访问令牌
            
        Returns:
            bool: 是否连接成功
            
        Raises:
            IMAPConnectionException: 连接失败
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开IMAP连接"""
        pass
    
    @abstractmethod
    async def list_folders(self) -> List[str]:
        """
        获取文件夹列表
        
        Returns:
            List[str]: 文件夹名称列表
        """
        pass
    
    @abstractmethod
    async def select_folder(self, folder: EmailFolder) -> int:
        """
        选择文件夹
        
        Args:
            folder: 文件夹枚举
            
        Returns:
            int: 文件夹中的邮件数量
            
        Raises:
            FolderNotFoundException: 文件夹不存在
        """
        pass
    
    @abstractmethod
    async def fetch_emails(
        self,
        folder: EmailFolder,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        unread_only: bool = False
    ) -> List[EmailMessage]:
        """
        获取邮件列表
        
        Args:
            folder: 邮件文件夹
            limit: 最大获取数量
            start_date: 起始日期
            end_date: 结束日期
            unread_only: 仅获取未读邮件
            
        Returns:
            List[EmailMessage]: 邮件实体列表
            
        Raises:
            EmailFetchException: 获取失败
        """
        pass
    
    @abstractmethod
    async def fetch_email_by_id(self, message_id: str) -> Optional[EmailMessage]:
        """
        根据消息ID获取邮件
        
        Args:
            message_id: 消息ID
            
        Returns:
            EmailMessage | None: 邮件实体或None
            
        Raises:
            EmailFetchException: 获取失败
        """
        pass
    
    @abstractmethod
    async def search_emails(
        self,
        folder: EmailFolder,
        query: str,
        limit: int = 100
    ) -> List[EmailMessage]:
        """
        搜索邮件
        
        Args:
            folder: 邮件文件夹
            query: 搜索关键词
            limit: 最大获取数量
            
        Returns:
            List[EmailMessage]: 邮件实体列表
            
        Raises:
            EmailFetchException: 搜索失败
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """
        标记邮件为已读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否标记成功
        """
        pass
    
    @abstractmethod
    async def mark_as_unread(self, message_id: str) -> bool:
        """
        标记邮件为未读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否标记成功
        """
        pass
    
    @abstractmethod
    async def move_email(
        self,
        message_id: str,
        target_folder: EmailFolder
    ) -> bool:
        """
        移动邮件到指定文件夹
        
        Args:
            message_id: 消息ID
            target_folder: 目标文件夹
            
        Returns:
            bool: 是否移动成功
        """
        pass

