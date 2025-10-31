"""
OAuth服务模块

提供OAuth2令牌获取、刷新等服务
"""

import logging

import httpx
from fastapi import HTTPException

from config import TOKEN_URL, OAUTH_SCOPE
from models import AccountCredentials

# 获取日志记录器
logger = logging.getLogger(__name__)


async def get_access_token(credentials: AccountCredentials) -> str:
    """
    使用refresh_token获取access_token

    Args:
        credentials: 账户凭证信息

    Returns:
        str: OAuth2访问令牌

    Raises:
        HTTPException: 令牌获取失败
    """
    # 构建OAuth2请求数据
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": OAUTH_SCOPE,
    }

    try:
        # 发送令牌请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            response.raise_for_status()

            # 解析响应
            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error(f"No access token in response for {credentials.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Failed to obtain access token from response",
                )

            logger.info(f"Successfully obtained access token for {credentials.email}")
            return access_token

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP {e.response.status_code} error getting access token for {credentials.email}: {e}"
        )
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token or client credentials"
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except httpx.RequestError as e:
        logger.error(f"Request error getting access token for {credentials.email}: {e}")
        raise HTTPException(
            status_code=500, detail="Network error during token acquisition"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting access token for {credentials.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Token acquisition failed")


async def refresh_account_token(credentials: AccountCredentials) -> dict:
    """
    刷新账户的refresh_token

    Args:
        credentials: 账户凭证信息

    Returns:
        dict: {
            'success': bool,
            'new_refresh_token': str (if success),
            'new_access_token': str (if success),
            'error': str (if failed)
        }
    """
    # 构建OAuth2请求数据
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": OAUTH_SCOPE,
    }

    try:
        # 发送令牌请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            response.raise_for_status()

            # 解析响应
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")

            if not new_access_token:
                logger.error(
                    f"No access token in refresh response for {credentials.email}"
                )
                return {"success": False, "error": "No access token in response"}

            if not new_refresh_token:
                logger.warning(
                    f"No new refresh token in response for {credentials.email}, using existing one"
                )
                new_refresh_token = credentials.refresh_token

            logger.info(f"Successfully refreshed token for {credentials.email}")
            return {
                "success": True,
                "new_refresh_token": new_refresh_token,
                "new_access_token": new_access_token,
            }

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} error refreshing token"
        logger.error(f"{error_msg} for {credentials.email}: {e}")
        return {"success": False, "error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Network error refreshing token: {str(e)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}

