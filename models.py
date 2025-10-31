"""
数据模型模块

定义系统中使用的所有Pydantic数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class AccountCredentials(BaseModel):
    """账户凭证模型"""

    email: EmailStr
    refresh_token: str
    client_id: str
    tags: Optional[List[str]] = Field(default=[])
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"
    refresh_error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@outlook.com",
                "refresh_token": "0.AXoA...",
                "client_id": "your-client-id",
                "tags": ["工作", "个人"],
                "last_refresh_time": "2024-01-01T12:00:00",
                "refresh_status": "success",
            }
        }


class EmailItem(BaseModel):
    """邮件项目模型"""

    message_id: str
    folder: str
    subject: str
    from_email: str
    date: str
    is_read: bool = False
    has_attachments: bool = False
    sender_initial: str = "?"
    verification_code: Optional[str] = None  # 验证码（如果检测到）

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "INBOX-123",
                "folder": "INBOX",
                "subject": "Welcome to Augment Code",
                "from_email": "noreply@augmentcode.com",
                "date": "2024-01-01T12:00:00",
                "is_read": False,
                "has_attachments": False,
                "sender_initial": "A",
                "verification_code": None,
            }
        }


class EmailListResponse(BaseModel):
    """邮件列表响应模型"""

    email_id: str
    folder_view: str
    page: int
    page_size: int
    total_emails: int
    emails: List[EmailItem]


class DualViewEmailResponse(BaseModel):
    """双栏视图邮件响应模型"""

    email_id: str
    inbox_emails: List[EmailItem]
    junk_emails: List[EmailItem]
    inbox_total: int
    junk_total: int


class EmailDetailsResponse(BaseModel):
    """邮件详情响应模型"""

    message_id: str
    subject: str
    from_email: str
    to_email: str
    date: str
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    verification_code: Optional[str] = None  # 验证码（如果检测到）


class AccountResponse(BaseModel):
    """账户操作响应模型"""

    email_id: str
    message: str


class AccountInfo(BaseModel):
    """账户信息模型"""

    email_id: str
    client_id: str
    status: str = "active"
    tags: List[str] = []
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"


class AccountListResponse(BaseModel):
    """账户列表响应模型"""

    total_accounts: int
    page: int
    page_size: int
    total_pages: int
    accounts: List[AccountInfo]


class UpdateTagsRequest(BaseModel):
    """更新标签请求模型"""

    tags: List[str]


class AddTagRequest(BaseModel):
    """添加标签请求模型"""

    tag: str


class BatchRefreshResult(BaseModel):
    """批量刷新结果模型"""
    
    total_processed: int
    success_count: int
    failed_count: int
    details: List[dict]

