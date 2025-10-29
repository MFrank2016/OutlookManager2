"""
邮件相关DTOs

数据传输对象，用于应用层和表现层之间的数据传递
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.config.constants import EmailFolder, EmailStatus


@dataclass
class EmailDTO:
    """邮件数据传输对象"""
    
    id: UUID
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    date: datetime
    folder: EmailFolder
    status: EmailStatus
    body_text: Optional[str]
    body_html: Optional[str]
    size: Optional[int]
    has_attachments: bool
    flags: List[str]
    preview: str  # 预览文本
    created_at: datetime
    updated_at: datetime


@dataclass
class EmailListDTO:
    """邮件列表DTO"""
    
    emails: List[EmailDTO]
    total: int
    page: int
    page_size: int
    folder: EmailFolder


@dataclass
class EmailSearchDTO:
    """邮件搜索结果DTO"""
    
    emails: List[EmailDTO]
    total: int
    query: str
    page: int
    page_size: int


@dataclass
class EmailDetailDTO:
    """邮件详情DTO（包含完整正文）"""
    
    id: UUID
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    date: datetime
    folder: EmailFolder
    status: EmailStatus
    body_text: Optional[str]
    body_html: Optional[str]
    size: Optional[int]
    has_attachments: bool
    flags: List[str]
    created_at: datetime
    updated_at: datetime

