"""
数据库会话管理

提供异步数据库连接和会话管理
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import settings
from src.infrastructure.database.models import Base

logger = logging.getLogger(__name__)

# 全局引擎和会话工厂
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    获取数据库引擎（单例）
    
    Returns:
        AsyncEngine: SQLAlchemy异步引擎
    """
    global _engine
    
    if _engine is None:
        # SQLite 不支持连接池参数
        if settings.DATABASE_URL.startswith("sqlite"):
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
            )
        else:
            # PostgreSQL 和其他数据库支持连接池
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True,  # 连接前检查
            )
        logger.info(f"Database engine created: {settings.DATABASE_URL}")
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    获取会话工厂（单例）
    
    Returns:
        async_sessionmaker: 异步会话工厂
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        logger.info("Session factory created")
    
    return _session_factory


async def init_database() -> None:
    """
    初始化数据库
    
    创建所有表（开发环境使用，生产环境应使用Alembic迁移）
    """
    engine = get_engine()
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_database() -> None:
    """关闭数据库连接"""
    global _engine, _session_factory
    
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的上下文管理器
    
    用法：
        async with get_session() as session:
            # 使用session进行数据库操作
            ...
    
    Yields:
        AsyncSession: SQLAlchemy异步会话
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入用的数据库会话获取器
    
    用法：
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: SQLAlchemy异步会话
    """
    async with get_session() as session:
        yield session

