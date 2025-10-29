"""
密码服务实现

使用passlib实现密码加密和验证
"""

import logging

from passlib.context import CryptContext

from src.domain.services import IPasswordService

logger = logging.getLogger(__name__)


class PasswordServiceImpl(IPasswordService):
    """密码管理服务实现"""
    
    def __init__(self):
        """初始化密码服务"""
        # 使用bcrypt算法
        self._pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )
    
    def hash_password(self, password: str) -> str:
        """对密码进行哈希加密"""
        return self._pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码是否匹配"""
        try:
            return self._pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """验证密码强度"""
        errors = []
        
        # 最小长度检查
        if len(password) < 8:
            errors.append("密码长度至少为8个字符")
        
        # 最大长度检查
        if len(password) > 128:
            errors.append("密码长度不能超过128个字符")
        
        # 复杂度检查（至少包含字母和数字）
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not has_letter:
            errors.append("密码必须包含字母")
        
        if not has_digit:
            errors.append("密码必须包含数字")
        
        return len(errors) == 0, errors

