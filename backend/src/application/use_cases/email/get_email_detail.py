"""
获取邮件详情用例

处理单个邮件详情查询的业务逻辑
"""

import logging

from src.application.dto import EmailDetailDTO
from src.application.interfaces import ICacheService, IIMAPClient, IOAuthClient
from src.domain.entities import Account, EmailMessage
from src.domain.exceptions import (
    AccountNotFoundException,
    EmailNotFoundException,
)
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.value_objects import Credentials, EmailAddress

logger = logging.getLogger(__name__)


class GetEmailDetailUseCase:
    """获取邮件详情用例"""
    
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
        message_id: str
    ) -> EmailDetailDTO:
        """
        执行获取邮件详情
        
        Args:
            email: 账户邮箱地址
            message_id: 邮件消息ID
            
        Returns:
            EmailDetailDTO: 邮件详情DTO
            
        Raises:
            AccountNotFoundException: 账户不存在
            EmailNotFoundException: 邮件不存在
        """
        logger.info(f"Getting email detail for {email}, message_id={message_id}")
        
        # 获取账户
        email_vo = EmailAddress.create(email)
        account = await self._account_repository.get_by_email(email_vo)
        
        if not account:
            logger.warning(f"Account not found: {email}")
            raise AccountNotFoundException(email)
        
        # 尝试从缓存获取
        cache_key = f"email:detail:{message_id}"
        cached_data = await self._cache_service.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached email detail: {message_id}")
            return cached_data
        
        # 获取访问令牌
        access_token = await self._get_access_token(account)
        
        # 连接IMAP
        await self._imap_client.connect(email_vo, access_token)
        
        try:
            # 获取邮件
            email_msg = await self._imap_client.fetch_email_by_id(message_id)
            
            if not email_msg:
                logger.warning(f"Email not found: {message_id}")
                raise EmailNotFoundException(message_id)
            
            # 转换为DTO
            result = self._to_dto(email_msg)
            
            # 缓存结果
            await self._cache_service.set(cache_key, result, ttl=600)  # 10分钟缓存
            
            logger.info(f"Email detail retrieved: {message_id}")
            
            return result
            
        finally:
            await self._imap_client.disconnect()
    
    async def _get_access_token(self, account: Account):
        """获取访问令牌"""
        credentials = Credentials.create(account.client_id, account.refresh_token)
        access_token, _ = await self._oauth_client.refresh_token(credentials)
        return access_token
    
    def _to_dto(self, email: EmailMessage) -> EmailDetailDTO:
        """将实体转换为DTO"""
        return EmailDetailDTO(
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
            created_at=email.created_at,
            updated_at=email.updated_at
        )

