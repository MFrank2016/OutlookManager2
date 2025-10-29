"""API依赖注入"""
from .auth import get_current_admin
from .database import get_database
from .services import (
    get_account_repository,
    get_admin_repository,
    get_change_password_use_case,
    get_create_account_use_case,
    get_delete_account_use_case,
    get_get_account_use_case,
    get_get_email_detail_use_case,
    get_list_accounts_use_case,
    get_list_emails_use_case,
    get_login_use_case,
    get_refresh_token_use_case,
    get_search_emails_use_case,
    get_update_account_use_case,
    get_verify_token_use_case,
)

__all__ = [
    # Database
    "get_database",
    # Auth
    "get_current_admin",
    # Repositories
    "get_account_repository",
    "get_admin_repository",
    # Use Cases
    "get_create_account_use_case",
    "get_list_accounts_use_case",
    "get_get_account_use_case",
    "get_update_account_use_case",
    "get_delete_account_use_case",
    "get_refresh_token_use_case",
    "get_list_emails_use_case",
    "get_get_email_detail_use_case",
    "get_search_emails_use_case",
    "get_login_use_case",
    "get_change_password_use_case",
    "get_verify_token_use_case",
]

