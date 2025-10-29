"""
账户管理路由

处理账户相关的API请求
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dto import CreateAccountDTO, UpdateAccountDTO
from src.application.use_cases.account import (
    CreateAccountUseCase,
    DeleteAccountUseCase,
    GetAccountUseCase,
    ListAccountsUseCase,
    RefreshTokenUseCase,
    UpdateAccountUseCase,
)
from src.domain.exceptions import (
    AccountAlreadyExistsException,
    AccountNotFoundException,
    DomainException,
)
from src.presentation.api.v1.dependencies import (
    get_create_account_use_case,
    get_current_admin,
    get_delete_account_use_case,
    get_get_account_use_case,
    get_list_accounts_use_case,
    get_refresh_token_use_case,
    get_update_account_use_case,
)
from src.presentation.api.v1.schemas import (
    AccountCreateRequest,
    AccountResponse,
    AccountUpdateRequest,
    PaginatedResponse,
    RefreshTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建账户"
)
async def create_account(
    request: AccountCreateRequest,
    use_case: CreateAccountUseCase = Depends(get_create_account_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """创建新的邮箱账户"""
    try:
        dto = CreateAccountDTO(
            email=request.email,
            refresh_token=request.refresh_token,
            client_id=request.client_id,
            tags=request.tags
        )
        
        result = await use_case.execute(dto)
        
        return AccountResponse(**result.__dict__)
        
    except AccountAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=PaginatedResponse[AccountResponse],
    summary="获取账户列表"
)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    email_search: str | None = Query(None),
    use_case: ListAccountsUseCase = Depends(get_list_accounts_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """获取账户列表（分页）"""
    result = await use_case.execute(
        page=page,
        page_size=page_size,
        email_search=email_search
    )
    
    accounts = [AccountResponse(**acc.__dict__) for acc in result.accounts]
    
    return PaginatedResponse.create(
        items=accounts,
        total=result.total,
        page=result.page,
        page_size=result.page_size
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="获取账户详情"
)
async def get_account(
    account_id: UUID,
    use_case: GetAccountUseCase = Depends(get_get_account_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """获取指定账户的详情"""
    try:
        result = await use_case.execute_by_id(account_id)
        return AccountResponse(**result.__dict__)
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
    summary="更新账户"
)
@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="更新账户"
)
async def update_account(
    account_id: UUID,
    request: AccountUpdateRequest,
    use_case: UpdateAccountUseCase = Depends(get_update_account_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """更新账户信息"""
    try:
        dto = UpdateAccountDTO(
            tags=request.tags,
            status=request.status
        )
        
        result = await use_case.execute(account_id, dto)
        return AccountResponse(**result.__dict__)
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除账户"
)
async def delete_account(
    account_id: UUID,
    use_case: DeleteAccountUseCase = Depends(get_delete_account_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """删除指定账户"""
    try:
        await use_case.execute(account_id)
        
    except AccountNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{account_id}/refresh-token",
    response_model=RefreshTokenResponse,
    summary="刷新Token"
)
async def refresh_token(
    account_id: UUID,
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
    _admin_id: UUID = Depends(get_current_admin)
):
    """刷新指定账户的访问Token"""
    try:
        result = await use_case.execute(account_id)
        return RefreshTokenResponse(**result.__dict__)
        
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

