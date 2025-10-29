"""邮件管理用例"""
from .get_email_detail import GetEmailDetailUseCase
from .list_emails import ListEmailsUseCase
from .search_emails import SearchEmailsUseCase

__all__ = [
    "ListEmailsUseCase",
    "GetEmailDetailUseCase",
    "SearchEmailsUseCase",
]

