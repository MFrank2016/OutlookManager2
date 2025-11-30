"""
Microsoft Graph API 服务模块

提供基于 Graph API 的邮件操作功能，包括列表、详情、删除和发送
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx
from fastapi import HTTPException

from config import GRAPH_API_BASE_URL, GRAPH_API_SCOPE, TOKEN_URL
from models import AccountCredentials, EmailItem, EmailDetailsResponse
from verification_code_detector import detect_verification_code

# 获取日志记录器
logger = logging.getLogger(__name__)


async def get_graph_access_token(credentials: AccountCredentials) -> str:
    """
    获取 Graph API 访问令牌
    
    Args:
        credentials: 账户凭证信息
        
    Returns:
        str: Graph API 访问令牌
        
    Raises:
        HTTPException: 令牌获取失败
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
            
            if not access_token:
                logger.error(f"No access token in Graph API response for {credentials.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Failed to obtain Graph API access token"
                )
            
            logger.info(f"Successfully obtained Graph API access token for {credentials.email}")
            return access_token
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error getting Graph API token for {credentials.email}: {e}")
        raise HTTPException(status_code=401, detail="Graph API authentication failed")
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
            
            # 检查是否包含 Mail.ReadWrite 权限
            has_mail_permission = "Mail.ReadWrite" in scope or "Mail.Read" in scope
            
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
    sort_order: str = "desc"
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            for folder_name in folders_to_query:
                # 构建查询参数
                params = {
                    "$top": 999,  # 获取足够多的邮件用于分页和搜索
                    "$orderby": "receivedDateTime desc",
                    "$select": "id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview"
                }
                
                # 添加过滤条件
                filters = []
                if sender_search:
                    filters.append(f"contains(from/emailAddress/address, '{sender_search}')")
                if subject_search:
                    filters.append(f"contains(subject, '{subject_search}')")
                
                if filters:
                    params["$filter"] = " and ".join(filters)
                
                url = f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages"
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
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
                    
                    # 检测验证码
                    verification_code = None
                    try:
                        code_info = detect_verification_code(subject=subject, body="")
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
            all_emails.sort(key=lambda x: x.date, reverse=reverse)
        elif sort_by == "subject":
            all_emails.sort(key=lambda x: x.subject, reverse=reverse)
        elif sort_by == "from_email":
            all_emails.sort(key=lambda x: x.from_email, reverse=reverse)
        
        # 分页
        total = len(all_emails)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_emails = all_emails[start_idx:end_idx]
        
        logger.info(f"Fetched {len(paginated_emails)} emails via Graph API for {credentials.email}")
        logger.info(f"Paginated emails: {paginated_emails}")
        return paginated_emails, total
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching emails via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch emails via Graph API")
    except Exception as e:
        logger.error(f"Error fetching emails via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch emails via Graph API")


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
    access_token = await get_graph_access_token(credentials)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{GRAPH_API_BASE_URL}/me/messages/{message_id}"
            params = {
                "$select": "id,subject,from,toRecipients,receivedDateTime,body,bodyPreview"
            }
            
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
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
            
            # 检测验证码
            verification_code = None
            try:
                body_for_detection = body_plain or body_html or ""
                code_info = detect_verification_code(subject=subject, body=body_for_detection)
                if code_info:
                    verification_code = code_info["code"]
                    logger.info(f"Detected verification code in email {message_id}: {verification_code}")
            except Exception as e:
                logger.warning(f"Failed to detect verification code: {e}")
            
            return EmailDetailsResponse(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                date=formatted_date,
                body_plain=body_plain,
                body_html=body_html,
                verification_code=verification_code
            )
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Email not found")
        logger.error(f"HTTP error fetching email details via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch email details via Graph API")
    except Exception as e:
        logger.error(f"Error fetching email details via Graph API: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch email details via Graph API")


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
                from cache_service import clear_email_cache
                clear_email_cache(credentials.email)
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

