"""
认证相关DTOs

数据传输对象，用于应用层和表现层之间的数据传递
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class LoginDTO:
    """登录请求DTO"""
    
    username: str
    password: str


@dataclass
class LoginResultDTO:
    """登录结果DTO"""
    
    success: bool
    access_token: Optional[str]
    token_type: str
    expires_in: int  # 秒数
    admin_id: UUID
    username: str
    message: str


@dataclass
class ChangePasswordDTO:
    """修改密码DTO"""
    
    old_password: str
    new_password: str


@dataclass
class ChangePasswordResultDTO:
    """修改密码结果DTO"""
    
    success: bool
    message: str


@dataclass
class TokenPayloadDTO:
    """Token载荷DTO"""
    
    sub: str  # subject (admin_id)
    username: str
    exp: datetime  # expiration time
    iat: datetime  # issued at


@dataclass
class VerifyTokenResultDTO:
    """验证Token结果DTO"""
    
    valid: bool
    admin_id: Optional[UUID]
    username: Optional[str]
    message: str

