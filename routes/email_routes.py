"""
邮件管理路由模块

处理邮件查询相关的API端点
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

import auth
from account_service import get_account_credentials
from email_service import get_email_details, list_emails, delete_email, delete_emails_batch, send_email
from models import (
    DualViewEmailResponse,
    EmailDetailsResponse,
    EmailListResponse,
    SendEmailRequest,
    SendEmailResponse,
    DeleteEmailResponse,
    BatchDeleteEmailsResponse
)
from permissions import Permission
from fastapi import HTTPException

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/emails", tags=["邮件管理"])


@router.get("/{email_id}", response_model=EmailListResponse)
async def get_emails(
    email_id: str,
    folder: str = Query("all", regex="^(inbox|junk|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    refresh: bool = Query(False, description="强制刷新缓存"),
    sender_search: Optional[str] = Query(None, description="发件人模糊搜索"),
    subject_search: Optional[str] = Query(None, description="主题模糊搜索"),
    sort_by: str = Query("date", description="排序字段（date/subject/from_email）"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    user: dict = Depends(auth.get_current_user),
):
    """获取邮件列表（支持搜索、排序、SQLite缓存，根据用户权限控制）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查查看邮件权限
    auth.require_permission(user, Permission.VIEW_EMAILS)
    
    credentials = await get_account_credentials(email_id)
    return await list_emails(
        credentials, folder, page, page_size, refresh,
        sender_search, subject_search, sort_by, sort_order
    )


@router.get("/{email_id}/dual-view")
async def get_dual_view_emails(
    email_id: str,
    inbox_page: int = Query(1, ge=1),
    junk_page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(auth.get_current_user),
):
    """获取双栏视图邮件（收件箱和垃圾箱，根据用户权限控制）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查查看邮件权限
    auth.require_permission(user, Permission.VIEW_EMAILS)
    
    credentials = await get_account_credentials(email_id)

    # 并行获取收件箱和垃圾箱邮件
    inbox_response = await list_emails(credentials, "inbox", inbox_page, page_size)
    junk_response = await list_emails(credentials, "junk", junk_page, page_size)

    return DualViewEmailResponse(
        email_id=email_id,
        inbox_emails=inbox_response.emails,
        junk_emails=junk_response.emails,
        inbox_total=inbox_response.total_emails,
        junk_total=junk_response.total_emails,
    )


@router.get("/{email_id}/{message_id}", response_model=EmailDetailsResponse)
async def get_email_detail(
    email_id: str, message_id: str, user: dict = Depends(auth.get_current_user)
):
    """获取邮件详细内容（根据用户权限控制）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查查看邮件权限
    auth.require_permission(user, Permission.VIEW_EMAILS)
    
    credentials = await get_account_credentials(email_id)
    return await get_email_details(credentials, message_id)


@router.delete("/{email_id}/{message_id}", response_model=DeleteEmailResponse)
async def delete_email_route(
    email_id: str, message_id: str, user: dict = Depends(auth.get_current_user)
):
    """删除指定邮件（需要删除邮件权限）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查删除邮件权限
    auth.require_permission(user, Permission.DELETE_EMAILS)
    
    credentials = await get_account_credentials(email_id)
    success = await delete_email(credentials, message_id)
    
    return DeleteEmailResponse(
        success=success,
        message="Email deleted successfully" if success else "Failed to delete email",
        message_id=message_id
    )


@router.delete("/{email_id}/batch", response_model=BatchDeleteEmailsResponse)
async def delete_emails_batch_route(
    email_id: str,
    folder: str = Query("inbox", regex="^(inbox|junk|all)$", description="要清空的文件夹"),
    user: dict = Depends(auth.get_current_user)
):
    """批量删除邮件（需要删除邮件权限）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查删除邮件权限
    auth.require_permission(user, Permission.DELETE_EMAILS)
    
    credentials = await get_account_credentials(email_id)
    
    try:
        result = await delete_emails_batch(credentials, folder)
        
        return BatchDeleteEmailsResponse(
            success=True,
            message=f"Successfully deleted {result['success_count']} emails, {result['fail_count']} failed",
            success_count=result['success_count'],
            fail_count=result['fail_count'],
            total_count=result['total_count']
        )
    except Exception as e:
        logger.error(f"Error batch deleting emails: {e}")
        return BatchDeleteEmailsResponse(
            success=False,
            message=str(e),
            success_count=0,
            fail_count=0,
            total_count=0
        )


@router.post("/{email_id}/send", response_model=SendEmailResponse)
async def send_email_route(
    email_id: str,
    request: SendEmailRequest,
    user: dict = Depends(auth.get_current_user)
):
    """发送邮件（需要发送邮件权限）"""
    # 检查账户访问权限
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email_id}")
    
    # 检查发送邮件权限
    auth.require_permission(user, Permission.SEND_EMAILS)
    
    credentials = await get_account_credentials(email_id)
    
    try:
        message_id = await send_email(
            credentials,
            request.to,
            request.subject,
            request.body_text,
            request.body_html
        )
        
        return SendEmailResponse(
            success=True,
            message="Email sent successfully",
            message_id=message_id
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return SendEmailResponse(
            success=False,
            message=str(e),
            message_id=None
        )

