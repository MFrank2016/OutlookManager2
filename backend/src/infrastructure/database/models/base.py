"""
SQLAlchemy基类

定义所有数据库模型的基类
"""

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """SQLAlchemy声明式基类"""
    
    pass


class TimestampMixin:
    """时间戳混入类"""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名（类名转小写复数）"""
        return cls.__name__.lower() + "s"

