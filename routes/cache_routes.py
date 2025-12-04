"""
缓存管理路由模块

处理缓存管理相关的API端点
"""

from fastapi import APIRouter, Depends, HTTPException

import auth
import database as db
import cache_service
from permissions import Permission
from logger_config import logger

# 创建路由器
router = APIRouter(prefix="/cache", tags=["缓存管理"])


@router.delete("/{email_id}")
async def clear_cache(email_id: str, user: dict = Depends(auth.get_current_user)):
    """清除指定邮箱的缓存（包括内存和SQLite缓存，普通用户只能清除自己的缓存）"""
    # 检查账户访问权限（普通用户只能清除自己绑定的账户缓存）
    if not auth.check_account_access(user, email_id):
        raise HTTPException(status_code=403, detail=f"无权清除账户 {email_id} 的缓存")
    
    # 检查缓存管理权限
    auth.require_permission(user, Permission.MANAGE_CACHE)
    
    # 清除内存LRU缓存
    cache_service.clear_email_cache(email_id)
    cache_service.clear_cached_access_token(email_id)
    # 清除 SQLite 缓存
    db.clear_email_cache_db(email_id)
    logger.info(f"Cache cleared (LRU memory + SQLite) for {email_id} by {user['username']}")
    return {"message": f"Cache cleared for {email_id}"}


@router.delete("")
async def clear_all_cache(user: dict = Depends(auth.get_current_user)):
    """清除所有缓存（仅管理员可用）"""
    # 仅管理员可以清除所有缓存
    auth.require_admin(user)
    
    # 清除所有LRU缓存
    cache_service.clear_all_cache()
    # 清除SQLite缓存（通过数据库操作）
    logger.info(f"All cache cleared by {user['username']}")
    return {"message": "All cache cleared"}

