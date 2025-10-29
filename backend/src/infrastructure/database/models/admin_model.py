"""
Admin数据库模型

SQLAlchemy ORM模型定义
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base, TimestampMixin


class AdminModel(Base, TimestampMixin):
    """管理员数据库模型"""
    
    __tablename__ = "admins"
    
    # 主键
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 登录记录
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AdminModel(id={self.id}, username={self.username}, is_active={self.is_active})>"

