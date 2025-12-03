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
    tags: Optional[List[str]] = Field(default_factory=list)
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"
    refresh_error: Optional[str] = None
    api_method: str = "imap"  # 'graph_api' or 'imap'

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
    body_preview: Optional[str] = None  # 邮件内容预览

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
    total_pages: int
    total_emails: int
    emails: List[EmailItem]
    from_cache: bool = False  # 是否来自缓存
    fetch_time_ms: Optional[int] = None  # 获取耗时（毫秒）


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
    tags: List[str] = Field(default_factory=list)
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"
    api_method: str = "imap"  # 'graph_api' or 'imap'


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


class BatchRefreshRequest(BaseModel):
    """批量刷新Token请求模型"""
    
    email_ids: Optional[List[str]] = Field(None, description="要刷新的邮箱账户列表，如果为空则使用筛选条件")


class BatchRefreshResult(BaseModel):
    """批量刷新结果模型"""
    
    total_processed: int
    success_count: int
    failed_count: int
    details: List[dict]


class BatchDeleteRequest(BaseModel):
    """批量删除账户请求模型"""
    
    email_ids: List[str] = Field(..., description="要删除的邮箱账户列表")


class BatchDeleteResult(BaseModel):
    """批量删除结果模型"""
    
    total_processed: int
    success_count: int
    failed_count: int
    details: List[dict]


class BatchImportItem(BaseModel):
    """批量导入项模型"""
    
    email: str
    refresh_token: str
    client_id: str


class BatchImportRequest(BaseModel):
    """批量导入请求模型"""
    
    items: List[BatchImportItem]
    api_method: str = "imap"
    tags: List[str] = Field(default_factory=list)


class BatchImportTaskResponse(BaseModel):
    """批量导入任务响应模型"""
    
    task_id: str
    total_count: int
    status: str
    message: str


class BatchImportTaskProgress(BaseModel):
    """批量导入任务进度模型"""
    
    task_id: str
    total_count: int
    success_count: int
    failed_count: int
    processed_count: int
    status: str
    progress_percent: float


class SendEmailRequest(BaseModel):
    """发送邮件请求模型"""
    
    to: str = Field(..., description="收件人邮箱地址")
    subject: str = Field(..., description="邮件主题")
    body_text: Optional[str] = Field(None, description="纯文本正文")
    body_html: Optional[str] = Field(None, description="HTML正文")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "recipient@example.com",
                "subject": "Test Email",
                "body_text": "This is a test email",
                "body_html": "<p>This is a test email</p>"
            }
        }


class SendEmailResponse(BaseModel):
    """发送邮件响应模型"""
    
    success: bool
    message: str
    message_id: Optional[str] = None


class DeleteEmailResponse(BaseModel):
    """删除邮件响应模型"""
    
    success: bool
    message: str
    message_id: str


# ============================================================================
# 用户管理模型
# ============================================================================

class UserCreateRequest(BaseModel):
    """创建用户请求模型"""
    
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field("user", description="角色 (admin/user)")
    bound_accounts: Optional[List[str]] = Field(default_factory=list, description="绑定的邮箱账户列表")
    permissions: Optional[List[str]] = Field(default_factory=list, description="权限列表")
    is_active: bool = Field(True, description="账户是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123",
                "email": "test@example.com",
                "role": "user",
                "bound_accounts": ["user1@outlook.com", "user2@outlook.com"],
                "permissions": ["view_emails", "send_emails"],
                "is_active": True
            }
        }


class UserUpdateRequest(BaseModel):
    """更新用户请求模型"""
    
    email: Optional[str] = Field(None, description="邮箱")
    role: Optional[str] = Field(None, description="角色 (admin/user)")
    bound_accounts: Optional[List[str]] = Field(None, description="绑定的邮箱账户列表")
    permissions: Optional[List[str]] = Field(None, description="权限列表")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "role": "user",
                "bound_accounts": ["user1@outlook.com"],
                "permissions": ["view_emails", "send_emails", "delete_emails"],
                "is_active": True
            }
        }


class UserInfo(BaseModel):
    """用户信息模型"""
    
    id: int
    username: str
    email: Optional[str] = None
    role: str
    bound_accounts: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: str
    last_login: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "role": "user",
                "bound_accounts": ["user1@outlook.com"],
                "permissions": ["view_emails", "send_emails"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-02T10:30:00"
            }
        }


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    
    total_users: int
    page: int
    page_size: int
    total_pages: int
    users: List[UserInfo]


class PermissionsUpdateRequest(BaseModel):
    """权限更新请求模型"""
    
    permissions: List[str] = Field(..., description="权限列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "permissions": ["view_emails", "send_emails", "delete_emails"]
            }
        }


class BindAccountsRequest(BaseModel):
    """绑定账户请求模型"""
    
    account_emails: List[str] = Field(..., description="邮箱账户列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_emails": ["user1@outlook.com", "user2@outlook.com"]
            }
        }


class RoleUpdateRequest(BaseModel):
    """角色更新请求模型"""
    
    role: str = Field(..., description="角色 (admin/user)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin"
            }
        }


class UserResponse(BaseModel):
    """用户操作响应模型"""
    
    message: str
    user: Optional[UserInfo] = None


class PasswordUpdateRequest(BaseModel):
    """修改密码请求模型"""
    
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_password": "newpassword123"
            }
        }


# ============================================================================
# 分享码管理模型
# ============================================================================

class ShareTokenCreate(BaseModel):
    """创建分享码请求模型"""
    email_account_id: str = Field(..., description="邮箱账户ID")
    valid_hours: Optional[int] = Field(None, description="有效期（小时）")
    valid_days: Optional[int] = Field(None, description="有效期（天）")
    filter_start_time: str = Field(..., description="邮件开始时间筛选 (ISO8601)")
    filter_end_time: Optional[str] = Field(None, description="邮件结束时间筛选 (ISO8601)")
    subject_keyword: Optional[str] = Field(None, description="主题关键词")
    sender_keyword: Optional[str] = Field(None, description="发件人关键词")
    max_emails: Optional[int] = Field(10, description="最多返回邮件数量（默认10）")

class ShareTokenUpdate(BaseModel):
    """更新分享码请求模型"""
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    subject_keyword: Optional[str] = Field(None, description="主题关键词")
    sender_keyword: Optional[str] = Field(None, description="发件人关键词")
    expiry_time: Optional[str] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")
    max_emails: Optional[int] = Field(None, description="最多返回邮件数量")

class ShareTokenResponse(BaseModel):
    """分享码响应模型"""
    id: int
    token: str
    email_account_id: str
    start_time: str
    end_time: Optional[str] = None
    subject_keyword: Optional[str] = None
    sender_keyword: Optional[str] = None
    expiry_time: Optional[str] = None
    created_at: str
    is_active: bool
    max_emails: int = 10
    share_link: Optional[str] = None

class BatchShareTokenCreate(BaseModel):
    """批量创建分享码请求模型"""
    email_accounts: List[str] = Field(..., description="邮箱账户ID列表")
    valid_hours: Optional[int] = Field(None, description="有效期（小时）")
    valid_days: Optional[int] = Field(None, description="有效期（天）")
    filter_start_time: str = Field(..., description="邮件开始时间筛选 (ISO8601)")
    filter_end_time: Optional[str] = Field(None, description="邮件结束时间筛选 (ISO8601)")
    subject_keyword: Optional[str] = Field(None, description="主题关键词")
    sender_keyword: Optional[str] = Field(None, description="发件人关键词")
    max_emails: Optional[int] = Field(10, description="最多返回邮件数量（默认10）")

class BatchShareResultItem(BaseModel):
    """批量分享单个账号的处理结果"""
    email_account_id: str
    status: str = Field(..., description="处理状态: success, failed, ignored")
    token: Optional[str] = Field(None, description="分享码（成功时返回）")
    error_message: Optional[str] = Field(None, description="错误信息（失败时返回）")

class BatchShareTokenResponse(BaseModel):
    """批量创建分享码响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    ignored_count: int = Field(..., description="忽略数量（账号不存在）")
    results: List[BatchShareResultItem] = Field(..., description="详细结果列表")

class BatchDeactivateRequest(BaseModel):
    """批量失效请求模型"""
    token_ids: List[int] = Field(..., description="分享码ID列表")

class BatchDeactivateResponse(BaseModel):
    """批量失效响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    total_count: int = Field(..., description="总数")

class ExtendShareTokenRequest(BaseModel):
    """延期分享码请求模型"""
    extend_hours: Optional[int] = Field(None, description="延长小时数")
    extend_days: Optional[int] = Field(None, description="延长天数")
    extend_to_time: Optional[str] = Field(None, description="延长至指定时间 (ISO8601)")

