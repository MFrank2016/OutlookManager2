"""
数据库依赖

提供数据库会话的依赖注入
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db

async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（FastAPI依赖）
    
    Yields:
        AsyncSession: SQLAlchemy异步会话
    """
    async for session in get_db():
        yield session

