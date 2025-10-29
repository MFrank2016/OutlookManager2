"""领域异常模块"""
from .domain_exceptions import (
    # 基础异常
    DomainException,
    ValidationException,
    NotFoundException,
    AlreadyExistsException,
    OperationFailedException,
    # 认证异常
    AuthenticationException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    ForbiddenException,
    # 账户异常
    AccountNotFoundException,
    AccountAlreadyExistsException,
    AccountInactiveException,
    InvalidRefreshTokenException,
    TokenRefreshFailedException,
    # 邮件异常
    EmailNotFoundException,
    IMAPConnectionException,
    EmailFetchException,
    EmailParseException,
    FolderNotFoundException,
    # 数据库异常
    DatabaseException,
    DatabaseConnectionException,
    DatabaseQueryException,
    # 外部服务异常
    OAuthException,
    IMAPException,
    CacheException,
)

__all__ = [
    # 基础异常
    "DomainException",
    "ValidationException",
    "NotFoundException",
    "AlreadyExistsException",
    "OperationFailedException",
    # 认证异常
    "AuthenticationException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "TokenInvalidException",
    "ForbiddenException",
    # 账户异常
    "AccountNotFoundException",
    "AccountAlreadyExistsException",
    "AccountInactiveException",
    "InvalidRefreshTokenException",
    "TokenRefreshFailedException",
    # 邮件异常
    "EmailNotFoundException",
    "IMAPConnectionException",
    "EmailFetchException",
    "EmailParseException",
    "FolderNotFoundException",
    # 数据库异常
    "DatabaseException",
    "DatabaseConnectionException",
    "DatabaseQueryException",
    # 外部服务异常
    "OAuthException",
    "IMAPException",
    "CacheException",
]

