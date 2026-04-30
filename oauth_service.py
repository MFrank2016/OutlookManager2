"""
OAuth服务模块

提供OAuth2令牌获取、刷新等服务
"""

from datetime import datetime, timezone

import httpx
import database as db
from fastapi import HTTPException
from logger_config import logger
from microsoft_access import TokenBroker
from models import AccountCredentials


# 统一的UTC时间获取函数，避免时区问题
def get_utc_now() -> datetime:
    """获取当前UTC时间（时区感知）"""
    return datetime.now(timezone.utc)


_token_broker = TokenBroker(now_fn=get_utc_now)


def _raise_token_acquisition_network_error() -> None:
    raise HTTPException(status_code=500, detail="Network error during token acquisition")


async def get_access_token(credentials: AccountCredentials) -> str:
    """获取新的 access token（不使用缓存）。"""
    try:
        result = await _token_broker.fetch_access_token(credentials, persist=True)
        return result.access_token
    except httpx.RequestError:
        _raise_token_acquisition_network_error()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error getting access token for {credentials.email}: {exc}")
        raise HTTPException(status_code=500, detail="Token acquisition failed")


async def refresh_account_token(credentials: AccountCredentials) -> dict:
    """刷新账户 token，保持旧返回结构兼容。"""
    try:
        return await _token_broker.refresh_access_token(credentials)
    except httpx.RequestError as exc:
        error_msg = f"Network error refreshing token: {str(exc)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}
    except HTTPException as exc:
        return {"success": False, "error": str(exc.detail)}
    except Exception as exc:
        error_msg = f"Unexpected error: {str(exc)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}


async def get_cached_access_token(credentials: AccountCredentials) -> str:
    """获取缓存 access token，不存在或即将过期时自动刷新。"""
    try:
        return await _token_broker.get_cached_access_token(credentials)
    except httpx.RequestError:
        _raise_token_acquisition_network_error()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            f"Unexpected error getting cached access token for {credentials.email}: {exc}"
        )
        raise HTTPException(status_code=500, detail="Token acquisition failed")


async def clear_cached_access_token(email: str) -> bool:
    """清除账户缓存的 access token。"""
    try:
        return await _token_broker.clear_cached_access_token(email)
    except Exception as exc:
        logger.error(f"Error clearing cached token for {email}: {exc}")
        return False


async def detect_and_update_api_method(credentials: AccountCredentials) -> str:
    """
    检测账户支持的 API 方法并更新数据库

    Args:
        credentials: 账户凭证信息

    Returns:
        str: 检测到的 API 方法 ('graph_api' 或 'imap')
    """
    from graph_api_service import (
        check_graph_api_availability,
        probe_confirms_graph_read_unavailable,
        probe_supports_graph_read,
    )

    try:
        result = await check_graph_api_availability(credentials)

        if probe_supports_graph_read(result):
            db.update_account(credentials.email, api_method="graph_api")
            logger.info(f"Detected and set Graph API for {credentials.email}")
            return "graph_api"

        if probe_confirms_graph_read_unavailable(result):
            db.update_account(credentials.email, api_method="imap")
            logger.info(f"Graph read capability unavailable for {credentials.email}, using IMAP")
            return "imap"

        logger.info(
            f"Graph read capability unknown for {credentials.email}, "
            "temporarily using IMAP without persisting api_method"
        )
        return "imap"

    except Exception as exc:
        logger.error(f"Error detecting API method for {credentials.email}: {exc}")
        return "imap"
