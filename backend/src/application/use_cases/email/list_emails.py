"""
邮件列表用例

处理邮件列表查询的业务逻辑
"""

import logging
from datetime import datetime
from typing import Optional

from src.application.dto import EmailDTO, EmailListDTO
from src.application.interfaces import ICacheService, IIMAPClient, IOAuthClient
from src.config.constants import EmailFolder
from src.domain.entities import Account, EmailMessage
from src.domain.exceptions import AccountNotFoundException
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.value_objects import Credentials, EmailAddress

logger = logging.getLogger(__name__)


class ListEmailsUseCase:
    """邮件列表用例"""
    
    def __init__(
        self,
        account_repository: IAccountRepository,
        imap_client: IIMAPClient,
        oauth_client: IOAuthClient,
        cache_service: ICacheService
    ):
        """
        初始化用例
        
        Args:
            account_repository: 账户仓储
            imap_client: IMAP客户端
            oauth_client: OAuth客户端
            cache_service: 缓存服务
        """
        self._account_repository = account_repository
        self._imap_client = imap_client
        self._oauth_client = oauth_client
        self._cache_service = cache_service
    
    async def execute(
        self,
        email: str,
        folder: EmailFolder = EmailFolder.INBOX,
        page: int = 1,
        page_size: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EmailListDTO:
        """
        执行查询邮件列表
        
        Args:
            email: 账户邮箱地址
            folder: 邮件文件夹
            page: 页码（从1开始）
            page_size: 每页大小
            start_date: 起始日期
            end_date: 结束日期
            
        Returns:
            EmailListDTO: 邮件列表DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
            EmailFetchException: 获取邮件失败
        """
        logger.info(f"Listing emails for {email}, folder={folder.value}, page={page}")
        
        # 获取账户
        email_vo = EmailAddress.create(email)
        account = await self._account_repository.get_by_email(email_vo)
        
        if not account:
            logger.warning(f"Account not found: {email}")
            raise AccountNotFoundException(email)
        
        # 尝试从缓存获取
        cache_key = f"email:list:{email}:{folder.value}:{page}:{page_size}"
        cached_data = await self._cache_service.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached email list for {email}")
            return cached_data
        
        # 获取访问令牌
        access_token = await self._get_access_token(account)
        
        # 连接IMAP
        await self._imap_client.connect(email_vo, access_token)
        
        try:
            # 获取邮件列表
            emails = await self._imap_client.fetch_emails(
                folder=folder,
                limit=page_size,
                start_date=start_date,
                end_date=end_date
            )
            
            # 转换为DTO
            email_dtos = [self._to_dto(email_msg) for email_msg in emails]
            
            # 构建结果
            result = EmailListDTO(
                emails=email_dtos,
                total=len(email_dtos),  # 注意：IMAP不提供总数，这里简化处理
                page=page,
                page_size=page_size,
                folder=folder
            )
            
            # 缓存结果
            await self._cache_service.set(cache_key, result, ttl=300)  # 5分钟缓存
            
            logger.info(f"Found {len(email_dtos)} emails for {email}")
            
            return result
            
        finally:
            await self._imap_client.disconnect()
    
    async def _get_access_token(self, account: Account):
        """获取访问令牌"""
        credentials = Credentials.create(account.client_id, account.refresh_token)
        access_token, _ = await self._oauth_client.refresh_token(credentials)
        return access_token
    
    def _to_dto(self, email: EmailMessage) -> EmailDTO:
        """将实体转换为DTO"""
        return EmailDTO(
            id=email.id,
            message_id=email.message_id,
            subject=email.subject,
            sender=email.sender_str,
            recipients=[str(r) for r in email.recipients],
            cc=[str(c) for c in email.cc],
            bcc=[str(b) for b in email.bcc],
            date=email.date,
            folder=email.folder,
            status=email.status,
            body_text=email.body_text,
            body_html=email.body_html,
            size=email.size,
            has_attachments=email.has_attachments,
            flags=email.flags,
            preview=email.get_preview_text(),
            created_at=email.created_at,
            updated_at=email.updated_at
        )

