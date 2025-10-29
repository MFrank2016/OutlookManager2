"""
认证依赖

提供认证和授权的依赖注入
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from uuid import UUID

from src.application.use_cases.auth import VerifyTokenUseCase
from src.presentation.api.v1.dependencies.services import get_verify_token_use_case

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    verify_token_use_case: VerifyTokenUseCase = Depends(get_verify_token_use_case)
) -> UUID:
    """
    获取当前认证的管理员ID
    
    Args:
        credentials: HTTP Bearer凭证
        verify_token_use_case: 验证Token用例
        
    Returns:
        UUID: 管理员ID
        
    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    
    # 验证Token
    result = await verify_token_use_case.execute(token)
    
    if not result.valid or not result.admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result.admin_id

