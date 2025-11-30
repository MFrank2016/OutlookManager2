"""
OAuth服务模块

提供OAuth2令牌获取、刷新等服务
"""

import logging
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException

from config import TOKEN_URL, OAUTH_SCOPE, GRAPH_API_SCOPE
from models import AccountCredentials
import database as db

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
    # Determine scope based on api_method
    api_method = getattr(credentials, "api_method", "imap")
    logger.info(f"Credentials: {credentials}, api_method: {api_method}")
    scope = GRAPH_API_SCOPE if api_method in ["graph", "graph_api"] else OAUTH_SCOPE

    # 构建OAuth2请求数据
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": scope,
    }
    logger.info(f"Token request data: {token_request_data}")
    logger.info(f"Scope: {scope}")
    logger.info(f"Client ID: {credentials.client_id}")
    logger.info(f"Refresh token: {credentials.refresh_token}")
    logger.info(f"Token URL: {TOKEN_URL}")

    try:
        # 发送令牌请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            
            # 检查状态码，如果是400/401/403，说明refresh token无效或过期
            if response.status_code in [400, 401, 403]:
                logger.error(f"OAuth2 token request failed for {credentials.email}: {response.text}")
                # 抛出具体的错误信息，而不是401 Unauthorized
                error_detail = f"OAuth2 Error: {response.json().get('error_description', 'Invalid grant')}"
                raise HTTPException(
                    status_code=400,
                    detail=error_detail,
                )
            
            response.raise_for_status()

            # 解析响应
            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # 默认1小时

            if not access_token:
                logger.error(f"No access token in response for {credentials.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Failed to obtain access token from response",
                )

            # 计算过期时间（expires_in 是秒数）
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            expires_at_str = expires_at.isoformat()
            
            # 保存 token 到数据库
            db.update_account_access_token(credentials.email, access_token, expires_at_str)

            logger.info(
                f"Successfully obtained access token for {credentials.email}, "
                f"expires in {expires_in}s at {expires_at_str}"
            )
            return access_token

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP {e.response.status_code} error getting access token for {credentials.email}: {e}"
        )
        # 捕获其他 HTTP 错误
        if e.response.status_code == 400:
             raise HTTPException(
                status_code=400, 
                detail=f"OAuth2 Error: {e.response.json().get('error_description', 'Invalid request')}"
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except httpx.RequestError as e:
        logger.error(f"Request error getting access token for {credentials.email}: {e}")
        raise HTTPException(
            status_code=500, detail="Network error during token acquisition"
        )
    except HTTPException:
        raise
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
            
            if response.status_code in [400, 401, 403]:
                error_msg = f"OAuth2 Error: {response.json().get('error_description', 'Invalid grant')}"
                logger.error(f"Token refresh failed for {credentials.email}: {error_msg}")
                return {"success": False, "error": error_msg}
                
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


async def get_cached_access_token(credentials: AccountCredentials) -> str:
    """
    获取缓存的 access token，如果不存在或即将过期则自动刷新
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        str: OAuth2访问令牌
        
    Raises:
        HTTPException: 令牌获取失败
    """
    # 尝试从数据库获取缓存的 token
    token_info = db.get_account_access_token(credentials.email)
    
    if token_info:
        access_token = token_info['access_token']
        expires_at_str = token_info['token_expires_at']
        
        try:
            # 解析过期时间
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now()
            
            # 检查 token 是否还有效（距离过期时间 > 10 分钟）
            time_until_expiry = (expires_at - now).total_seconds()
            
            if time_until_expiry > 600:  # 10分钟 = 600秒
                logger.info(
                    f"Using cached access token for {credentials.email}, "
                    f"expires in {int(time_until_expiry/60)} minutes"
                )
                return access_token
            else:
                logger.info(
                    f"Cached token for {credentials.email} expires soon "
                    f"(in {int(time_until_expiry/60)} minutes), refreshing..."
                )
        except Exception as e:
            logger.warning(f"Error parsing token expiry time for {credentials.email}: {e}")
    
    # Token 不存在、即将过期或解析失败，获取新 token
    logger.info(f"Fetching new access token for {credentials.email}")
    return await get_access_token(credentials)


async def clear_cached_access_token(email: str) -> bool:
    """
    清除账户的缓存 access token（用于容错重试）
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否清除成功
    """
    try:
        # 将 token 设置为 NULL
        success = db.update_account_access_token(email, "", "")
        if success:
            logger.info(f"Cleared cached access token for {email}")
        return success
    except Exception as e:
        logger.error(f"Error clearing cached token for {email}: {e}")
        return False


async def detect_and_update_api_method(credentials: AccountCredentials) -> str:
    """
    检测账户支持的 API 方法并更新数据库
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        str: 检测到的 API 方法 ('graph_api' 或 'imap')
    """
    from graph_api_service import check_graph_api_availability
    
    try:
        # 检测 Graph API 可用性
        result = await check_graph_api_availability(credentials)
        
        if result["available"]:
            # 更新数据库中的 api_method 字段
            db.update_account(credentials.email, api_method="graph_api")
            logger.info(f"Detected and set Graph API for {credentials.email}")
            return "graph_api"
        else:
            # 使用 IMAP
            db.update_account(credentials.email, api_method="imap")
            logger.info(f"Graph API not available for {credentials.email}, using IMAP")
            return "imap"
            
    except Exception as e:
        logger.error(f"Error detecting API method for {credentials.email}: {e}")
        # 出错时默认使用 IMAP
        db.update_account(credentials.email, api_method="imap")
        return "imap"
