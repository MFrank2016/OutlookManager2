"""
登录用例

处理管理员登录的业务逻辑
"""

import logging
from datetime import datetime, timedelta

from src.application.dto import LoginDTO, LoginResultDTO
from src.config.settings import settings
from src.domain.exceptions import InvalidCredentialsException
from src.domain.repositories.admin_repository import IAdminRepository
from src.domain.services import IPasswordService

logger = logging.getLogger(__name__)


class LoginUseCase:
    """登录用例"""
    
    def __init__(
        self,
        admin_repository: IAdminRepository,
        password_service: IPasswordService
    ):
        """
        初始化用例
        
        Args:
            admin_repository: 管理员仓储
            password_service: 密码服务
        """
        self._admin_repository = admin_repository
        self._password_service = password_service
    
    async def execute(self, dto: LoginDTO) -> LoginResultDTO:
        """
        执行登录
        
        Args:
            dto: 登录请求DTO
            
        Returns:
            LoginResultDTO: 登录结果DTO
            
        Raises:
            InvalidCredentialsException: 凭证无效
        """
        logger.info(f"Login attempt for username: {dto.username}")
        
        # 查找管理员
        admin = await self._admin_repository.get_by_username(dto.username)
        
        if not admin:
            logger.warning(f"Admin not found: {dto.username}")
            raise InvalidCredentialsException("Invalid username or password")
        
        # 检查是否可以登录
        if not admin.can_login():
            logger.warning(f"Admin account is inactive: {dto.username}")
            raise InvalidCredentialsException("Account is inactive")
        
        # 验证密码
        if not self._password_service.verify_password(dto.password, admin.password_hash):
            logger.warning(f"Invalid password for admin: {dto.username}")
            raise InvalidCredentialsException("Invalid username or password")
        
        # 记录登录时间
        admin.record_login()
        await self._admin_repository.update(admin)
        
        # 生成JWT Token（这里简化处理，实际实现在基础设施层）
        # 注意：真实实现需要在基础设施层创建JWT服务
        access_token = self._generate_token(admin.id, admin.username)
        
        logger.info(f"Login successful for admin: {dto.username}")
        
        return LoginResultDTO(
            success=True,
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            admin_id=admin.id,
            username=admin.username,
            message="Login successful"
        )
    
    def _generate_token(self, admin_id, username: str) -> str:
        """
        生成JWT Token
        
        注意：这里导入JWT服务，避免循环依赖
        """
        from src.infrastructure.external_services.auth import get_jwt_service
        
        jwt_service = get_jwt_service()
        return jwt_service.create_access_token(admin_id, username)

