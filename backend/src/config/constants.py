"""
应用常量定义

集中管理所有硬编码的常量值
"""

from enum import Enum


# ============================================================================
# 账户状态
# ============================================================================
class AccountStatus(str, Enum):
    """账户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


# ============================================================================
# Token刷新状态
# ============================================================================
class RefreshStatus(str, Enum):
    """Token刷新状态枚举"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


# ============================================================================
# 邮件文件夹
# ============================================================================
class EmailFolder(str, Enum):
    """邮件文件夹枚举"""
    INBOX = "INBOX"
    JUNK = "Junk"
    SENT = "Sent"
    DRAFTS = "Drafts"
    DELETED = "Deleted Items"
    ARCHIVE = "Archive"


# ============================================================================
# 邮件状态
# ============================================================================
class EmailStatus(str, Enum):
    """邮件状态枚举"""
    UNREAD = "unread"
    READ = "read"
    FLAGGED = "flagged"
    ARCHIVED = "archived"


# ============================================================================
# 用户角色
# ============================================================================
class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


# ============================================================================
# API错误码
# ============================================================================
class ErrorCode(str, Enum):
    """API错误码枚举"""
    # 通用错误 (1xxx)
    INTERNAL_ERROR = "E1000"
    VALIDATION_ERROR = "E1001"
    NOT_FOUND = "E1002"
    ALREADY_EXISTS = "E1003"
    OPERATION_FAILED = "E1004"
    
    # 认证错误 (2xxx)
    UNAUTHORIZED = "E2000"
    INVALID_CREDENTIALS = "E2001"
    TOKEN_EXPIRED = "E2002"
    TOKEN_INVALID = "E2003"
    FORBIDDEN = "E2004"
    
    # 账户错误 (3xxx)
    ACCOUNT_NOT_FOUND = "E3000"
    ACCOUNT_ALREADY_EXISTS = "E3001"
    ACCOUNT_INACTIVE = "E3002"
    INVALID_REFRESH_TOKEN = "E3003"
    TOKEN_REFRESH_FAILED = "E3004"
    
    # 邮件错误 (4xxx)
    EMAIL_NOT_FOUND = "E4000"
    IMAP_CONNECTION_FAILED = "E4001"
    EMAIL_FETCH_FAILED = "E4002"
    EMAIL_PARSE_ERROR = "E4003"
    FOLDER_NOT_FOUND = "E4004"
    
    # 数据库错误 (5xxx)
    DATABASE_ERROR = "E5000"
    DATABASE_CONNECTION_ERROR = "E5001"
    DATABASE_QUERY_ERROR = "E5002"
    
    # 外部服务错误 (6xxx)
    OAUTH_ERROR = "E6000"
    IMAP_ERROR = "E6001"
    CACHE_ERROR = "E6002"


# ============================================================================
# HTTP状态码映射
# ============================================================================
ERROR_CODE_HTTP_STATUS = {
    # 通用错误
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.ALREADY_EXISTS: 409,
    ErrorCode.OPERATION_FAILED: 500,
    
    # 认证错误
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.TOKEN_INVALID: 401,
    ErrorCode.FORBIDDEN: 403,
    
    # 账户错误
    ErrorCode.ACCOUNT_NOT_FOUND: 404,
    ErrorCode.ACCOUNT_ALREADY_EXISTS: 409,
    ErrorCode.ACCOUNT_INACTIVE: 400,
    ErrorCode.INVALID_REFRESH_TOKEN: 400,
    ErrorCode.TOKEN_REFRESH_FAILED: 500,
    
    # 邮件错误
    ErrorCode.EMAIL_NOT_FOUND: 404,
    ErrorCode.IMAP_CONNECTION_FAILED: 503,
    ErrorCode.EMAIL_FETCH_FAILED: 500,
    ErrorCode.EMAIL_PARSE_ERROR: 500,
    ErrorCode.FOLDER_NOT_FOUND: 404,
    
    # 数据库错误
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.DATABASE_CONNECTION_ERROR: 503,
    ErrorCode.DATABASE_QUERY_ERROR: 500,
    
    # 外部服务错误
    ErrorCode.OAUTH_ERROR: 503,
    ErrorCode.IMAP_ERROR: 503,
    ErrorCode.CACHE_ERROR: 500,
}


# ============================================================================
# 分页常量
# ============================================================================
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 500

# ============================================================================
# 时间格式
# ============================================================================
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# ============================================================================
# 缓存键前缀
# ============================================================================
CACHE_KEY_EMAIL_LIST = "email:list:{email_id}:{folder}:{page}:{page_size}"
CACHE_KEY_EMAIL_DETAIL = "email:detail:{message_id}"
CACHE_KEY_ACCOUNT = "account:{email_id}"
CACHE_KEY_TOKEN = "token:{email_id}"

# ============================================================================
# 正则表达式
# ============================================================================
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

