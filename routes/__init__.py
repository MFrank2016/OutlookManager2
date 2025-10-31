"""
路由模块包

包含所有API路由的定义
"""

from fastapi import APIRouter

from . import auth_routes, account_routes, email_routes, cache_routes

# 创建主路由器
main_router = APIRouter()

# 包含所有子路由
main_router.include_router(auth_routes.router)
main_router.include_router(account_routes.router)
main_router.include_router(email_routes.router)
main_router.include_router(cache_routes.router)

