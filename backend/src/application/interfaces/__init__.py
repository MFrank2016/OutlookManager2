"""应用层接口"""
from .cache_service import ICacheService
from .imap_client import IIMAPClient
from .oauth_client import IOAuthClient

__all__ = ["IIMAPClient", "IOAuthClient", "ICacheService"]

