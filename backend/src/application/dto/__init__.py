"""应用层DTOs"""
from .account_dto import (
    AccountDTO,
    AccountListDTO,
    CreateAccountDTO,
    RefreshTokenDTO,
    UpdateAccountDTO,
)
from .auth_dto import (
    ChangePasswordDTO,
    ChangePasswordResultDTO,
    LoginDTO,
    LoginResultDTO,
    TokenPayloadDTO,
    VerifyTokenResultDTO,
)
from .email_dto import (
    EmailDetailDTO,
    EmailDTO,
    EmailListDTO,
    EmailSearchDTO,
)

__all__ = [
    # Account DTOs
    "AccountDTO",
    "CreateAccountDTO",
    "UpdateAccountDTO",
    "AccountListDTO",
    "RefreshTokenDTO",
    # Email DTOs
    "EmailDTO",
    "EmailListDTO",
    "EmailSearchDTO",
    "EmailDetailDTO",
    # Auth DTOs
    "LoginDTO",
    "LoginResultDTO",
    "ChangePasswordDTO",
    "ChangePasswordResultDTO",
    "TokenPayloadDTO",
    "VerifyTokenResultDTO",
]

