"""
修改密码用例

处理管理员密码修改的业务逻辑
"""

import logging
from uuid import UUID

from src.application.dto import ChangePasswordDTO, ChangePasswordResultDTO
from src.domain.exceptions import (
    InvalidCredentialsException,
    NotFoundException,
    ValidationException,
)
from src.domain.repositories.admin_repository import IAdminRepository
from src.domain.services import IPasswordService

logger = logging.getLogger(__name__)


class ChangePasswordUseCase:
    """修改密码用例"""
    
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
    
    async def execute(
        self,
        admin_id: UUID,
        dto: ChangePasswordDTO
    ) -> ChangePasswordResultDTO:
        """
        执行修改密码
        
        Args:
            admin_id: 管理员ID
            dto: 修改密码DTO
            
        Returns:
            ChangePasswordResultDTO: 修改结果DTO
            
        Raises:
            NotFoundException: 管理员不存在
            InvalidCredentialsException: 旧密码错误
            ValidationException: 新密码不符合要求
        """
        logger.info(f"Changing password for admin: {admin_id}")
        
        # 获取管理员
        admin = await self._admin_repository.get_by_id(admin_id)
        
        if not admin:
            logger.warning(f"Admin not found: {admin_id}")
            raise NotFoundException("Admin", str(admin_id))
        
        # 验证旧密码
        if not self._password_service.verify_password(
            dto.old_password,
            admin.password_hash
        ):
            logger.warning(f"Invalid old password for admin: {admin_id}")
            raise InvalidCredentialsException("Old password is incorrect")
        
        # 验证新密码强度
        is_valid, errors = self._password_service.validate_password_strength(
            dto.new_password
        )
        
        if not is_valid:
            logger.warning(f"New password validation failed for admin: {admin_id}")
            raise ValidationException(
                "New password does not meet requirements",
                {"errors": errors}
            )
        
        # 哈希新密码
        new_password_hash = self._password_service.hash_password(dto.new_password)
        
        # 更新密码
        admin.update_password(new_password_hash)
        await self._admin_repository.update(admin)
        
        logger.info(f"Password changed successfully for admin: {admin_id}")
        
        return ChangePasswordResultDTO(
            success=True,
            message="Password changed successfully"
        )

