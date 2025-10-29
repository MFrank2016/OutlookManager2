"""
账户相关API Schemas

定义账户管理的请求和响应Schema
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.config.constants import AccountStatus, RefreshStatus


class AccountCreateRequest(BaseModel):
    """创建账户请求Schema"""
    
    email: EmailStr = Field(description="邮箱地址")
    refresh_token: str = Field(min_length=10, description="OAuth刷新令牌")
    client_id: str = Field(min_length=10, description="Azure客户端ID")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class AccountUpdateRequest(BaseModel):
    """更新账户请求Schema"""
    
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    status: Optional[AccountStatus] = Field(default=None, description="账户状态")


class AccountResponse(BaseModel):
    """账户响应Schema"""
    
    id: UUID = Field(description="账户ID")
    email: str = Field(description="邮箱地址")
    client_id: str = Field(description="客户端ID")
    tags: List[str] = Field(description="标签列表")
    status: AccountStatus = Field(description="账户状态")
    refresh_status: RefreshStatus = Field(description="刷新状态")
    last_refresh_time: Optional[datetime] = Field(description="最后刷新时间")
    next_refresh_time: Optional[datetime] = Field(description="下次刷新时间")
    refresh_error: Optional[str] = Field(description="刷新错误信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    class Config:
        from_attributes = True


class RefreshTokenResponse(BaseModel):
    """刷新Token响应Schema"""
    
    success: bool = Field(description="是否成功")
    message: str = Field(description="消息")
    refresh_time: datetime = Field(description="刷新时间")
    next_refresh_time: Optional[datetime] = Field(description="下次刷新时间")

