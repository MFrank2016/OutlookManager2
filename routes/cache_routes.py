"""
缓存管理路由模块

处理缓存管理相关的API端点
"""

import logging

from fastapi import APIRouter, Depends

import auth
import database as db
from cache_service import clear_email_cache

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/cache", tags=["缓存管理"])


@router.delete("/{email_id}")
async def clear_cache(email_id: str, admin: dict = Depends(auth.get_current_admin)):
    """清除指定邮箱的缓存（包括内存和SQLite缓存）"""
    # 清除内存缓存
    clear_email_cache(email_id)
    # 清除 SQLite 缓存
    db.clear_email_cache_db(email_id)
    logger.info(f"Cache cleared (memory + SQLite) for {email_id} by {admin['username']}")
    return {"message": f"Cache cleared for {email_id}"}


@router.delete("")
async def clear_all_cache(admin: dict = Depends(auth.get_current_admin)):
    """清除所有缓存"""
    clear_email_cache()
    logger.info(f"All cache cleared by {admin['username']}")
    return {"message": "All cache cleared"}

