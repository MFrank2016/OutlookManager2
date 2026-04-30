"""API v2 路由聚合。"""

from fastapi import APIRouter

from . import account_routes, message_routes


v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(account_routes.router)
v2_router.include_router(message_routes.router)


__all__ = ["v2_router"]
