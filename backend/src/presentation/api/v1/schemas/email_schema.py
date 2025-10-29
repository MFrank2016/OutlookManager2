"""
邮件相关API Schemas

定义邮件管理的请求和响应Schema
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.config.constants import EmailFolder, EmailStatus


class EmailResponse(BaseModel):
    """邮件响应Schema"""
    
    id: UUID = Field(description="邮件ID")
    message_id: str = Field(description="邮件消息ID")
    subject: str = Field(description="主题")
    sender: str = Field(description="发件人")
    recipients: List[str] = Field(description="收件人列表")
    date: datetime = Field(description="邮件日期")
    folder: EmailFolder = Field(description="所在文件夹")
    status: EmailStatus = Field(description="邮件状态")
    preview: str = Field(description="预览文本")
    has_attachments: bool = Field(description="是否有附件")
    size: Optional[int] = Field(description="邮件大小")
    
    class Config:
        from_attributes = True


class EmailDetailResponse(BaseModel):
    """邮件详情响应Schema"""
    
    id: UUID = Field(description="邮件ID")
    message_id: str = Field(description="邮件消息ID")
    subject: str = Field(description="主题")
    sender: str = Field(description="发件人")
    recipients: List[str] = Field(description="收件人列表")
    cc: List[str] = Field(description="抄送人列表")
    bcc: List[str] = Field(description="密送人列表")
    date: datetime = Field(description="邮件日期")
    folder: EmailFolder = Field(description="所在文件夹")
    status: EmailStatus = Field(description="邮件状态")
    body_text: Optional[str] = Field(description="纯文本正文")
    body_html: Optional[str] = Field(description="HTML正文")
    has_attachments: bool = Field(description="是否有附件")
    size: Optional[int] = Field(description="邮件大小")
    flags: List[str] = Field(description="IMAP标志")
    
    class Config:
        from_attributes = True


class EmailListParams(BaseModel):
    """邮件列表查询参数Schema"""
    
    folder: EmailFolder = Field(default=EmailFolder.INBOX, description="邮件文件夹")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=100, ge=1, le=500, description="每页大小")


class EmailSearchParams(BaseModel):
    """邮件搜索参数Schema"""
    
    query: str = Field(min_length=1, description="搜索关键词")
    folder: Optional[EmailFolder] = Field(default=None, description="邮件文件夹")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=100, ge=1, le=500, description="每页大小")

