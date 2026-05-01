from __future__ import annotations

from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

import auth
from account_service import get_account_credentials
from microsoft_access.mail_gateway import default_mail_gateway
from models import (
    AccountCredentials,
    BatchDeleteEmailsResponse,
    DeleteEmailResponse,
    EmailDetailsResponse,
    EmailListResponse,
    SendEmailRequest,
    SendEmailResponse,
    StrategyMode,
)
from permissions import Permission


router = APIRouter(prefix="/accounts", tags=["API v2 / 邮件"])


async def _default_account_loader(email: str) -> AccountCredentials:
    return await get_account_credentials(email)


def get_account_loader(request: Request) -> Callable[[str], object]:
    return getattr(request.app.state, "v2_account_loader", None) or _default_account_loader


def get_mail_gateway(request: Request):
    return getattr(request.app.state, "v2_mail_gateway", None) or default_mail_gateway


@router.get("/{email}/messages", response_model=EmailListResponse)
async def list_messages(
    email: str,
    folder: str = Query("all", pattern="^(inbox|junk|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    skip_cache: bool = Query(False),
    sender_search: Optional[str] = Query(None),
    subject_search: Optional[str] = Query(None),
    sort_by: str = Query("date"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    user: dict = Depends(auth.get_current_user),
    account_loader=Depends(get_account_loader),
    mail_gateway=Depends(get_mail_gateway),
):
    if not auth.check_account_access(user, email):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    auth.require_permission(user, Permission.VIEW_EMAILS)

    credentials = await account_loader(email)
    return await mail_gateway.list_messages(
        credentials,
        folder=folder,
        page=page,
        page_size=page_size,
        strategy_mode=strategy_mode or credentials.strategy_mode,
        override_provider=override_provider,
        skip_cache=skip_cache,
        sender_search=sender_search,
        subject_search=subject_search,
        sort_by=sort_by,
        sort_order=sort_order,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/{email}/messages/{message_id}", response_model=EmailDetailsResponse)
async def get_message_detail(
    email: str,
    message_id: str,
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    skip_cache: bool = Query(False),
    user: dict = Depends(auth.get_current_user),
    account_loader=Depends(get_account_loader),
    mail_gateway=Depends(get_mail_gateway),
):
    if not auth.check_account_access(user, email):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    auth.require_permission(user, Permission.VIEW_EMAILS)

    credentials = await account_loader(email)
    return await mail_gateway.get_message_detail(
        credentials,
        message_id,
        strategy_mode=strategy_mode or credentials.strategy_mode,
        override_provider=override_provider,
        skip_cache=skip_cache,
    )


@router.delete("/{email}/messages/{message_id}", response_model=DeleteEmailResponse)
async def delete_message(
    email: str,
    message_id: str,
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    user: dict = Depends(auth.get_current_user),
    account_loader=Depends(get_account_loader),
    mail_gateway=Depends(get_mail_gateway),
):
    if not auth.check_account_access(user, email):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    auth.require_permission(user, Permission.DELETE_EMAILS)

    credentials = await account_loader(email)
    success = await mail_gateway.delete_message(
        credentials,
        message_id,
        strategy_mode=strategy_mode or credentials.strategy_mode,
        override_provider=override_provider,
    )
    return DeleteEmailResponse(
        success=success,
        message="Email deleted successfully" if success else "Failed to delete email",
        message_id=message_id,
    )


@router.delete("/{email}/messages", response_model=BatchDeleteEmailsResponse)
async def delete_messages_batch(
    email: str,
    folder: str = Query("inbox", pattern="^(inbox|junk|all)$"),
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    user: dict = Depends(auth.get_current_user),
    account_loader=Depends(get_account_loader),
    mail_gateway=Depends(get_mail_gateway),
):
    if not auth.check_account_access(user, email):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    auth.require_permission(user, Permission.DELETE_EMAILS)

    credentials = await account_loader(email)
    result = await mail_gateway.delete_messages_batch(
        credentials,
        folder=folder,
        strategy_mode=strategy_mode or credentials.strategy_mode,
        override_provider=override_provider,
    )
    return BatchDeleteEmailsResponse(
        success=True,
        message=f"Successfully deleted {result['success_count']} emails, {result['fail_count']} failed",
        success_count=result["success_count"],
        fail_count=result["fail_count"],
        total_count=result["total_count"],
    )


@router.post("/{email}/messages/send", response_model=SendEmailResponse)
async def send_message(
    email: str,
    request: SendEmailRequest,
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    user: dict = Depends(auth.get_current_user),
    account_loader=Depends(get_account_loader),
    mail_gateway=Depends(get_mail_gateway),
):
    if not auth.check_account_access(user, email):
        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    auth.require_permission(user, Permission.SEND_EMAILS)

    credentials = await account_loader(email)
    message_id = await mail_gateway.send_message(
        credentials,
        to=request.to,
        subject=request.subject,
        body_text=request.body_text,
        body_html=request.body_html,
        strategy_mode=strategy_mode or credentials.strategy_mode,
        override_provider=override_provider,
    )
    return SendEmailResponse(
        success=True,
        message="Email sent successfully",
        message_id=message_id,
    )
