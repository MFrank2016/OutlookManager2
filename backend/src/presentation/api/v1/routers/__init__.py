"""API路由"""
from .accounts import router as accounts_router
from .admin import router as admin_router
from .auth import router as auth_router
from .emails import router as emails_router

__all__ = ["accounts_router", "auth_router", "emails_router", "admin_router"]

