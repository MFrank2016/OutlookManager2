"""
邮件管理路由模块

处理邮件查询相关的API端点
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

import auth
from account_service import get_account_credentials
from email_service import get_email_details, list_emails
from models import DualViewEmailResponse, EmailDetailsResponse, EmailListResponse

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/emails", tags=["邮件管理"])


@router.get("/{email_id}", response_model=EmailListResponse)
async def get_emails(
    email_id: str,
    folder: str = Query("all", regex="^(inbox|junk|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    refresh: bool = Query(False, description="强制刷新缓存"),
    sender_search: Optional[str] = Query(None, description="发件人模糊搜索"),
    subject_search: Optional[str] = Query(None, description="主题模糊搜索"),
    sort_by: str = Query("date", description="排序字段（date/subject/from_email）"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    admin: dict = Depends(auth.get_current_admin),
):
    """获取邮件列表（支持搜索、排序、SQLite缓存）"""
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
    admin: dict = Depends(auth.get_current_admin),
):
    """获取双栏视图邮件（收件箱和垃圾箱）"""
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
    email_id: str, message_id: str, admin: dict = Depends(auth.get_current_admin)
):
    """获取邮件详细内容"""
    credentials = await get_account_credentials(email_id)
    return await get_email_details(credentials, message_id)

