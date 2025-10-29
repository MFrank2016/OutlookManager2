"""
邮件管理路由

处理邮件相关的API请求
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases.email import (
    GetEmailDetailUseCase,
    ListEmailsUseCase,
    SearchEmailsUseCase,
)
from src.config.constants import EmailFolder
from src.domain.exceptions import (
    AccountNotFoundException,
    DomainException,
    EmailNotFoundException,
)
from src.domain.repositories.account_repository import IAccountRepository
from src.presentation.api.v1.dependencies import (
    get_account_repository,
    get_current_admin,
    get_get_email_detail_use_case,
    get_list_emails_use_case,
    get_search_emails_use_case,
)
from src.presentation.api.v1.schemas import (
    EmailDetailResponse,
    EmailResponse,
    EmailSearchParams,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get(
    "/{account_id}",
    response_model=PaginatedResponse[EmailResponse],
    summary="获取邮件列表"
)
async def list_emails(
    account_id: UUID,
    folder: EmailFolder = Query(EmailFolder.INBOX, description="邮件文件夹"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=500, description="返回数量"),
    use_case: ListEmailsUseCase = Depends(get_list_emails_use_case),
    account_repository: IAccountRepository = Depends(get_account_repository),
    _admin_id: UUID = Depends(get_current_admin)
):
    """
    获取指定账户的邮件列表
    
    - **account_id**: 账户ID（UUID）
    - **folder**: 邮件文件夹（默认INBOX）
    - **skip**: 跳过数量（用于分页）
    - **limit**: 返回数量（最大500）
    """
    try:
        # 根据account_id获取账户
        account = await account_repository.get_by_id(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {account_id}"
            )
        
        # 计算页码
        page = (skip // limit) + 1
        page_size = limit
        
        # 执行用例
        result = await use_case.execute(
            email=str(account.email),
            folder=folder,
            page=page,
            page_size=page_size
        )
        
        emails = [EmailResponse(**email.__dict__) for email in result.emails]
        
        return PaginatedResponse.create(
            items=emails,
            total=result.total,
            page=result.page,
            page_size=result.page_size
        )
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{account_id}/{message_id}",
    response_model=EmailDetailResponse,
    summary="获取邮件详情"
)
async def get_email_detail(
    account_id: UUID,
    message_id: str,
    use_case: GetEmailDetailUseCase = Depends(get_get_email_detail_use_case),
    account_repository: IAccountRepository = Depends(get_account_repository),
    _admin_id: UUID = Depends(get_current_admin)
):
    """
    获取指定邮件的详细信息
    
    - **account_id**: 账户ID（UUID）
    - **message_id**: 邮件消息ID
    """
    try:
        # 根据account_id获取账户
        account = await account_repository.get_by_id(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {account_id}"
            )
        
        result = await use_case.execute(
            email=str(account.email),
            message_id=message_id
        )
        
        return EmailDetailResponse(**result.__dict__)
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except EmailNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{account_id}/search",
    response_model=PaginatedResponse[EmailResponse],
    summary="搜索邮件"
)
async def search_emails(
    account_id: UUID,
    params: EmailSearchParams,
    use_case: SearchEmailsUseCase = Depends(get_search_emails_use_case),
    account_repository: IAccountRepository = Depends(get_account_repository),
    _admin_id: UUID = Depends(get_current_admin)
):
    """
    搜索邮件
    
    - **account_id**: 账户ID（UUID）
    - **query**: 搜索关键词
    - **folder**: 邮件文件夹（可选）
    - **page**: 页码
    - **page_size**: 每页大小
    """
    try:
        # 根据account_id获取账户
        account = await account_repository.get_by_id(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {account_id}"
            )
        
        result = await use_case.execute(
            email=str(account.email),
            query=params.query,
            folder=params.folder,
            page=params.page,
            page_size=params.page_size
        )
        
        emails = [EmailResponse(**email.__dict__) for email in result.emails]
        
        return PaginatedResponse.create(
            items=emails,
            total=result.total,
            page=result.page,
            page_size=result.page_size
        )
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

