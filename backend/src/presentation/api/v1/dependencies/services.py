"""
服务依赖

提供各种服务的依赖注入
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces import ICacheService, IIMAPClient, IOAuthClient
from src.application.use_cases.account import (
    CreateAccountUseCase,
    DeleteAccountUseCase,
    GetAccountUseCase,
    ListAccountsUseCase,
    RefreshTokenUseCase,
    UpdateAccountUseCase,
)
from src.application.use_cases.auth import (
    ChangePasswordUseCase,
    LoginUseCase,
    VerifyTokenUseCase,
)
from src.application.use_cases.email import (
    GetEmailDetailUseCase,
    ListEmailsUseCase,
    SearchEmailsUseCase,
)
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.repositories.admin_repository import IAdminRepository
from src.domain.services import IPasswordService, ITokenService
from src.infrastructure.cache import get_cache_service
from src.infrastructure.database.repositories import (
    AccountRepositoryImpl,
    AdminRepositoryImpl,
)
from src.infrastructure.external_services.imap import IMAPClientImpl
from src.infrastructure.external_services.oauth import (
    OAuthClientImpl,
    PasswordServiceImpl,
    TokenServiceImpl,
)
from src.presentation.api.v1.dependencies.database import get_database


# ============================================================================
# 基础服务依赖
# ============================================================================

def get_oauth_client() -> IOAuthClient:
    """获取OAuth客户端"""
    return OAuthClientImpl()


def get_password_service() -> IPasswordService:
    """获取密码服务"""
    return PasswordServiceImpl()


def get_token_service(
    oauth_client: IOAuthClient = Depends(get_oauth_client)
) -> ITokenService:
    """获取Token服务"""
    return TokenServiceImpl(oauth_client)


def get_imap_client() -> IIMAPClient:
    """获取IMAP客户端"""
    return IMAPClientImpl()


def get_cache_service_dep() -> ICacheService:
    """获取缓存服务"""
    return get_cache_service()


# ============================================================================
# 仓储依赖
# ============================================================================

def get_account_repository(
    session: AsyncSession = Depends(get_database)
) -> IAccountRepository:
    """获取账户仓储"""
    return AccountRepositoryImpl(session)


def get_admin_repository(
    session: AsyncSession = Depends(get_database)
) -> IAdminRepository:
    """获取管理员仓储"""
    return AdminRepositoryImpl(session)


# ============================================================================
# 用例依赖 - 账户管理
# ============================================================================

def get_create_account_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository)
) -> CreateAccountUseCase:
    """获取创建账户用例"""
    return CreateAccountUseCase(account_repository)


def get_list_accounts_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository)
) -> ListAccountsUseCase:
    """获取列表账户用例"""
    return ListAccountsUseCase(account_repository)


def get_get_account_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository)
) -> GetAccountUseCase:
    """获取获取账户用例"""
    return GetAccountUseCase(account_repository)


def get_update_account_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository)
) -> UpdateAccountUseCase:
    """获取更新账户用例"""
    return UpdateAccountUseCase(account_repository)


def get_delete_account_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository)
) -> DeleteAccountUseCase:
    """获取删除账户用例"""
    return DeleteAccountUseCase(account_repository)


def get_refresh_token_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository),
    oauth_client: IOAuthClient = Depends(get_oauth_client),
    token_service: ITokenService = Depends(get_token_service)
) -> RefreshTokenUseCase:
    """获取刷新Token用例"""
    return RefreshTokenUseCase(account_repository, oauth_client, token_service)


# ============================================================================
# 用例依赖 - 邮件管理
# ============================================================================

def get_list_emails_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository),
    imap_client: IIMAPClient = Depends(get_imap_client),
    oauth_client: IOAuthClient = Depends(get_oauth_client),
    cache_service: ICacheService = Depends(get_cache_service_dep)
) -> ListEmailsUseCase:
    """获取列表邮件用例"""
    return ListEmailsUseCase(
        account_repository,
        imap_client,
        oauth_client,
        cache_service
    )


def get_get_email_detail_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository),
    imap_client: IIMAPClient = Depends(get_imap_client),
    oauth_client: IOAuthClient = Depends(get_oauth_client),
    cache_service: ICacheService = Depends(get_cache_service_dep)
) -> GetEmailDetailUseCase:
    """获取获取邮件详情用例"""
    return GetEmailDetailUseCase(
        account_repository,
        imap_client,
        oauth_client,
        cache_service
    )


def get_search_emails_use_case(
    account_repository: IAccountRepository = Depends(get_account_repository),
    imap_client: IIMAPClient = Depends(get_imap_client),
    oauth_client: IOAuthClient = Depends(get_oauth_client),
    cache_service: ICacheService = Depends(get_cache_service_dep)
) -> SearchEmailsUseCase:
    """获取搜索邮件用例"""
    return SearchEmailsUseCase(
        account_repository,
        imap_client,
        oauth_client,
        cache_service
    )


# ============================================================================
# 用例依赖 - 认证管理
# ============================================================================

def get_login_use_case(
    admin_repository: IAdminRepository = Depends(get_admin_repository),
    password_service: IPasswordService = Depends(get_password_service)
) -> LoginUseCase:
    """获取登录用例"""
    return LoginUseCase(admin_repository, password_service)


def get_change_password_use_case(
    admin_repository: IAdminRepository = Depends(get_admin_repository),
    password_service: IPasswordService = Depends(get_password_service)
) -> ChangePasswordUseCase:
    """获取修改密码用例"""
    return ChangePasswordUseCase(admin_repository, password_service)


def get_verify_token_use_case(
    admin_repository: IAdminRepository = Depends(get_admin_repository)
) -> VerifyTokenUseCase:
    """获取验证Token用例"""
    return VerifyTokenUseCase(admin_repository)

