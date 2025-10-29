"""
认证相关API Schemas

定义认证管理的请求和响应Schema
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求Schema"""
    
    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=8, description="密码")


class LoginResponse(BaseModel):
    """登录响应Schema"""
    
    success: bool = Field(description="是否成功")
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(description="令牌类型")
    expires_in: int = Field(description="过期秒数")
    admin_id: UUID = Field(description="管理员ID")
    username: str = Field(description="用户名")
    message: str = Field(description="消息")


class ChangePasswordRequest(BaseModel):
    """修改密码请求Schema"""
    
    old_password: str = Field(min_length=8, description="旧密码")
    new_password: str = Field(min_length=8, description="新密码")


class ChangePasswordResponse(BaseModel):
    """修改密码响应Schema"""
    
    success: bool = Field(description="是否成功")
    message: str = Field(description="消息")


class TokenResponse(BaseModel):
    """Token响应Schema"""
    
    valid: bool = Field(description="是否有效")
    admin_id: Optional[UUID] = Field(description="管理员ID")
    username: Optional[str] = Field(description="用户名")
    message: str = Field(description="消息")

