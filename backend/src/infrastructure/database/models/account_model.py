"""
Account数据库模型

SQLAlchemy ORM模型定义
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.config.constants import AccountStatus, RefreshStatus
from src.infrastructure.database.models.base import Base, TimestampMixin


class AccountModel(Base, TimestampMixin):
    """账户数据库模型"""
    
    __tablename__ = "accounts"
    
    # 主键
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # 基本信息
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 标签（JSON数组）
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        default=AccountStatus.ACTIVE.value,
        nullable=False
    )
    refresh_status: Mapped[str] = mapped_column(
        String(20),
        default=RefreshStatus.PENDING.value,
        nullable=False
    )
    
    # Token刷新相关
    last_refresh_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_refresh_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refresh_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AccountModel(id={self.id}, email={self.email}, status={self.status})>"

