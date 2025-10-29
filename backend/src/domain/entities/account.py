"""
Account实体

表示邮箱账户的领域实体
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from src.config.constants import AccountStatus, RefreshStatus
from src.domain.exceptions import ValidationException
from src.domain.value_objects import EmailAddress


class Account:
    """
    账户实体
    
    代表一个Outlook邮箱账户
    包含账户的身份、凭证和状态信息
    """
    
    def __init__(
        self,
        email: EmailAddress,
        refresh_token: str,
        client_id: str,
        id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        status: AccountStatus = AccountStatus.ACTIVE,
        refresh_status: RefreshStatus = RefreshStatus.PENDING,
        last_refresh_time: Optional[datetime] = None,
        next_refresh_time: Optional[datetime] = None,
        refresh_error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        初始化账户实体
        
        Args:
            email: 邮箱地址（值对象）
            refresh_token: OAuth2刷新令牌
            client_id: Azure客户端ID
            id: 账户唯一标识
            tags: 标签列表
            status: 账户状态
            refresh_status: Token刷新状态
            last_refresh_time: 最后刷新时间
            next_refresh_time: 下次刷新时间
            refresh_error: 刷新错误信息
            created_at: 创建时间
            updated_at: 更新时间
        """
        self._id = id or uuid4()
        self._email = email
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._tags = tags or []
        self._status = status
        self._refresh_status = refresh_status
        self._last_refresh_time = last_refresh_time
        self._next_refresh_time = next_refresh_time
        self._refresh_error = refresh_error
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
        # 验证
        self._validate()
    
    def _validate(self) -> None:
        """验证账户数据"""
        if not self._refresh_token:
            raise ValidationException("Refresh token cannot be empty")
        
        if not self._client_id:
            raise ValidationException("Client ID cannot be empty")
        
        if len(self._refresh_token) < 10:
            raise ValidationException("Invalid refresh token format")
    
    # ========================================================================
    # 属性访问器
    # ========================================================================
    
    @property
    def id(self) -> UUID:
        """账户ID"""
        return self._id
    
    @property
    def email(self) -> EmailAddress:
        """邮箱地址"""
        return self._email
    
    @property
    def email_str(self) -> str:
        """邮箱地址字符串"""
        return str(self._email)
    
    @property
    def refresh_token(self) -> str:
        """刷新令牌"""
        return self._refresh_token
    
    @property
    def client_id(self) -> str:
        """客户端ID"""
        return self._client_id
    
    @property
    def tags(self) -> List[str]:
        """标签列表"""
        return self._tags.copy()  # 返回副本，防止外部修改
    
    @property
    def status(self) -> AccountStatus:
        """账户状态"""
        return self._status
    
    @property
    def refresh_status(self) -> RefreshStatus:
        """Token刷新状态"""
        return self._refresh_status
    
    @property
    def last_refresh_time(self) -> Optional[datetime]:
        """最后刷新时间"""
        return self._last_refresh_time
    
    @property
    def next_refresh_time(self) -> Optional[datetime]:
        """下次刷新时间"""
        return self._next_refresh_time
    
    @property
    def refresh_error(self) -> Optional[str]:
        """刷新错误信息"""
        return self._refresh_error
    
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
    
    def update_refresh_token(self, new_refresh_token: str) -> None:
        """
        更新刷新令牌
        
        Args:
            new_refresh_token: 新的刷新令牌
        """
        if not new_refresh_token:
            raise ValidationException("Refresh token cannot be empty")
        
        self._refresh_token = new_refresh_token
        self._last_refresh_time = datetime.utcnow()
        self._refresh_status = RefreshStatus.SUCCESS
        self._refresh_error = None
        self._updated_at = datetime.utcnow()
    
    def mark_refresh_failed(self, error_message: str) -> None:
        """
        标记Token刷新失败
        
        Args:
            error_message: 错误信息
        """
        self._refresh_status = RefreshStatus.FAILED
        self._refresh_error = error_message
        self._updated_at = datetime.utcnow()
    
    def mark_refresh_in_progress(self) -> None:
        """标记Token正在刷新"""
        self._refresh_status = RefreshStatus.IN_PROGRESS
        self._updated_at = datetime.utcnow()
    
    def schedule_next_refresh(self, next_time: datetime) -> None:
        """
        安排下次刷新时间
        
        Args:
            next_time: 下次刷新时间
        """
        self._next_refresh_time = next_time
        self._updated_at = datetime.utcnow()
    
    def update_tags(self, tags: List[str]) -> None:
        """
        更新标签
        
        Args:
            tags: 新的标签列表
        """
        # 去重和清理
        self._tags = list(set(tag.strip() for tag in tags if tag.strip()))
        self._updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        添加标签
        
        Args:
            tag: 标签名称
        """
        tag = tag.strip()
        if tag and tag not in self._tags:
            self._tags.append(tag)
            self._updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """
        移除标签
        
        Args:
            tag: 标签名称
        """
        if tag in self._tags:
            self._tags.remove(tag)
            self._updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """激活账户"""
        self._status = AccountStatus.ACTIVE
        self._updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用账户"""
        self._status = AccountStatus.INACTIVE
        self._updated_at = datetime.utcnow()
    
    def suspend(self, reason: Optional[str] = None) -> None:
        """
        暂停账户
        
        Args:
            reason: 暂停原因
        """
        self._status = AccountStatus.SUSPENDED
        if reason:
            self._refresh_error = reason
        self._updated_at = datetime.utcnow()
    
    def mark_error(self, error_message: str) -> None:
        """
        标记账户出错
        
        Args:
            error_message: 错误信息
        """
        self._status = AccountStatus.ERROR
        self._refresh_error = error_message
        self._updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """账户是否激活"""
        return self._status == AccountStatus.ACTIVE
    
    def is_refresh_needed(self) -> bool:
        """
        是否需要刷新Token
        
        Returns:
            bool: 如果需要刷新返回True
        """
        if not self._next_refresh_time:
            return True
        
        return datetime.utcnow() >= self._next_refresh_time
    
    def can_refresh(self) -> bool:
        """
        是否可以刷新Token
        
        Returns:
            bool: 如果可以刷新返回True
        """
        # 只有激活状态且不在刷新中才可以刷新
        return self.is_active() and self._refresh_status != RefreshStatus.IN_PROGRESS
    
    # ========================================================================
    # 特殊方法
    # ========================================================================
    
    def __eq__(self, other) -> bool:
        """相等性比较（基于ID）"""
        if isinstance(other, Account):
            return self._id == other._id
        return False
    
    def __hash__(self) -> int:
        """哈希值（基于ID）"""
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"Account({self.email_str}, status={self._status.value})"
    
    def __repr__(self) -> str:
        return (
            f"Account(id={self._id}, email={self.email_str}, "
            f"status={self._status.value}, refresh_status={self._refresh_status.value})"
        )

