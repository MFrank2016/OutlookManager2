"""
Pytest配置和fixtures

提供测试中使用的通用fixtures
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# 添加src到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


# ============================================================================
# 事件循环配置
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# 数据库fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    提供数据库会话（每个测试函数一个新会话）
    
    使用in-memory SQLite数据库进行测试
    """
    from src.config.settings import settings
    from src.infrastructure.database.session import (
        get_session,
        init_database,
    )
    
    # 覆盖数据库URL为内存数据库
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    
    try:
        # 初始化数据库
        await init_database()
        
        # 提供会话
        async with get_session() as session:
            yield session
    finally:
        # 恢复原始URL
        settings.DATABASE_URL = original_url


# ============================================================================
# API客户端fixtures
# ============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """提供异步HTTP客户端（用于API测试）"""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# 认证fixtures
# ============================================================================

@pytest.fixture
async def admin_token(db_session: AsyncSession) -> str:
    """
    创建测试管理员并返回认证Token
    """
    from src.domain.entities import Admin
    from src.infrastructure.database.repositories import AdminRepositoryImpl
    from src.infrastructure.external_services.auth import get_jwt_service
    from src.infrastructure.external_services.oauth import PasswordServiceImpl
    
    # 创建测试管理员
    password_service = PasswordServiceImpl()
    password_hash = password_service.hash_password("testpass123")
    
    admin = Admin(
        username="testadmin",
        password_hash=password_hash,
        is_active=True
    )
    
    repository = AdminRepositoryImpl(db_session)
    created_admin = await repository.create(admin)
    
    # 生成Token
    jwt_service = get_jwt_service()
    token = jwt_service.create_access_token(
        created_admin.id,
        created_admin.username
    )
    
    return token


# ============================================================================
# 实体fixtures
# ============================================================================

@pytest.fixture
def sample_account():
    """提供示例账户数据"""
    from src.config.constants import AccountStatus, RefreshStatus
    from src.domain.entities import Account
    from src.domain.value_objects import EmailAddress
    
    return Account(
        email=EmailAddress.create("test@outlook.com"),
        refresh_token="test_refresh_token_12345",
        client_id="test_client_id_12345",
        tags=["test"],
        status=AccountStatus.ACTIVE,
        refresh_status=RefreshStatus.PENDING
    )


@pytest.fixture
def sample_admin():
    """提供示例管理员数据"""
    from src.domain.entities import Admin
    from src.infrastructure.external_services.oauth import PasswordServiceImpl
    
    password_service = PasswordServiceImpl()
    password_hash = password_service.hash_password("testpass123")
    
    return Admin(
        username="testadmin",
        password_hash=password_hash,
        is_active=True
    )


# ============================================================================
# Mock fixtures
# ============================================================================

@pytest.fixture
def mock_oauth_client(monkeypatch):
    """Mock OAuth客户端"""
    from datetime import datetime, timedelta
    from src.domain.value_objects import AccessToken
    
    class MockOAuthClient:
        async def refresh_token(self, credentials):
            # 返回mock的访问令牌
            token = AccessToken.create(
                value="mock_access_token",
                expires_in=3600
            )
            return token, None
        
        async def validate_token(self, access_token):
            return True
        
        async def revoke_token(self, refresh_token):
            return True
    
    return MockOAuthClient()


@pytest.fixture
def mock_imap_client(monkeypatch):
    """Mock IMAP客户端"""
    
    class MockIMAPClient:
        async def connect(self, email, access_token):
            return True
        
        async def disconnect(self):
            pass
        
        async def list_folders(self):
            return ["INBOX", "Junk", "Sent"]
        
        async def select_folder(self, folder):
            return 100  # 100封邮件
        
        async def fetch_emails(self, folder, limit=100, **kwargs):
            return []  # 返回空列表
        
        async def fetch_email_by_id(self, message_id):
            return None
        
        async def search_emails(self, folder, query, limit=100):
            return []
    
    return MockIMAPClient()

