"""
验证Token用例

处理JWT Token验证的业务逻辑
"""

import logging
from uuid import UUID

from src.application.dto import VerifyTokenResultDTO
from src.domain.repositories.admin_repository import IAdminRepository

logger = logging.getLogger(__name__)


class VerifyTokenUseCase:
    """验证Token用例"""
    
    def __init__(self, admin_repository: IAdminRepository):
        """
        初始化用例
        
        Args:
            admin_repository: 管理员仓储
        """
        self._admin_repository = admin_repository
    
    async def execute(self, token: str) -> VerifyTokenResultDTO:
        """
        执行Token验证
        
        Args:
            token: JWT Token字符串
            
        Returns:
            VerifyTokenResultDTO: 验证结果DTO
        """
        logger.info("Verifying JWT token")
        
        try:
            # 解析Token（简化版本）
            # 注意：实际应该在基础设施层实现JWT服务进行解析
            admin_id, username = self._parse_token(token)
            
            if not admin_id:
                return VerifyTokenResultDTO(
                    valid=False,
                    admin_id=None,
                    username=None,
                    message="Invalid token"
                )
            
            # 验证管理员是否存在且激活
            admin = await self._admin_repository.get_by_id(admin_id)
            
            if not admin or not admin.can_login():
                return VerifyTokenResultDTO(
                    valid=False,
                    admin_id=None,
                    username=None,
                    message="Admin not found or inactive"
                )
            
            logger.info(f"Token verified successfully for admin: {username}")
            
            return VerifyTokenResultDTO(
                valid=True,
                admin_id=admin.id,
                username=admin.username,
                message="Token is valid"
            )
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return VerifyTokenResultDTO(
                valid=False,
                admin_id=None,
                username=None,
                message=f"Token verification failed: {str(e)}"
            )
    
    def _parse_token(self, token: str) -> tuple[UUID | None, str | None]:
        """
        解析Token
        
        Args:
            token: JWT Token
            
        Returns:
            tuple[UUID | None, str | None]: (管理员ID, 用户名)
        """
        from src.infrastructure.external_services.auth import get_jwt_service
        
        try:
            jwt_service = get_jwt_service()
            admin_id = jwt_service.get_admin_id_from_token(token)
            username = jwt_service.get_username_from_token(token)
            return admin_id, username
        except Exception as e:
            logger.error(f"Failed to parse token: {str(e)}")
            return None, None

