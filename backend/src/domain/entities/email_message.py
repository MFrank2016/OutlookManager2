"""
EmailMessage实体

表示邮件消息的领域实体
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from src.config.constants import EmailFolder, EmailStatus
from src.domain.exceptions import ValidationException
from src.domain.value_objects import EmailAddress


class EmailMessage:
    """
    邮件消息实体
    
    代表一封电子邮件
    包含邮件的元数据、内容和状态信息
    """
    
    def __init__(
        self,
        message_id: str,
        subject: str,
        sender: EmailAddress,
        date: datetime,
        folder: EmailFolder = EmailFolder.INBOX,
        id: Optional[UUID] = None,
        recipients: Optional[List[EmailAddress]] = None,
        cc: Optional[List[EmailAddress]] = None,
        bcc: Optional[List[EmailAddress]] = None,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        status: EmailStatus = EmailStatus.UNREAD,
        size: Optional[int] = None,
        has_attachments: bool = False,
        flags: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        初始化邮件消息实体
        
        Args:
            message_id: 邮件消息ID（来自IMAP）
            subject: 邮件主题
            sender: 发件人邮箱地址
            date: 邮件日期
            folder: 邮件所在文件夹
            id: 实体唯一标识
            recipients: 收件人列表
            cc: 抄送人列表
            bcc: 密送人列表
            body_text: 纯文本邮件正文
            body_html: HTML邮件正文
            status: 邮件状态
            size: 邮件大小（字节）
            has_attachments: 是否有附件
            flags: IMAP标志列表
            created_at: 创建时间
            updated_at: 更新时间
        """
        self._id = id or uuid4()
        self._message_id = message_id
        self._subject = subject
        self._sender = sender
        self._date = date
        self._folder = folder
        self._recipients = recipients or []
        self._cc = cc or []
        self._bcc = bcc or []
        self._body_text = body_text
        self._body_html = body_html
        self._status = status
        self._size = size
        self._has_attachments = has_attachments
        self._flags = flags or []
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
        # 验证
        self._validate()
    
    def _validate(self) -> None:
        """验证邮件数据"""
        if not self._message_id:
            raise ValidationException("Message ID cannot be empty")
        
        if not self._subject:
            raise ValidationException("Subject cannot be empty")
    
    # ========================================================================
    # 属性访问器
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        """实体ID"""
        return self._id
    
    @property
    def message_id(self) -> str:
        """邮件消息ID"""
        return self._message_id
    
    @property
    def subject(self) -> str:
        """邮件主题"""
        return self._subject
    
    @property
    def sender(self) -> EmailAddress:
        """发件人"""
        return self._sender
    
    @property
    def sender_str(self) -> str:
        """发件人字符串"""
        return str(self._sender)
    
    @property
    def date(self) -> datetime:
        """邮件日期"""
        return self._date
    
    @property
    def folder(self) -> EmailFolder:
        """邮件文件夹"""
        return self._folder
    
    @property
    def recipients(self) -> List[EmailAddress]:
        """收件人列表"""
        return self._recipients.copy()
    
    @property
    def cc(self) -> List[EmailAddress]:
        """抄送人列表"""
        return self._cc.copy()
    
    @property
    def bcc(self) -> List[EmailAddress]:
        """密送人列表"""
        return self._bcc.copy()
    
    @property
    def body_text(self) -> Optional[str]:
        """纯文本正文"""
        return self._body_text
    
    @property
    def body_html(self) -> Optional[str]:
        """HTML正文"""
        return self._body_html
    
    @property
    def status(self) -> EmailStatus:
        """邮件状态"""
        return self._status
    
    @property
    def size(self) -> Optional[int]:
        """邮件大小"""
        return self._size
    
    @property
    def has_attachments(self) -> bool:
        """是否有附件"""
        return self._has_attachments
    
    @property
    def flags(self) -> List[str]:
        """IMAP标志列表"""
        return self._flags.copy()
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at
    
    # ========================================================================
    # 业务方法
    # ========================================================================
    
    def mark_as_read(self) -> None:
        """标记为已读"""
        if self._status != EmailStatus.READ:
            self._status = EmailStatus.READ
            self._updated_at = datetime.utcnow()
    
    def mark_as_unread(self) -> None:
        """标记为未读"""
        if self._status != EmailStatus.UNREAD:
            self._status = EmailStatus.UNREAD
            self._updated_at = datetime.utcnow()
    
    def mark_as_flagged(self) -> None:
        """标记为星标/重要"""
        if self._status != EmailStatus.FLAGGED:
            self._status = EmailStatus.FLAGGED
            self._updated_at = datetime.utcnow()
    
    def mark_as_archived(self) -> None:
        """标记为已归档"""
        if self._status != EmailStatus.ARCHIVED:
            self._status = EmailStatus.ARCHIVED
            self._updated_at = datetime.utcnow()
    
    def move_to_folder(self, folder: EmailFolder) -> None:
        """
        移动到指定文件夹
        
        Args:
            folder: 目标文件夹
        """
        if self._folder != folder:
            self._folder = folder
            self._updated_at = datetime.utcnow()
    
    def add_flag(self, flag: str) -> None:
        """
        添加IMAP标志
        
        Args:
            flag: 标志名称
        """
        flag = flag.strip()
        if flag and flag not in self._flags:
            self._flags.append(flag)
            self._updated_at = datetime.utcnow()
    
    def remove_flag(self, flag: str) -> None:
        """
        移除IMAP标志
        
        Args:
            flag: 标志名称
        """
        if flag in self._flags:
            self._flags.remove(flag)
            self._updated_at = datetime.utcnow()
    
    def has_flag(self, flag: str) -> bool:
        """
        检查是否有指定标志
        
        Args:
            flag: 标志名称
            
        Returns:
            bool: 是否有该标志
        """
        return flag in self._flags
    
    def is_read(self) -> bool:
        """邮件是否已读"""
        return self._status == EmailStatus.READ
    
    def is_flagged(self) -> bool:
        """邮件是否被标记"""
        return self._status == EmailStatus.FLAGGED
    
    def is_archived(self) -> bool:
        """邮件是否已归档"""
        return self._status == EmailStatus.ARCHIVED
    
    def get_all_recipients(self) -> List[EmailAddress]:
        """
        获取所有收件人（包括to、cc、bcc）
        
        Returns:
            List[EmailAddress]: 所有收件人列表
        """
        return self._recipients + self._cc + self._bcc
    
    def get_preview_text(self, length: int = 100) -> str:
        """
        获取邮件预览文本
        
        Args:
            length: 预览长度
            
        Returns:
            str: 预览文本
        """
        text = self._body_text or self._body_html or ""
        if len(text) > length:
            return text[:length] + "..."
        return text
    
    # ========================================================================
    # 特殊方法
    # ========================================================================
    
    def __eq__(self, other) -> bool:
        """相等性比较（基于ID）"""
        if isinstance(other, EmailMessage):
            return self._id == other._id
        return False
    
    def __hash__(self) -> int:
        """哈希值（基于ID）"""
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"EmailMessage(subject='{self._subject[:30]}...', from={self.sender_str})"
    
    def __repr__(self) -> str:
        return (
            f"EmailMessage(id={self._id}, message_id='{self._message_id}', "
            f"subject='{self._subject}', folder={self._folder.value})"
        )

