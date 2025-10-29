"""
认证路由

处理认证相关的API请求
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dto import ChangePasswordDTO, LoginDTO
from src.application.use_cases.auth import (
    ChangePasswordUseCase,
    LoginUseCase,
    VerifyTokenUseCase,
)
from src.domain.exceptions import InvalidCredentialsException, ValidationException
from src.presentation.api.v1.dependencies import (
    get_change_password_use_case,
    get_current_admin,
    get_login_use_case,
    get_verify_token_use_case,
)
from src.presentation.api.v1.schemas import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="管理员登录"
)
async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    """管理员登录获取访问令牌"""
    try:
        dto = LoginDTO(
            username=request.username,
            password=request.password
        )
        
        result = await use_case.execute(dto)
        return LoginResponse(**result.__dict__)
        
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    summary="修改密码"
)
async def change_password(
    request: ChangePasswordRequest,
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
    admin_id: UUID = Depends(get_current_admin)
):
    """修改当前管理员的密码"""
    try:
        dto = ChangePasswordDTO(
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        result = await use_case.execute(admin_id, dto)
        return ChangePasswordResponse(**result.__dict__)
        
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/verify-token",
    response_model=TokenResponse,
    summary="验证访问令牌"
)
async def verify_token(
    admin_id: UUID = Depends(get_current_admin)
):
    """验证当前访问令牌是否有效"""
    # 如果能执行到这里，说明token有效
    return TokenResponse(
        admin_id=admin_id,
        valid=True,
        username="admin",
        message="Token is valid"
    )

