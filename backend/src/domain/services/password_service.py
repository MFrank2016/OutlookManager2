"""
密码服务

处理密码加密和验证的领域服务
"""

from abc import ABC, abstractmethod


class IPasswordService(ABC):
    """
    密码管理服务接口
    
    定义密码加密和验证的业务逻辑
    具体实现在基础设施层
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希加密
        
        Args:
            password: 明文密码
            
        Returns:
            str: 密码哈希值
        """
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码是否匹配
        
        Args:
            plain_password: 明文密码
            hashed_password: 密码哈希值
            
        Returns:
            bool: 是否匹配
        """
        pass
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """
        验证密码强度
        
        Args:
            password: 明文密码
            
        Returns:
            tuple[bool, list[str]]: (是否满足强度要求, 错误信息列表)
        """
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

