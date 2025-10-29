"""
账户相关DTOs

数据传输对象，用于应用层和表现层之间的数据传递
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.config.constants import AccountStatus, RefreshStatus


@dataclass
class AccountDTO:
    """账户数据传输对象"""
    
    id: UUID
    email: str
    client_id: str
    tags: List[str]
    status: AccountStatus
    refresh_status: RefreshStatus
    last_refresh_time: Optional[datetime]
    next_refresh_time: Optional[datetime]
    refresh_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateAccountDTO:
    """创建账户DTO"""
    
    email: str
    refresh_token: str
    client_id: str
    tags: Optional[List[str]] = None


@dataclass
class UpdateAccountDTO:
    """更新账户DTO"""
    
    tags: Optional[List[str]] = None
    status: Optional[AccountStatus] = None


@dataclass
class AccountListDTO:
    """账户列表DTO"""
    
    accounts: List[AccountDTO]
    total: int
    page: int
    page_size: int


@dataclass
class RefreshTokenDTO:
    """刷新Token结果DTO"""
    
    success: bool
    message: str
    refresh_time: datetime
    next_refresh_time: Optional[datetime] = None

