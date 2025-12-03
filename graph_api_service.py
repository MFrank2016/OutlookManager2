"""
Microsoft Graph API 服务模块

提供基于 Graph API 的邮件操作功能，包括列表、详情、删除和发送
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx
from fastapi import HTTPException

from config import GRAPH_API_BASE_URL, GRAPH_API_SCOPE, TOKEN_URL
from models import AccountCredentials, EmailItem, EmailDetailsResponse
from verification_code_detector import detect_verification_code
import database as db
import cache_service

# 获取日志记录器
logger = logging.getLogger(__name__)


async def get_graph_access_token(credentials: AccountCredentials) -> str:
    """
    获取 Graph API 访问令牌（使用缓存机制）
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        str: Graph API 访问令牌
        
    Raises:
        HTTPException: 令牌获取失败
    """
    from oauth_service import get_cached_access_token
    
    try:
        # 使用统一的缓存机制获取 access token
        access_token = await get_cached_access_token(credentials)
        
        # 格式化 token 信息用于日志
        if len(access_token) <= 16:
            masked_token = access_token[:4] + "..." + access_token[-4:]
        else:
            masked_token = access_token[:8] + "..." + access_token[-8:]
        
        # 获取过期时间信息用于日志
        import database as db
        token_info = db.get_account_access_token(credentials.email)
        if token_info:
            expires_at_str = token_info.get('token_expires_at')
            if expires_at_str:
                from datetime import datetime
                if isinstance(expires_at_str, datetime):
                    expires_at = expires_at_str
                else:
                    expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.now()
                expires_in = int((expires_at - now).total_seconds())
                logger.info(f"[Token信息] 账户: {credentials.email}, Graph API Token: {masked_token}, Expires in: {expires_in} seconds ({int(expires_in/60)} minutes)")
            else:
                logger.info(f"[Token信息] 账户: {credentials.email}, Graph API Token: {masked_token}")
        else:
            logger.info(f"[Token信息] 账户: {credentials.email}, Graph API Token: {masked_token}")
        
        return access_token
            
    except Exception as e:
        logger.error(f"Error getting Graph API token for {credentials.email}: {e}")
        raise HTTPException(status_code=500, detail="Graph API token acquisition failed")


async def check_graph_api_availability(credentials: AccountCredentials) -> Dict[str, Any]:
    """
    检测账户是否支持 Graph API（是否有 Mail.ReadWrite 权限）
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        dict: {
            'available': bool,
            'access_token': str (if available),
            'scope': str (if available)
        }
    """
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": GRAPH_API_SCOPE,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            scope = token_data.get("scope", "")
            
            # 检查是否包含 Mail.ReadWrite 或 Mail.Read 权限（参考 mail-all.js 的实现）
            # mail-all.js 中检查: data.scope.indexOf('https://graph.microsoft.com/Mail.ReadWrite') != -1
            has_mail_permission = (
                "Mail.ReadWrite" in scope or 
                "Mail.Read" in scope or
                "https://graph.microsoft.com/Mail.ReadWrite" in scope or
                "https://graph.microsoft.com/Mail.Read" in scope
            )
            
            logger.info(
                f"Graph API availability check for {credentials.email}: "
                f"available={has_mail_permission}, scope={scope}"
            )
            
            return {
                "available": has_mail_permission,
                "access_token": access_token if has_mail_permission else None,
                "scope": scope
            }
            
    except Exception as e:
        logger.warning(f"Graph API availability check failed for {credentials.email}: {e}")
        return {
            "available": False,
            "access_token": None,
            "scope": ""
        }


async def list_emails_graph(
    credentials: AccountCredentials,
    folder: str,
    page: int,
    page_size: int,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> tuple[List[EmailItem], int]:
    """
    使用 Graph API 获取邮件列表
    
    Args:
        credentials: 账户凭证
        folder: 文件夹名称 ('inbox', 'junk', 'all')
        page: 页码
        page_size: 每页大小
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间 (ISO8601)
        end_time: 结束时间 (ISO8601)
        
    Returns:
        tuple: (邮件列表, 总数)
    """
    access_token = await get_graph_access_token(credentials)
    
    # 映射文件夹名称
    folder_map = {
        "inbox": "inbox",
        "junk": "junkemail",
        "all": None  # 需要分别获取
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_emails = []
    
    # 确定要查询的文件夹
    folders_to_query = []
    if folder == "all":
        folders_to_query = ["inbox", "junkemail"]
    else:
        folders_to_query = [folder_map.get(folder, "inbox")]
    
    try:
        # 增加超时时间，并添加重试机制
        timeout = httpx.Timeout(10.0, connect=5.0)  # 总超时10秒，连接超时5秒
        async with httpx.AsyncClient(timeout=timeout) as client:
            for folder_name in folders_to_query:
                # 构建查询参数（参考 mail-all.js 的实现，使用 $top=10000）
                params = {
                    "$top": 1000,  # 一次性获取大量邮件（参考 mail-all.js）
                    "$orderby": "receivedDateTime desc",  # 按接收时间降序排序
                    "$select": "id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview"
                }
                
                # 添加过滤条件
                filters = []
                if sender_search:
                    filters.append(f"contains(from/emailAddress/address, '{sender_search}')")
                if subject_search:
                    filters.append(f"contains(subject, '{subject_search}')")
                if start_time:
                    filters.append(f"receivedDateTime ge {start_time}")
                if end_time:
                    filters.append(f"receivedDateTime le {end_time}")
                
                if filters:
                    params["$filter"] = " and ".join(filters)
                
                url = f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages"
                
                # 添加重试机制（包括 401 错误处理）
                max_retries = 2
                last_error = None
                token_refreshed = False
                response = None
                for attempt in range(max_retries + 1):
                    try:
                        logger.info(f"Requesting URL: {url}, Headers: {headers}, Params: {params}")
                        response = await client.get(url, headers=headers, params=params)
                        logger.info(f"Response: {response.text[:200]}...")
                        # 处理 401 未授权错误（token 过期或无效）
                        if response.status_code == 401:
                            if not token_refreshed:
                                logger.warning(
                                    f"Received 401 Unauthorized for {credentials.email}, "
                                    f"clearing cache and refreshing token..."
                                )
                                # 清除缓存的 token
                                from oauth_service import clear_cached_access_token
                                await clear_cached_access_token(credentials.email)
                                
                                # 重新获取 token
                                access_token = await get_graph_access_token(credentials)
                                headers["Authorization"] = f"Bearer {access_token}"
                                token_refreshed = True
                                
                                # 重试请求（不增加 attempt 计数，继续循环）
                                continue
                            else:
                                # 已经刷新过 token，还是 401，说明凭证有问题
                                logger.error(
                                    f"401 Unauthorized persists after token refresh for {credentials.email}. "
                                    f"Response: {response.text[:200]}"
                                )
                                response.raise_for_status()  # 抛出异常
                        
                        response.raise_for_status()
                        break  # 成功，退出重试循环
                    except (httpx.ConnectError, httpx.TimeoutException) as e:
                        last_error = e
                        if attempt < max_retries:
                            wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒
                            logger.warning(
                                f"Network error fetching emails from {folder_name} for {credentials.email} "
                                f"(attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            raise  # 最后一次尝试失败，抛出异常
                
                if response is None:
                    raise httpx.RequestError("Failed to get response after retries")
                
                data = response.json()
                emails = data.get("value", [])
                
                # 转换为 EmailItem 格式
                for email in emails:
                    from_data = email.get("from", {}).get("emailAddress", {})
                    from_email = from_data.get("address", "(Unknown Sender)")
                    
                    # 提取发件人首字母
                    sender_initial = "?"
                    email_match = re.search(r"([a-zA-Z])", from_email)
                    if email_match:
                        sender_initial = email_match.group(1).upper()
                    
                    subject = email.get("subject", "(No Subject)")
                    body_preview = email.get("bodyPreview", "")
                    
                    # 检测验证码（只从 body_plain 中检测）
                    verification_code = None
                    try:
                        # 使用 bodyPreview 作为 body_plain 的替代
                        code_info = detect_verification_code(subject="", body=body_preview)
                        if code_info:
                            verification_code = code_info["code"]
                    except Exception as e:
                        logger.warning(f"Failed to detect verification code: {e}")
                    
                    # 格式化日期
                    date_str = email.get("receivedDateTime", "")
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = date_obj.isoformat()
                    except Exception:
                        formatted_date = datetime.now().isoformat()
                    
                    email_item = EmailItem(
                        message_id=email.get("id"),
                        folder=folder_name,
                        subject=subject,
                        from_email=from_email,
                        date=formatted_date,
                        is_read=email.get("isRead", False),
                        has_attachments=email.get("hasAttachments", False),
                        sender_initial=sender_initial,
                        verification_code=verification_code,
                        body_preview=email.get("bodyPreview", "")
                    )
                    all_emails.append(email_item)
        
        # 排序
        reverse = (sort_order == "desc")
        if sort_by == "date":
            # 使用datetime对象进行日期排序，确保准确性
            def get_date_key(email_item):
                try:
                    return datetime.fromisoformat(email_item.date.replace('Z', '+00:00'))
                except:
                    return datetime.min
            all_emails.sort(key=get_date_key, reverse=reverse)
        elif sort_by == "subject":
            all_emails.sort(key=lambda x: x.subject, reverse=reverse)
        elif sort_by == "from_email":
            all_emails.sort(key=lambda x: x.from_email, reverse=reverse)
        
        # 分页
        total = len(all_emails)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_emails = all_emails[start_idx:end_idx]
        
        logger.debug(f"Fetched {len(paginated_emails)} emails via Graph API for {credentials.email}")
        return paginated_emails, total
        
    except httpx.ConnectError as e:
        error_msg = f"Network connection error: Unable to connect to Microsoft Graph API. Please check your network connection."
        logger.error(f"Connection error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=503, detail=error_msg)
    except httpx.TimeoutException as e:
        error_msg = f"Request timeout: The request to Microsoft Graph API took too long. Please try again later."
        logger.error(f"Timeout error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.HTTPStatusError as e:
        # 401 错误应该已经在循环中处理过了，如果还是失败，记录错误
        if e.response.status_code == 401:
            logger.error(
                f"401 Unauthorized error for {credentials.email} after token refresh attempt. "
                f"Response: {e.response.text[:200]}"
            )
            raise HTTPException(
                status_code=401, 
                detail="Authentication failed. Please check your account credentials."
            )
        
        logger.error(f"HTTP error fetching emails via Graph API for {credentials.email}: Status {e.response.status_code}, Response: {e.response.text[:200]}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails via Graph API: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"Error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails via Graph API: {str(e)}")


async def list_emails_graph2(
    credentials: AccountCredentials,
    folder: str,
    page: int,
    page_size: int,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> tuple[List[EmailItem], int]:
    """
    使用 Graph API 获取邮件列表（新版本，使用 $count=true 获取总数）
    参考 list_emails_with_body_graph 的实现
    
    Args:
        credentials: 账户凭证
        folder: 文件夹名称 ('inbox', 'junk', 'all')
        page: 页码
        page_size: 每页大小
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间 (ISO8601)
        end_time: 结束时间 (ISO8601)
        
    Returns:
        tuple: (邮件列表, 总数)
    """
    access_token = await get_graph_access_token(credentials)
    
    # 映射文件夹名称
    folder_map = {
        "inbox": "inbox",
        "junk": "junkemail",
        "all": None
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "ConsistencyLevel": "eventual"  # 使用 $count=true 时需要此 header
    }
    
    # 确定要查询的URL和文件夹
    # 如果不指定folder（即folder == "all"），使用 /me/messages 而不是分别请求inbox和junkemail
    if folder == "all":
        url = f"{GRAPH_API_BASE_URL}/me/messages"
        folder_name = None  # 用于后续处理，表示所有文件夹
    else:
        folder_name = folder_map.get(folder, "inbox")
        url = f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages"
    
    try:
        timeout = httpx.Timeout(60.0, connect=30.0)  # 总超时60秒，连接超时30秒
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 构建查询参数
            # 计算分页参数
            skip = (page - 1) * page_size
            top = page_size
            
            params = {
                "$top": top,
                "$skip": skip,
                "$count": "true",  # 添加 $count=true 获取总数
                "$orderby": "receivedDateTime desc",  # 按接收时间降序排序
                "$select": "id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview"
            }
            
            # 添加过滤条件
            filters = []
            if sender_search:
                filters.append(f"contains(from/emailAddress/address, '{sender_search}')")
            if subject_search:
                filters.append(f"contains(subject, '{subject_search}')")
            if start_time:
                filters.append(f"receivedDateTime ge {start_time}")
            if end_time:
                filters.append(f"receivedDateTime le {end_time}")
            
            if filters:
                params["$filter"] = " and ".join(filters)
            
            # 添加重试机制
            max_retries = 2
            token_refreshed = False
            response = None
            for attempt in range(max_retries + 1):
                try:
                    response = await client.get(url, headers=headers, params=params)
                    # 处理 401 未授权错误
                    if response.status_code == 401:
                        if not token_refreshed:
                            logger.warning(
                                f"Received 401 Unauthorized for {credentials.email}, "
                                f"clearing cache and refreshing token..."
                            )
                            from oauth_service import clear_cached_access_token
                            await clear_cached_access_token(credentials.email)
                            access_token = await get_graph_access_token(credentials)
                            headers["Authorization"] = f"Bearer {access_token}"
                            token_refreshed = True
                            continue
                    response.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2
                        logger.warning(
                            f"Network error fetching emails for {credentials.email} "
                            f"(attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            
            if response is None:
                raise httpx.RequestError("Failed to get response after retries")
            
            data = response.json()
            emails = data.get("value", [])
            
            # 从响应中获取总数（使用 $count=true 时返回 @odata.count）
            total_count = data.get("@odata.count")
            if total_count is None:
                # 如果没有 @odata.count，尝试从其他字段获取，或者使用当前返回的数量
                # 注意：如果没有 $count=true 或服务器不支持，可能需要回退到其他方法
                logger.warning(f"@odata.count not found in response for {credentials.email}, using fallback")
                total_count = len(emails)  # 回退方案：使用当前页的数量
            
            # 转换为 EmailItem 格式
            email_items = []
            for email in emails:
                from_data = email.get("from", {}).get("emailAddress", {})
                from_email = from_data.get("address", "(Unknown Sender)")
                
                # 提取发件人首字母
                sender_initial = "?"
                email_match = re.search(r"([a-zA-Z])", from_email)
                if email_match:
                    sender_initial = email_match.group(1).upper()
                
                subject = email.get("subject", "(No Subject)")
                body_preview = email.get("bodyPreview", "")
                
                # 检测验证码（只从 body_plain 中检测）
                verification_code = None
                try:
                    # 使用 bodyPreview 作为 body_plain 的替代
                    code_info = detect_verification_code(subject="", body=body_preview)
                    if code_info:
                        verification_code = code_info["code"]
                except Exception as e:
                    logger.warning(f"Failed to detect verification code: {e}")
                
                # 格式化日期
                date_str = email.get("receivedDateTime", "")
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.isoformat()
                except Exception:
                    formatted_date = datetime.now().isoformat()
                
                # 获取邮件所在的文件夹
                email_folder = folder_name
                if folder_name is None:
                    # 从 /me/messages 获取的邮件，尝试从 parentFolderId 或其他字段获取文件夹信息
                    # 如果没有，默认为 "inbox"
                    parent_folder_id = email.get("parentFolderId", "")
                    # 尝试从 parentFolderId 推断文件夹名称
                    if "inbox" in parent_folder_id.lower():
                        email_folder = "inbox"
                    elif "junk" in parent_folder_id.lower() or "spam" in parent_folder_id.lower():
                        email_folder = "junkemail"
                    else:
                        email_folder = "inbox"  # 默认
                
                email_item = EmailItem(
                    message_id=email.get("id"),
                    folder=email_folder or "inbox",  # 如果无法确定，默认为 inbox
                    subject=subject,
                    from_email=from_email,
                    date=formatted_date,
                    is_read=email.get("isRead", False),
                    has_attachments=email.get("hasAttachments", False),
                    sender_initial=sender_initial,
                    verification_code=verification_code,
                    body_preview=email.get("bodyPreview", "")
                )
                email_items.append(email_item)
            
            # 如果需要客户端排序（当使用 $filter 时，服务器端排序可能不准确）
            # 这里我们依赖服务器端排序，因为使用了 $orderby
            
            logger.info(
                f"Fetched {len(email_items)} emails via Graph API for {credentials.email}, "
                f"total count: {total_count}"
            )
            return email_items, total_count
            
    except httpx.ConnectError as e:
        error_msg = f"Network connection error: Unable to connect to Microsoft Graph API. Please check your network connection."
        logger.error(f"Connection error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=503, detail=error_msg)
    except httpx.TimeoutException as e:
        error_msg = f"Request timeout: The request to Microsoft Graph API took too long. Please try again later."
        logger.error(f"Timeout error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.error(
                f"401 Unauthorized error for {credentials.email} after token refresh attempt. "
                f"Response: {e.response.text[:200]}"
            )
            raise HTTPException(
                status_code=401, 
                detail="Authentication failed. Please check your account credentials."
            )
        logger.error(f"HTTP error fetching emails via Graph API for {credentials.email}: Status {e.response.status_code}, Response: {e.response.text[:200]}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails via Graph API: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"Error fetching emails via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails via Graph API: {str(e)}")


async def list_emails_with_body_graph(
    credentials: AccountCredentials,
    folder: str,
    max_count: int,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    使用 Graph API 直接获取包含body的邮件详情列表（用于分享页）
    
    Args:
        credentials: 账户凭证
        folder: 文件夹名称 ('inbox', 'junk', 'all')
        max_count: 最多返回邮件数量
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间 (ISO8601)
        end_time: 结束时间 (ISO8601)
        
    Returns:
        List[Dict]: 包含完整body的邮件详情列表
    """
    access_token = await get_graph_access_token(credentials)
    
    # 映射文件夹名称
    folder_map = {
        "inbox": "inbox",
        "junk": "junkemail",
        "all": None
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_emails = []
    
    # 确定要查询的URL和文件夹
    # 如果不指定folder（即folder == "all"），使用 /me/messages 而不是分别请求inbox和junkemail
    if folder == "all":
        url = f"{GRAPH_API_BASE_URL}/me/messages"
        folder_name = None  # 用于后续处理，表示所有文件夹
    else:
        folder_name = folder_map.get(folder, "inbox")
        url = f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages"
    
    try:
        timeout = httpx.Timeout(60.0, connect=30.0)  # 总超时60秒，连接超时30秒
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 构建查询参数，包含body字段
            # 取件数设置为入参的两倍，以便过滤后仍有足够的数据
            params = {
                "$top": max_count * 2,  # 取两倍数量，过滤后再截取
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,toRecipients,receivedDateTime,isRead,hasAttachments,body,bodyPreview"
            }
            
            # 不再使用 $filter，改为代码过滤
                
            # 添加重试机制
            max_retries = 2
            last_error = None
            token_refreshed = False
            response = None
            for attempt in range(max_retries + 1):
                try:
                    response = await client.get(url, headers=headers, params=params)
                    # 处理 401 未授权错误
                    if response.status_code == 401:
                        if not token_refreshed:
                            logger.warning(
                                f"Received 401 Unauthorized for {credentials.email}, "
                                f"clearing cache and refreshing token..."
                            )
                            from oauth_service import clear_cached_access_token
                            clear_cached_access_token(credentials.email)
                            access_token = await get_graph_access_token(credentials)
                            headers["Authorization"] = f"Bearer {access_token}"
                            token_refreshed = True
                            continue
                    response.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    last_error = e
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2
                        logger.warning(
                            f"Network error fetching emails with body for {credentials.email} "
                            f"(attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            
            if response is None:
                logger.warning(f"No response received for {credentials.email}")
                return []
            
            data = response.json()
            emails = data.get("value", [])
            
            # 代码过滤：在取件后进行过滤
            filtered_emails = []
            for email in emails:
                # 提取基本信息用于过滤
                from_data = email.get("from", {}).get("emailAddress", {})
                from_email = from_data.get("address", "")
                subject = email.get("subject", "")
                date_str = email.get("receivedDateTime", "")
                
                # 发件人过滤
                if sender_search:
                    if sender_search.lower() not in from_email.lower():
                        continue
                
                # 主题过滤
                if subject_search:
                    if subject_search.lower() not in subject.lower():
                        continue
                
                # 时间过滤
                if start_time or end_time:
                    try:
                        email_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        if start_time:
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            if email_date < start_dt:
                                continue
                        if end_time:
                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            if email_date > end_dt:
                                continue
                    except Exception as e:
                        logger.warning(f"Error parsing date for filtering: {e}")
                        # 如果日期解析失败，跳过时间过滤
                
                filtered_emails.append(email)
            
            # 处理每封过滤后的邮件
            for email in filtered_emails:
                # 提取基本信息（过滤时已提取，这里重新提取以确保完整性）
                from_data = email.get("from", {}).get("emailAddress", {})
                from_email = from_data.get("address", "(Unknown Sender)")
                
                to_recipients = email.get("toRecipients", [])
                to_email = ", ".join([r.get("emailAddress", {}).get("address", "") for r in to_recipients])
                
                subject = email.get("subject", "(No Subject)")
                
                # 获取邮件正文
                body_data = email.get("body", {})
                body_content = body_data.get("content", "")
                body_type = body_data.get("contentType", "text")
                
                body_plain = None
                body_html = None
                
                if body_type.lower() == "html":
                    body_html = body_content
                    body_plain = email.get("bodyPreview", "")
                else:
                    body_plain = body_content
                
                # 格式化日期
                date_str = email.get("receivedDateTime", "")
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.isoformat()
                except Exception:
                    formatted_date = datetime.now().isoformat()
                
                # 检测验证码（只从 body_plain 中检测）
                verification_code = None
                try:
                    # 只使用 body_plain，不使用 body_html
                    code_info = detect_verification_code(subject="", body=body_plain or "")
                    if code_info:
                        verification_code = code_info["code"]
                except Exception as e:
                    logger.warning(f"Failed to detect verification code: {e}")
                
                # 提取发件人首字母
                sender_initial = "?"
                if from_email:
                    match = re.search(r'([a-zA-Z])', from_email)
                    if match:
                        sender_initial = match.group(1).upper()
                    
                # 获取邮件所在的文件夹（如果是从 /me/messages 获取的）
                email_folder = folder_name
                if folder_name is None:
                    # 从 /me/messages 获取的邮件，尝试从 parentFolderId 或其他字段获取文件夹信息
                    # 如果没有，默认为 "all" 表示所有文件夹
                    email_folder = email.get("parentFolderId") or "all"
                
                email_dict = {
                    'message_id': email.get("id"),
                    'folder': email_folder,
                    'subject': subject,
                    'from_email': from_email,
                    'to_email': to_email,
                    'date': formatted_date,
                    'is_read': email.get("isRead", False),
                    'has_attachments': email.get("hasAttachments", False),
                    'sender_initial': sender_initial,
                    'verification_code': verification_code,
                    'body_preview': email.get("bodyPreview", ""),
                    'body_plain': body_plain,
                    'body_html': body_html,
                }
                all_emails.append(email_dict)
                
                # 如果已经达到所需数量，提前退出
                if len(all_emails) >= max_count:
                    break
        
        # 排序
        reverse = (sort_order == "desc")
        if sort_by == "date":
            def get_date_key(email_dict):
                try:
                    return datetime.fromisoformat(email_dict['date'].replace('Z', '+00:00'))
                except:
                    return datetime.min
            all_emails.sort(key=get_date_key, reverse=reverse)
        elif sort_by == "subject":
            all_emails.sort(key=lambda x: x['subject'], reverse=reverse)
        elif sort_by == "from_email":
            all_emails.sort(key=lambda x: x['from_email'], reverse=reverse)
        
        # 限制返回数量
        all_emails = all_emails[:max_count]
        
        logger.info(f"Fetched {len(all_emails)} emails with body via Graph API for {credentials.email}")
        return all_emails
        
    except httpx.ConnectError as e:
        error_msg = f"Network connection error: Unable to connect to Microsoft Graph API. Please check your network connection."
        logger.error(f"Connection error fetching emails with body via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=503, detail=error_msg)
    except httpx.TimeoutException as e:
        error_msg = f"Request timeout: The request to Microsoft Graph API took too long. Please try again later."
        logger.error(f"Timeout error fetching emails with body via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.error(
                f"401 Unauthorized error for {credentials.email} after token refresh attempt. "
                f"Response: {e.response.text[:200]}"
            )
            raise HTTPException(
                status_code=401, 
                detail="Authentication failed. Please check your account credentials."
            )
        logger.error(f"HTTP error fetching emails with body via Graph API for {credentials.email}: Status {e.response.status_code}, Response: {e.response.text[:200]}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails with body via Graph API: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"Error fetching emails with body via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails with body via Graph API: {str(e)}")


async def get_email_details_graph(
    credentials: AccountCredentials,
    message_id: str
) -> EmailDetailsResponse:
    """
    使用 Graph API 获取邮件详情
    
    Args:
        credentials: 账户凭证
        message_id: 邮件ID
        
    Returns:
        EmailDetailsResponse: 邮件详情
    """
    # 优先从内存LRU缓存获取
    cached_detail = cache_service.get_cached_email_detail(credentials.email, message_id)
    if cached_detail:
        logger.info(f"Returning cached email detail from LRU cache for {message_id}")
        return EmailDetailsResponse(**cached_detail)
    
    # 从 SQLite 缓存获取
    try:
        cached_detail = db.get_cached_email_detail(credentials.email, message_id)
        if cached_detail:
            logger.info(f"Returning cached email detail from database for {message_id}")
            # 缓存到内存LRU缓存
            cache_service.set_cached_email_detail(credentials.email, message_id, cached_detail)
            return EmailDetailsResponse(**cached_detail)
    except Exception as e:
        logger.warning(f"Failed to load email detail from cache: {e}")
    
    access_token = await get_graph_access_token(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 增加超时时间，并添加重试机制
        timeout = httpx.Timeout(60.0, connect=30.0)  # 总超时60秒，连接超时30秒
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{GRAPH_API_BASE_URL}/me/messages/{message_id}"
            params = {
                "$select": "id,subject,from,toRecipients,receivedDateTime,body,bodyPreview"
            }
            
            # 添加重试机制
            max_retries = 2
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    break  # 成功，退出重试循环
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    last_error = e
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒
                        logger.warning(
                            f"Network error fetching email detail for {message_id} (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise  # 最后一次尝试失败，抛出异常
            
            email = response.json()
            
            # 提取信息
            from_data = email.get("from", {}).get("emailAddress", {})
            from_email = from_data.get("address", "(Unknown Sender)")
            
            to_recipients = email.get("toRecipients", [])
            to_email = ", ".join([r.get("emailAddress", {}).get("address", "") for r in to_recipients])
            
            subject = email.get("subject", "(No Subject)")
            
            # 获取邮件正文
            body_data = email.get("body", {})
            body_content = body_data.get("content", "")
            body_type = body_data.get("contentType", "text")
            
            body_plain = None
            body_html = None
            
            if body_type.lower() == "html":
                body_html = body_content
                body_plain = email.get("bodyPreview", "")
            else:
                body_plain = body_content
            
            # 格式化日期
            date_str = email.get("receivedDateTime", "")
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = date_obj.isoformat()
            except Exception:
                formatted_date = datetime.now().isoformat()
            
            # 检测验证码（只从 body_plain 中检测）
            verification_code = None
            try:
                # 只使用 body_plain，不使用 body_html
                code_info = detect_verification_code(subject="", body=body_plain or "")
                if code_info:
                    verification_code = code_info["code"]
                    logger.info(f"Detected verification code in email {message_id}: {verification_code}")
            except Exception as e:
                logger.warning(f"Failed to detect verification code: {e}")
            
            email_detail_response = EmailDetailsResponse(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                date=formatted_date,
                body_plain=body_plain,
                body_html=body_html,
                verification_code=verification_code
            )
            
            # 缓存到 SQLite
            try:
                db.cache_email_detail(credentials.email, email_detail_response.dict())
                logger.info(f"Cached email detail to database for {message_id}")
            except Exception as e:
                logger.warning(f"Failed to cache email detail to database: {e}")
            
            # 缓存到内存LRU缓存
            try:
                cache_service.set_cached_email_detail(
                    credentials.email, 
                    message_id, 
                    email_detail_response.dict()
                )
            except Exception as e:
                logger.warning(f"Failed to cache email detail to LRU cache: {e}")
            
            return email_detail_response
            
    except httpx.ConnectError as e:
        error_msg = f"Network connection error: Unable to connect to Microsoft Graph API. Please check your network connection."
        logger.error(f"Connection error fetching email details via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=503, detail=error_msg)
    except httpx.TimeoutException as e:
        error_msg = f"Request timeout: The request to Microsoft Graph API took too long. Please try again later."
        logger.error(f"Timeout error fetching email details via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Email not found")
        logger.error(f"HTTP error fetching email details via Graph API for {credentials.email}: Status {e.response.status_code}, Response: {e.response.text[:200]}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email details via Graph API: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"Error fetching email details via Graph API for {credentials.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email details via Graph API: {str(e)}")


async def delete_email_graph(
    credentials: AccountCredentials,
    message_id: str
) -> bool:
    """
    使用 Graph API 删除邮件
    
    Args:
        credentials: 账户凭证
        message_id: 邮件ID
        
    Returns:
        bool: 是否删除成功
    """
    access_token = await get_graph_access_token(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{GRAPH_API_BASE_URL}/me/messages/{message_id}"
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully deleted email {message_id} via Graph API for {credentials.email}")
            
            # 删除缓存
            try:
                import database as db
                db.delete_email_from_cache(credentials.email, message_id)
                
                # 清除内存缓存
                cache_service.clear_email_cache(credentials.email)
            except Exception as e:
                logger.warning(f"Failed to delete email from cache: {e}")
            
            return True
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Email not found")
        logger.error(f"HTTP error deleting email via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete email via Graph API")
    except Exception as e:
        logger.error(f"Error deleting email via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete email via Graph API")


async def delete_emails_batch_graph(
    credentials: AccountCredentials,
    folder: str = "inbox"
) -> Dict[str, Any]:
    """
    使用 Graph API 批量删除邮件（使用 batch 请求）
    参考 graph_clear_demo.py 的实现
    
    Args:
        credentials: 账户凭证
        folder: 文件夹名称 ('inbox', 'junk', 'all')
        
    Returns:
        dict: {
            'success_count': int,  # 成功删除的邮件数
            'fail_count': int,     # 失败的邮件数
            'total_count': int     # 总邮件数
        }
    """
    access_token = await get_graph_access_token(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 映射文件夹名称
    folder_map = {
        "inbox": "inbox",
        "junk": "junkemail",
        "all": None
    }
    
    # 确定要查询的URL
    if folder == "all":
        # 使用 /me/messages 获取所有邮件
        list_url = f"{GRAPH_API_BASE_URL}/me/messages"
    else:
        folder_name = folder_map.get(folder, "inbox")
        list_url = f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. 获取邮件列表（仅获取ID）
            all_message_ids = []
            url = list_url
            
            # 处理分页，获取所有邮件ID
            while url:
                params = {
                    "$select": "id",
                    "$top": 100  # 每次最多获取100封
                }
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                messages = data.get('value', [])
                
                for msg in messages:
                    all_message_ids.append(msg['id'])
                
                # 检查是否有下一页
                next_link = data.get('@odata.nextLink')
                if next_link:
                    # @odata.nextLink 通常是完整的 URL，直接使用
                    url = next_link
                else:
                    url = None
            
            if not all_message_ids:
                logger.info(f"No emails to delete in folder {folder} for {credentials.email}")
                return {
                    'success_count': 0,
                    'fail_count': 0,
                    'total_count': 0
                }
            
            logger.info(f"Found {len(all_message_ids)} emails to delete in folder {folder} for {credentials.email}")
            
            # 2. 分批删除（Graph API 限制每次 batch 最多 20 个请求）
            batch_size = 20
            success_count = 0
            fail_count = 0
            
            for i in range(0, len(all_message_ids), batch_size):
                batch_chunk = all_message_ids[i:i + batch_size]
                
                batch_payload = {
                    "requests": []
                }
                
                # 构建 batch 请求体
                for index, message_id in enumerate(batch_chunk):
                    batch_payload["requests"].append({
                        "id": str(index),  # 请求的序号，不是邮件 ID
                        "method": "DELETE",
                        "url": f"/me/messages/{message_id}"
                    })
                
                # 发送批量删除请求
                batch_url = f"{GRAPH_API_BASE_URL}/$batch"
                del_resp = await client.post(batch_url, headers=headers, json=batch_payload)
                
                if del_resp.status_code == 200:
                    batch_result = del_resp.json()
                    responses = batch_result.get('responses', [])
                    
                    for resp in responses:
                        if resp.get('status') == 204:  # 204 No Content 表示删除成功
                            success_count += 1
                        else:
                            fail_count += 1
                            logger.warning(f"Failed to delete email: {resp}")
                    
                    logger.info(f"Processed batch {i // batch_size + 1}: {len(batch_chunk)} emails")
                else:
                    # 整个批次失败
                    fail_count += len(batch_chunk)
                    logger.error(f"Batch delete failed: {del_resp.status_code}, {del_resp.text[:200]}")
            
            # 清除缓存
            try:
                cache_service.clear_email_cache(credentials.email)
                logger.info(f"Cleared email cache for {credentials.email}")
            except Exception as e:
                logger.warning(f"Failed to clear email cache: {e}")
            
            logger.info(
                f"Batch delete completed for {credentials.email} folder {folder}: "
                f"success={success_count}, failed={fail_count}, total={len(all_message_ids)}"
            )
            
            return {
                'success_count': success_count,
                'fail_count': fail_count,
                'total_count': len(all_message_ids)
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error batch deleting emails via Graph API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch delete emails via Graph API: HTTP {e.response.status_code}")
    except Exception as e:
        logger.exception(f"Error batch deleting emails via Graph API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch delete emails via Graph API: {str(e)}")


async def send_email_graph(
    credentials: AccountCredentials,
    to: str,
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None
) -> str:
    """
    使用 Graph API 发送邮件
    
    Args:
        credentials: 账户凭证
        to: 收件人邮箱地址
        subject: 邮件主题
        body_text: 纯文本正文
        body_html: HTML正文
        
    Returns:
        str: 邮件ID（如果成功）
    """
    access_token = await get_graph_access_token(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 构建邮件内容
    body_content = body_html if body_html else body_text
    body_type = "HTML" if body_html else "Text"
    
    if not body_content:
        raise HTTPException(status_code=400, detail="Email body is required (body_text or body_html)")
    
    message = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": body_type,
                "content": body_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{GRAPH_API_BASE_URL}/me/sendMail"
            response = await client.post(url, headers=headers, json=message)
            response.raise_for_status()
            
            logger.info(f"Successfully sent email via Graph API from {credentials.email} to {to}")
            return "sent"  # Graph API sendMail 不返回 message ID
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending email via Graph API: {e}")
        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
        raise HTTPException(status_code=500, detail=f"Failed to send email via Graph API: {error_detail}")
    except Exception as e:
        logger.error(f"Error sending email via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email via Graph API")

