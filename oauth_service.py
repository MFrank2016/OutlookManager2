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
import cache_service

# 获取日志记录器
logger = logging.getLogger(__name__)


async def get_access_token(credentials: AccountCredentials) -> str:
    """
    从 OAuth2 接口获取新的 access_token（不使用缓存）
    
    此函数会：
    1. 调用 OAuth2 接口获取新 token
    2. 自动尝试 fallback scope（如果主 scope 失败）
    3. 保存 token 到数据库和内存缓存
    
    注意：此函数不检查缓存。如果需要使用缓存，请调用 get_cached_access_token()

    Args:
        credentials: 账户凭证信息

    Returns:
        str: OAuth2访问令牌

    Raises:
        HTTPException: 令牌获取失败
    """
    # Determine scope based on api_method
    api_method = getattr(credentials, "api_method", "imap")
    # 如果没有明确指定 api_method，或者已经是 imap，我们默认先试 OAUTH_SCOPE
    # 如果是 graph，先试 GRAPH_API_SCOPE
    primary_scope = GRAPH_API_SCOPE if api_method in ["graph", "graph_api"] else OAUTH_SCOPE
    fallback_scope = OAUTH_SCOPE if api_method in ["graph", "graph_api"] else GRAPH_API_SCOPE
    
    logger.info(f"Fetching new access token for {credentials.email}, api_method: {api_method}, trying scope: {primary_scope}")

    # 定义内部函数来尝试获取 token
    async def _try_get_token(scope_to_try):
        token_request_data = {
            "client_id": credentials.client_id,
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token,
            "scope": scope_to_try,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            return response

    try:
        # 第一次尝试
        response = await _try_get_token(primary_scope)
        
        # 如果失败且状态码为 400 (invalid_grant/invalid_scope)，尝试 fallback scope
        if response.status_code == 400:
            error_data = response.json()
            error_desc = error_data.get('error_description', '')
            # AADSTS70000 包含 unauthorized_scope 等错误
            if 'AADSTS70000' in error_desc or 'scope' in error_desc.lower():
                logger.warning(f"Token request failed with scope {primary_scope}, trying fallback scope {fallback_scope}. Error: {error_desc[:100]}...")
                response = await _try_get_token(fallback_scope)
                
                # 如果第二次尝试成功，我们需要更新账户的 api_method
                if response.status_code == 200:
                    new_method = "graph_api" if fallback_scope == GRAPH_API_SCOPE else "imap"
                    logger.info(f"Fallback scope succeeded. Updating api_method to {new_method} for {credentials.email}")
                    try:
                        db.update_account(credentials.email, api_method=new_method)
                        # 同时也更新 credentials 对象，以便后续使用
                        if hasattr(credentials, 'api_method'):
                            credentials.api_method = new_method
                    except Exception as e:
                        logger.error(f"Failed to update api_method in db: {e}")

        # 检查最终响应状态
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
        expires_in = token_data.get("expires_in", 3600)  # Microsoft 返回的过期时间（通常1小时）
        
        # 设置 access token 的缓存时间为 3 小时
        # 这样可以减少频繁刷新，同时保持合理的安全性
        cache_hours = 3
        cache_seconds = cache_hours * 3600  # 3小时 = 10800秒
        
        # 使用较小的值：Microsoft 返回的过期时间或 3 小时，取较小者
        actual_expires_in = min(expires_in, cache_seconds)

        if not access_token:
            logger.error(f"No access token in response for {credentials.email}")
            raise HTTPException(
                status_code=401,
                detail="Failed to obtain access token from response",
            )

        # 计算过期时间（使用实际过期时间，最多3小时）
        expires_at = datetime.now() + timedelta(seconds=actual_expires_in)
        expires_at_str = expires_at.isoformat()
        
        logger.debug(
            f"Access token for {credentials.email}: Microsoft expires_in={expires_in}s, "
            f"actual cache time={actual_expires_in}s ({actual_expires_in/3600:.1f}h)"
        )
        
        # 保存 token 到数据库
        db.update_account_access_token(credentials.email, access_token, expires_at_str)
        
        # 同时缓存到内存（LRU缓存）
        cache_service.set_cached_access_token(credentials.email, access_token, expires_at_str)

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
    # Determine scope based on api_method
    api_method = getattr(credentials, "api_method", "imap")
    primary_scope = GRAPH_API_SCOPE if api_method in ["graph", "graph_api"] else OAUTH_SCOPE
    fallback_scope = OAUTH_SCOPE if api_method in ["graph", "graph_api"] else GRAPH_API_SCOPE
    
    # 定义内部函数来尝试刷新 token
    async def _try_refresh_token(scope_to_try):
        token_request_data = {
            "client_id": credentials.client_id,
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token,
            "scope": scope_to_try,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await client.post(TOKEN_URL, data=token_request_data)

    try:
        # 发送令牌请求
        response = await _try_refresh_token(primary_scope)
        
        # 如果失败且状态码为 400，尝试 fallback scope
        if response.status_code == 400:
            try:
                error_data = response.json()
                error_desc = error_data.get('error_description', '')
                if 'AADSTS70000' in error_desc or 'scope' in error_desc.lower():
                    logger.warning(f"Token refresh failed with scope {primary_scope}, trying fallback scope {fallback_scope} for {credentials.email}")
                    response = await _try_refresh_token(fallback_scope)
                    
                    if response.status_code == 200:
                        new_method = "graph_api" if fallback_scope == GRAPH_API_SCOPE else "imap"
                        logger.info(f"Fallback refresh succeeded. Updating api_method to {new_method} for {credentials.email}")
                        try:
                            db.update_account(credentials.email, api_method=new_method)
                        except Exception as e:
                            logger.error(f"Failed to update api_method in db: {e}")
            except Exception:
                pass  # 如果解析JSON失败，忽略，继续处理原响应

        if response.status_code in [400, 401, 403]:
            error_msg = f"OAuth2 Error: {response.json().get('error_description', 'Invalid grant')}"
            logger.error(f"Token refresh failed for {credentials.email}: {error_msg}")
            return {"success": False, "error": error_msg}
            
        response.raise_for_status()

        # 解析响应
        token_data = response.json()
        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)  # Microsoft 返回的过期时间（通常1小时）

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

        # 计算 access token 过期时间（设置为3小时）
        access_token_expires_hours = 3
        expires_at = datetime.now() + timedelta(hours=access_token_expires_hours)
        expires_at_str = expires_at.isoformat()

        logger.info(f"Successfully refreshed token for {credentials.email}, access token expires in {access_token_expires_hours} hours")
        return {
            "success": True,
            "new_refresh_token": new_refresh_token,
            "new_access_token": new_access_token,
            "access_token_expires_at": expires_at_str,
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
    
    优先从内存LRU缓存获取，如果不存在则从数据库获取，最后才请求新token
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        str: OAuth2访问令牌
        
    Raises:
        HTTPException: 令牌获取失败
    """
    # 1. 优先从内存LRU缓存获取（需要检查过期时间）
    cache_key = cache_service.get_access_token_cache_key(credentials.email)
    if cache_key in cache_service.access_token_cache:
        token_data = cache_service.access_token_cache[cache_key]
        
        # token_data 可能是字符串或字典
        if isinstance(token_data, dict):
            cached_token = token_data.get('access_token')
            expires_at_str = token_data.get('expires_at')
            
            if cached_token and expires_at_str:
                try:
                    # 解析过期时间
                    if isinstance(expires_at_str, datetime):
                        expires_at = expires_at_str
                    else:
                        expires_at = datetime.fromisoformat(expires_at_str)
                    
                    now = datetime.now()
                    time_until_expiry = (expires_at - now).total_seconds()
                    
                    # 检查 token 是否还有效（距离过期时间 > 10 minutes）
                    if time_until_expiry > 600:  # 10 minutes = 600 seconds
                        logger.debug(
                            f"Using LRU cached access token for {credentials.email}, "
                            f"expires in {int(time_until_expiry/60)} minutes"
                        )
                        return cached_token
                    else:
                        # Token 已过期或即将过期，清除缓存
                        logger.info(
                            f"LRU cached token for {credentials.email} expires soon "
                            f"(in {int(time_until_expiry/60)} minutes), clearing cache and refreshing..."
                        )
                        cache_service.clear_cached_access_token(credentials.email)
                except Exception as e:
                    logger.warning(f"Error parsing LRU cache token expiry time for {credentials.email}: {e}")
                    # 解析失败，清除缓存
                    cache_service.clear_cached_access_token(credentials.email)
            elif cached_token:
                # 有 token 但没有过期时间信息，直接使用（向后兼容）
                logger.debug(f"Using LRU cached access token for {credentials.email} (no expiry info)")
                return cached_token
        elif isinstance(token_data, str):
            # 旧格式：直接是字符串，没有过期时间信息
            logger.debug(f"Using LRU cached access token for {credentials.email} (legacy format)")
            return token_data
    
    # 2. 尝试从数据库获取缓存的 token
    token_info = db.get_account_access_token(credentials.email)
    
    if token_info:
        access_token = token_info['access_token']
        expires_at_str = token_info['token_expires_at']
        
        try:
            # 解析过期时间（处理 datetime 对象或字符串）
            if isinstance(expires_at_str, datetime):
                expires_at = expires_at_str
                expires_at_str = expires_at.isoformat()  # 转换为字符串用于缓存
            else:
                expires_at = datetime.fromisoformat(expires_at_str)
            
            now = datetime.now()
            
            # 检查 token 是否还有效（距离过期时间 > 1 小时，因为 access token 缓存时间为 3 小时）
            time_until_expiry = (expires_at - now).total_seconds()
            
            if time_until_expiry > 600:  # 10分钟 = 600秒（access token 缓存时间为 3 小时，提前 10分钟刷新）
                # 将数据库中的token缓存到内存
                cache_service.set_cached_access_token(credentials.email, access_token, expires_at_str)
                logger.info(
                    f"Using database cached access token for {credentials.email}, "
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
    
    # 3. Token 不存在、即将过期或解析失败，获取新 token
    logger.info(f"Fetching new access token for {credentials.email}")
    return await get_access_token(credentials)


async def clear_cached_access_token(email: str) -> bool:
    """
    清除账户的缓存 access token（用于容错重试）
    
    清除内存LRU缓存和数据库缓存
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否清除成功
    """
    try:
        # 清除内存LRU缓存
        cache_service.clear_cached_access_token(email)
        
        # 清除数据库缓存
        success = db.update_account_access_token(email, "", "")
        if success:
            logger.info(f"Cleared cached access token for {email} (both memory and database)")
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
