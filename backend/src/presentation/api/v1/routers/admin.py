"""
管理员管理路由

处理管理员相关的API请求
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.config.settings import settings
from src.domain.exceptions import NotFoundException, ValidationException
from src.domain.repositories.account_repository import IAccountRepository
from src.domain.repositories.admin_repository import IAdminRepository
from src.domain.value_objects import EmailAddress
from src.presentation.api.v1.dependencies import (
    get_account_repository,
    get_admin_repository,
    get_current_admin,
)
from src.presentation.api.v1.schemas.admin_schema import (
    AdminProfileResponse,
    SystemStatsResponse,
    UpdateAdminProfileRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# 应用启动时间（用于计算uptime）
_app_start_time = datetime.utcnow()


@router.get(
    "/profile",
    response_model=AdminProfileResponse,
    summary="获取当前管理员信息"
)
async def get_profile(
    admin_id: UUID = Depends(get_current_admin),
    admin_repository: IAdminRepository = Depends(get_admin_repository)
):
    """获取当前登录管理员的个人信息"""
    admin = await admin_repository.get_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return AdminProfileResponse(
        id=admin.id,
        username=admin.username,
        email=admin.email_str,
        is_active=admin.is_active,
        last_login=admin.last_login,
        created_at=admin.created_at
    )


@router.put(
    "/profile",
    response_model=AdminProfileResponse,
    summary="更新管理员信息"
)
@router.patch(
    "/profile",
    response_model=AdminProfileResponse,
    summary="更新管理员信息"
)
async def update_profile(
    request: UpdateAdminProfileRequest,
    admin_id: UUID = Depends(get_current_admin),
    admin_repository: IAdminRepository = Depends(get_admin_repository)
):
    """更新当前登录管理员的个人信息"""
    try:
        admin = await admin_repository.get_by_id(admin_id)
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # 更新邮箱
        if request.email is not None:
            email_vo = EmailAddress.create(request.email) if request.email else None
            admin.update_email(email_vo)
        
        # 保存更新
        updated_admin = await admin_repository.update(admin)
        
        return AdminProfileResponse(
            id=updated_admin.id,
            username=updated_admin.username,
            email=updated_admin.email_str,
            is_active=updated_admin.is_active,
            last_login=updated_admin.last_login,
            created_at=updated_admin.created_at
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="获取系统统计信息"
)
async def get_system_stats(
    _admin_id: UUID = Depends(get_current_admin),
    account_repository: IAccountRepository = Depends(get_account_repository),
    admin_repository: IAdminRepository = Depends(get_admin_repository)
):
    """获取系统统计信息（仅管理员可访问）"""
    # 获取账户统计
    total_accounts = await account_repository.count()
    
    # 获取激活账户（简化实现，实际需要添加方法）
    all_accounts, _ = await account_repository.get_all(skip=0, limit=10000)
    active_accounts = sum(1 for acc in all_accounts if acc.is_active())
    
    # 获取管理员统计
    total_admins = await admin_repository.count()
    
    # 计算系统运行时间
    uptime_delta = datetime.utcnow() - _app_start_time
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}天 {hours}小时 {minutes}分钟"
    
    return SystemStatsResponse(
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        total_admins=total_admins,
        system_uptime=uptime_str,
        app_version=settings.APP_VERSION
    )

