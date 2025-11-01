"""
账户服务模块

提供账户凭证管理、账户列表查询等服务
"""

import logging
from typing import Optional

from fastapi import HTTPException

import database as db
from models import AccountCredentials, AccountInfo, AccountListResponse

# 获取日志记录器
logger = logging.getLogger(__name__)


async def get_account_credentials(email_id: str) -> AccountCredentials:
    """
    从SQLite数据库获取指定邮箱的账户凭证

    Args:
        email_id: 邮箱地址

    Returns:
        AccountCredentials: 账户凭证对象

    Raises:
        HTTPException: 账户不存在或数据库读取失败
    """
    try:
        # 从数据库获取账户信息
        account = db.get_account_by_email(email_id)

        # 检查账户是否存在
        if not account:
            logger.warning(f"Account {email_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Account {email_id} not found")

        # 验证账户数据完整性
        required_fields = ["refresh_token", "client_id"]
        missing_fields = [field for field in required_fields if not account.get(field)]

        if missing_fields:
            logger.error(
                f"Account {email_id} missing required fields: {missing_fields}"
            )
            raise HTTPException(
                status_code=500, detail="Account configuration incomplete"
            )

        return AccountCredentials(
            email=account["email"],
            refresh_token=account["refresh_token"],
            client_id=account["client_id"],
            tags=account.get("tags", []),
            last_refresh_time=account.get("last_refresh_time"),
            next_refresh_time=account.get("next_refresh_time"),
            refresh_status=account.get("refresh_status", "pending"),
            refresh_error=account.get("refresh_error"),
            api_method=account.get("api_method", "imap"),
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting account credentials for {email_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def save_account_credentials(
    email_id: str, credentials: AccountCredentials
) -> None:
    """保存账户凭证到SQLite数据库"""
    try:
        # 检查账户是否已存在
        existing_account = db.get_account_by_email(email_id)

        if existing_account:
            # 更新现有账户
            db.update_account(
                email_id,
                refresh_token=credentials.refresh_token,
                client_id=credentials.client_id,
                tags=credentials.tags if hasattr(credentials, "tags") else [],
                last_refresh_time=credentials.last_refresh_time,
                next_refresh_time=credentials.next_refresh_time,
                refresh_status=credentials.refresh_status,
                refresh_error=credentials.refresh_error,
            )
        else:
            # 创建新账户
            db.create_account(
                email=email_id,
                refresh_token=credentials.refresh_token,
                client_id=credentials.client_id,
                tags=credentials.tags if hasattr(credentials, "tags") else [],
            )

            # 更新额外字段
            if credentials.last_refresh_time or credentials.next_refresh_time:
                db.update_account(
                    email_id,
                    last_refresh_time=credentials.last_refresh_time,
                    next_refresh_time=credentials.next_refresh_time,
                    refresh_status=credentials.refresh_status,
                    refresh_error=credentials.refresh_error,
                )

        logger.info(f"Account credentials saved for {email_id}")
    except Exception as e:
        logger.error(f"Error saving account credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to save account")


async def get_all_accounts(
    page: int = 1,
    page_size: int = 10,
    email_search: Optional[str] = None,
    tag_search: Optional[str] = None,
) -> AccountListResponse:
    """获取所有已加载的邮箱账户列表，支持分页和搜索"""
    try:
        # 从数据库获取账户列表
        accounts_data, total_accounts = db.get_all_accounts_db(
            page=page,
            page_size=page_size,
            email_search=email_search,
            tag_search=tag_search,
        )

        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get(
                    "client_id"
                ):
                    status = "invalid"
            except Exception:
                status = "error"

            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
                api_method=account_data.get("api_method", "imap"),
            )
            all_accounts.append(account)

        # 计算分页信息
        total_pages = (
            (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        )

        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )

    except Exception as e:
        logger.error(f"Error getting accounts list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

