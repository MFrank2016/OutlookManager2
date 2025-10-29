"""
管理员相关API Schemas

定义管理员管理的请求和响应Schema
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminProfileResponse(BaseModel):
    """管理员个人信息响应Schema"""
    
    id: UUID = Field(description="管理员ID")
    username: str = Field(description="用户名")
    email: Optional[str] = Field(description="邮箱地址")
    is_active: bool = Field(description="是否激活")
    last_login: Optional[datetime] = Field(description="最后登录时间")
    created_at: datetime = Field(description="创建时间")
    
    class Config:
        from_attributes = True


class UpdateAdminProfileRequest(BaseModel):
    """更新管理员信息请求Schema"""
    
    email: Optional[EmailStr] = Field(default=None, description="邮箱地址")


class SystemStatsResponse(BaseModel):
    """系统统计信息响应Schema"""
    
    total_accounts: int = Field(description="总账户数")
    active_accounts: int = Field(description="激活账户数")
    total_admins: int = Field(description="总管理员数")
    system_uptime: str = Field(description="系统运行时间")
    app_version: str = Field(description="应用版本")

