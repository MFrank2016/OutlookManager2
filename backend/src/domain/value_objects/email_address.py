"""
EmailAddress值对象

表示一个不可变的电子邮件地址
"""

import re
from dataclasses import dataclass
from typing import ClassVar

from src.config.constants import EMAIL_REGEX
from src.domain.exceptions import ValidationException


@dataclass(frozen=True)
class EmailAddress:
    """
    电子邮件地址值对象
    
    特性：
    - 不可变（frozen=True）
    - 自动验证格式
    - 规范化存储（小写）
    """
    
    value: str
    EMAIL_PATTERN: ClassVar[re.Pattern] = re.compile(EMAIL_REGEX)
    
    def __post_init__(self):
        """初始化后验证"""
        # 由于frozen=True，需要使用object.__setattr__来设置值
        normalized_value = self.value.strip().lower()
        object.__setattr__(self, 'value', normalized_value)
        
        if not self._is_valid(normalized_value):
            raise ValidationException(
                f"Invalid email address: {self.value}",
                {"email": self.value}
            )
    
    @classmethod
    def _is_valid(cls, email: str) -> bool:
        """
        验证邮箱地址格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        if not email:
            return False
        
        if len(email) > 254:  # RFC 5321
            return False
        
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def create(cls, email: str) -> "EmailAddress":
        """
        工厂方法创建EmailAddress
        
        Args:
            email: 邮箱地址字符串
            
        Returns:
            EmailAddress: 邮箱地址值对象
        """
        return cls(value=email)
    
    def get_domain(self) -> str:
        """
        获取邮箱域名
        
        Returns:
            str: 域名部分
        """
        if '@' in self.value:
            return self.value.split('@')[1]
        return ""
    
    def get_local_part(self) -> str:
        """
        获取邮箱本地部分（@之前的部分）
        
        Returns:
            str: 本地部分
        """
        if '@' in self.value:
            return self.value.split('@')[0]
        return self.value
    
    def is_outlook(self) -> bool:
        """
        判断是否为Outlook邮箱
        
        Returns:
            bool: 是否为Outlook邮箱
        """
        outlook_domains = ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']
        return self.get_domain() in outlook_domains
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"EmailAddress('{self.value}')"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, EmailAddress):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        return hash(self.value)

