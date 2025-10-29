"""
Admin实体

表示系统管理员的领域实体
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from src.domain.exceptions import ValidationException
from src.domain.value_objects import EmailAddress


class Admin:
    """
    管理员实体
    
    代表系统管理员账户
    包含管理员的身份、凭证和状态信息
    """
    
    def __init__(
        self,
        username: str,
        password_hash: str,
        id: Optional[UUID] = None,
        email: Optional[EmailAddress] = None,
        is_active: bool = True,
        last_login: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        初始化管理员实体
        
        Args:
            username: 用户名
            password_hash: 密码哈希值
            id: 管理员唯一标识
            email: 管理员邮箱地址（可选）
            is_active: 是否激活
            last_login: 最后登录时间
            created_at: 创建时间
            updated_at: 更新时间
        """
        self._id = id or uuid4()
        self._username = username
        self._password_hash = password_hash
        self._email = email
        self._is_active = is_active
        self._last_login = last_login
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
        # 验证
        self._validate()
    
    def _validate(self) -> None:
        """验证管理员数据"""
        if not self._username or not self._username.strip():
            raise ValidationException("Username cannot be empty")
        
        if len(self._username) < 3:
            raise ValidationException(
                "Username must be at least 3 characters long",
                {"username_length": len(self._username)}
            )
        
        if len(self._username) > 50:
            raise ValidationException(
                "Username must not exceed 50 characters",
                {"username_length": len(self._username)}
            )
        
        if not self._password_hash or not self._password_hash.strip():
            raise ValidationException("Password hash cannot be empty")
    
    # ========================================================================
    # 属性访问器
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        """管理员ID"""
        return self._id
    
    @property
    def username(self) -> str:
        """用户名"""
        return self._username
    
    @property
    def password_hash(self) -> str:
        """密码哈希值"""
        return self._password_hash
    
    @property
    def email(self) -> Optional[EmailAddress]:
        """邮箱地址"""
        return self._email
    
    @property
    def email_str(self) -> Optional[str]:
        """邮箱地址字符串"""
        return str(self._email) if self._email else None
    
    @property
    def is_active(self) -> bool:
        """是否激活"""
        return self._is_active
    
    @property
    def last_login(self) -> Optional[datetime]:
        """最后登录时间"""
        return self._last_login
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at
    
    # ========================================================================
    # 业务方法
    # ========================================================================
    
    def update_password(self, new_password_hash: str) -> None:
        """
        更新密码
        
        Args:
            new_password_hash: 新的密码哈希值
        """
        if not new_password_hash or not new_password_hash.strip():
            raise ValidationException("Password hash cannot be empty")
        
        self._password_hash = new_password_hash
        self._updated_at = datetime.utcnow()
    
    def update_email(self, email: Optional[EmailAddress]) -> None:
        """
        更新邮箱地址
        
        Args:
            email: 新的邮箱地址
        """
        self._email = email
        self._updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """激活管理员账户"""
        if not self._is_active:
            self._is_active = True
            self._updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用管理员账户"""
        if self._is_active:
            self._is_active = False
            self._updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        """记录登录时间"""
        self._last_login = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    def can_login(self) -> bool:
        """
        检查是否可以登录
        
        Returns:
            bool: 是否可以登录（激活状态）
        """
        return self._is_active
    
    # ========================================================================
    # 特殊方法
    # ========================================================================
    
    def __eq__(self, other) -> bool:
        """相等性比较（基于ID）"""
        if isinstance(other, Admin):
            return self._id == other._id
        return False
    
    def __hash__(self) -> int:
        """哈希值（基于ID）"""
        return hash(self._id)
    
    def __str__(self) -> str:
        status = "active" if self._is_active else "inactive"
        return f"Admin({self._username}, status={status})"
    
    def __repr__(self) -> str:
        return (
            f"Admin(id={self._id}, username='{self._username}', "
            f"is_active={self._is_active})"
        )

