"""
领域异常定义

定义所有业务规则相关的异常
所有领域异常都继承自DomainException基类
"""

from typing import Any, Dict, Optional

from src.config.constants import ErrorCode


class DomainException(Exception):
    """
    领域异常基类
    
    所有业务规则异常都应继承此类
    提供统一的异常格式和处理方式
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化领域异常
        
        Args:
            message: 错误消息
            code: 错误码
            details: 错误详细信息
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# 通用业务异常
# ============================================================================

class ValidationException(DomainException):
    """数据验证异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class NotFoundException(DomainException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, ErrorCode.NOT_FOUND, details or {"resource": resource, "identifier": str(identifier)})


class AlreadyExistsException(DomainException):
    """资源已存在异常"""
    
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' already exists"
        super().__init__(message, ErrorCode.ALREADY_EXISTS, details or {"resource": resource, "identifier": str(identifier)})


class OperationFailedException(DomainException):
    """操作失败异常"""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Operation '{operation}' failed: {reason}"
        super().__init__(message, ErrorCode.OPERATION_FAILED, details or {"operation": operation, "reason": reason})


# ============================================================================
# 认证和授权异常
# ============================================================================

class AuthenticationException(DomainException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.UNAUTHORIZED, details)


class InvalidCredentialsException(DomainException):
    """无效凭证异常"""
    
    def __init__(self, message: str = "Invalid username or password", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_CREDENTIALS, details)


class TokenExpiredException(DomainException):
    """Token过期异常"""
    
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TOKEN_EXPIRED, details)


class TokenInvalidException(DomainException):
    """Token无效异常"""
    
    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TOKEN_INVALID, details)


class ForbiddenException(DomainException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.FORBIDDEN, details)


# ============================================================================
# 账户相关异常
# ============================================================================

class AccountNotFoundException(NotFoundException):
    """账户未找到异常"""
    
    def __init__(self, email: str):
        super().__init__("Account", email)


class AccountAlreadyExistsException(AlreadyExistsException):
    """账户已存在异常"""
    
    def __init__(self, email: str):
        super().__init__("Account", email)


class AccountInactiveException(DomainException):
    """账户未激活异常"""
    
    def __init__(self, email: str):
        message = f"Account '{email}' is inactive"
        super().__init__(message, ErrorCode.ACCOUNT_INACTIVE, {"email": email})


class InvalidRefreshTokenException(DomainException):
    """无效刷新令牌异常"""
    
    def __init__(self, email: str, reason: str = ""):
        message = f"Invalid refresh token for account '{email}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, ErrorCode.INVALID_REFRESH_TOKEN, {"email": email, "reason": reason})


class TokenRefreshFailedException(DomainException):
    """Token刷新失败异常"""
    
    def __init__(self, email: str, reason: str):
        message = f"Failed to refresh token for account '{email}': {reason}"
        super().__init__(message, ErrorCode.TOKEN_REFRESH_FAILED, {"email": email, "reason": reason})


# ============================================================================
# 邮件相关异常
# ============================================================================

class EmailNotFoundException(NotFoundException):
    """邮件未找到异常"""
    
    def __init__(self, message_id: str):
        super().__init__("Email", message_id)


class IMAPConnectionException(DomainException):
    """IMAP连接异常"""
    
    def __init__(self, email: str, reason: str):
        message = f"Failed to connect to IMAP server for '{email}': {reason}"
        super().__init__(message, ErrorCode.IMAP_CONNECTION_FAILED, {"email": email, "reason": reason})


class EmailFetchException(DomainException):
    """邮件获取异常"""
    
    def __init__(self, email: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to fetch emails for '{email}': {reason}"
        super().__init__(message, ErrorCode.EMAIL_FETCH_FAILED, details or {"email": email, "reason": reason})


class EmailParseException(DomainException):
    """邮件解析异常"""
    
    def __init__(self, message_id: str, reason: str):
        message = f"Failed to parse email '{message_id}': {reason}"
        super().__init__(message, ErrorCode.EMAIL_PARSE_ERROR, {"message_id": message_id, "reason": reason})


class FolderNotFoundException(NotFoundException):
    """文件夹未找到异常"""
    
    def __init__(self, folder_name: str):
        super().__init__("Folder", folder_name)


# ============================================================================
# 数据库相关异常
# ============================================================================

class DatabaseException(DomainException):
    """数据库异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.DATABASE_ERROR, details)


class DatabaseConnectionException(DomainException):
    """数据库连接异常"""
    
    def __init__(self, reason: str):
        message = f"Database connection failed: {reason}"
        super().__init__(message, ErrorCode.DATABASE_CONNECTION_ERROR, {"reason": reason})


class DatabaseQueryException(DomainException):
    """数据库查询异常"""
    
    def __init__(self, query: str, reason: str):
        message = f"Database query failed: {reason}"
        super().__init__(message, ErrorCode.DATABASE_QUERY_ERROR, {"query": query, "reason": reason})


# ============================================================================
# 外部服务异常
# ============================================================================

class OAuthException(DomainException):
    """OAuth异常"""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"OAuth error: {reason}"
        super().__init__(message, ErrorCode.OAUTH_ERROR, details or {"reason": reason})


class IMAPException(DomainException):
    """IMAP异常"""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"IMAP error: {reason}"
        super().__init__(message, ErrorCode.IMAP_ERROR, details or {"reason": reason})


class CacheException(DomainException):
    """缓存异常"""
    
    def __init__(self, operation: str, reason: str):
        message = f"Cache {operation} failed: {reason}"
        super().__init__(message, ErrorCode.CACHE_ERROR, {"operation": operation, "reason": reason})

