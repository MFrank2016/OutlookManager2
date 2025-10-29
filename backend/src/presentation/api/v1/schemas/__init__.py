"""API Schemas"""
from .account_schema import (
    AccountCreateRequest,
    AccountResponse,
    AccountUpdateRequest,
    RefreshTokenResponse,
)
from .admin_schema import (
    AdminProfileResponse,
    SystemStatsResponse,
    UpdateAdminProfileRequest,
)
from .auth_schema import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)
from .common_schema import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)
from .email_schema import (
    EmailDetailResponse,
    EmailListParams,
    EmailResponse,
    EmailSearchParams,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthResponse",
    # Account
    "AccountCreateRequest",
    "AccountUpdateRequest",
    "AccountResponse",
    "RefreshTokenResponse",
    # Email
    "EmailResponse",
    "EmailDetailResponse",
    "EmailListParams",
    "EmailSearchParams",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "ChangePasswordRequest",
    "ChangePasswordResponse",
    "TokenResponse",
    # Admin
    "AdminProfileResponse",
    "UpdateAdminProfileRequest",
    "SystemStatsResponse",
]

