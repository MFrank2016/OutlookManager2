"""
缓存管理模块

使用 cachetools 的 LRU 缓存算法优化内存缓存
提供邮件列表、邮件详情、access_token 的统一缓存管理
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from cachetools import LRUCache, TTLCache
from cachetools.keys import hashkey

from config import CACHE_EXPIRE_TIME
from logger_config import logger

# ============================================================================
# LRU 缓存配置
# ============================================================================

# 邮件列表缓存：最大1000个条目，每个条目缓存5分钟
EMAIL_LIST_CACHE_SIZE = 1000
EMAIL_LIST_CACHE_TTL = 300  # 5分钟

# 邮件详情缓存：最大500个条目，不过期（设置为 None 表示永不过期）
EMAIL_DETAIL_CACHE_SIZE = 500
EMAIL_DETAIL_CACHE_TTL = None  # 不过期

# Access Token 缓存：最大200个条目，每个条目缓存24小时
ACCESS_TOKEN_CACHE_SIZE = 200
ACCESS_TOKEN_CACHE_TTL = 86400  # 24小时 = 86400秒

# 分享页邮件列表缓存：最大500个条目，每个条目缓存10秒
SHARE_EMAIL_LIST_CACHE_SIZE = 100
SHARE_EMAIL_LIST_CACHE_TTL = 10  # 10秒

# ============================================================================
# LRU 缓存实例
# ============================================================================

# 使用 TTLCache（带过期时间的 LRU 缓存）
email_list_cache: TTLCache = TTLCache(maxsize=EMAIL_LIST_CACHE_SIZE, ttl=EMAIL_LIST_CACHE_TTL)
# 邮件详情缓存使用 LRUCache（不过期，只受最大条目数限制）
email_detail_cache: LRUCache = LRUCache(maxsize=EMAIL_DETAIL_CACHE_SIZE)
access_token_cache: TTLCache = TTLCache(maxsize=ACCESS_TOKEN_CACHE_SIZE, ttl=ACCESS_TOKEN_CACHE_TTL)
# 分享页邮件列表缓存（10秒TTL）
share_email_list_cache: TTLCache = TTLCache(maxsize=SHARE_EMAIL_LIST_CACHE_SIZE, ttl=SHARE_EMAIL_LIST_CACHE_TTL)

# ============================================================================
# 缓存键生成函数
# ============================================================================

def get_email_list_cache_key(
    email: str, 
    folder: str, 
    page: int, 
    page_size: int,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Tuple:
    """
    生成邮件列表缓存键
    
    Args:
        email: 邮箱地址
        folder: 文件夹名称
        page: 页码
        page_size: 每页大小
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        缓存键元组
    """
    return hashkey(
        "email_list",
        email,
        folder,
        page,
        page_size,
        sender_search or "",
        subject_search or "",
        sort_by,
        sort_order,
        start_time or "",
        end_time or ""
    )


def get_email_detail_cache_key(email: str, message_id: str) -> Tuple:
    """
    生成邮件详情缓存键
    
    Args:
        email: 邮箱地址
        message_id: 邮件ID
        
    Returns:
        缓存键元组
    """
    return hashkey("email_detail", email, message_id)


def get_access_token_cache_key(email: str) -> Tuple:
    """
    生成 Access Token 缓存键
    
    Args:
        email: 邮箱地址
        
    Returns:
        缓存键元组
    """
    return hashkey("access_token", email)


def get_share_email_list_cache_key(
    token: str,
    page: int,
    page_size: int
) -> Tuple:
    """
    生成分享页邮件列表缓存键
    
    Args:
        token: 分享码
        page: 页码
        page_size: 每页大小
        
    Returns:
        缓存键元组
    """
    return hashkey("share_email_list", token, page, page_size)

# ============================================================================
# 邮件列表缓存操作
# ============================================================================

def get_cached_email_list(
    email: str,
    folder: str,
    page: int,
    page_size: int,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    force_refresh: bool = False
) -> Optional[Dict[str, Any]]:
    """
    获取缓存的邮件列表
    
    Args:
        email: 邮箱地址
        folder: 文件夹名称
        page: 页码
        page_size: 每页大小
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间
        end_time: 结束时间
        force_refresh: 是否强制刷新缓存
        
    Returns:
        缓存的数据或None
    """
    if force_refresh:
        cache_key = get_email_list_cache_key(
            email, folder, page, page_size,
            sender_search, subject_search, sort_by, sort_order,
            start_time, end_time
        )
        if cache_key in email_list_cache:
            del email_list_cache[cache_key]
            logger.debug(f"Force refresh: removed email list cache for {email}:{folder}:{page}")
        return None
    
    cache_key = get_email_list_cache_key(
        email, folder, page, page_size,
        sender_search, subject_search, sort_by, sort_order,
        start_time, end_time
    )
    
    if cache_key in email_list_cache:
        cached_data = email_list_cache[cache_key]
        logger.debug(f"Cache hit for email list: {email}:{folder}:{page}")
        return cached_data
    
    return None


def set_cached_email_list(
    email: str,
    folder: str,
    page: int,
    page_size: int,
    data: Dict[str, Any],
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> None:
    """
    设置邮件列表缓存
    
    Args:
        email: 邮箱地址
        folder: 文件夹名称
        page: 页码
        page_size: 每页大小
        data: 要缓存的数据
        sender_search: 发件人搜索
        subject_search: 主题搜索
        sort_by: 排序字段
        sort_order: 排序方向
        start_time: 开始时间
        end_time: 结束时间
    """
    cache_key = get_email_list_cache_key(
        email, folder, page, page_size,
        sender_search, subject_search, sort_by, sort_order,
        start_time, end_time
    )
    email_list_cache[cache_key] = data
    logger.debug(f"Cache set for email list: {email}:{folder}:{page} (cache size: {len(email_list_cache)})")


# ============================================================================
# 邮件详情缓存操作
# ============================================================================

def get_cached_email_detail(email: str, message_id: str) -> Optional[Dict[str, Any]]:
    """
    获取缓存的邮件详情
    
    Args:
        email: 邮箱地址
        message_id: 邮件ID
        
    Returns:
        缓存的数据或None
    """
    cache_key = get_email_detail_cache_key(email, message_id)
    
    if cache_key in email_detail_cache:
        cached_data = email_detail_cache[cache_key]
        logger.debug(f"Cache hit for email detail: {email}:{message_id}")
        return cached_data
    
    return None


def set_cached_email_detail(email: str, message_id: str, data: Dict[str, Any]) -> None:
    """
    设置邮件详情缓存
    
    Args:
        email: 邮箱地址
        message_id: 邮件ID
        data: 要缓存的数据
    """
    cache_key = get_email_detail_cache_key(email, message_id)
    email_detail_cache[cache_key] = data
    logger.debug(f"Cache set for email detail: {email}:{message_id} (cache size: {len(email_detail_cache)})")


# ============================================================================
# Access Token 缓存操作
# ============================================================================

def get_cached_access_token(email: str) -> Optional[str]:
    """
    获取缓存的 Access Token
    
    Args:
        email: 邮箱地址
        
    Returns:
        Access Token 或 None
    """
    cache_key = get_access_token_cache_key(email)
    
    if cache_key in access_token_cache:
        token_data = access_token_cache[cache_key]
        # token_data 可能是字符串或字典
        if isinstance(token_data, str):
            logger.debug(f"Cache hit for access token: {email}")
            return token_data
        elif isinstance(token_data, dict):
            logger.debug(f"Cache hit for access token: {email}")
            return token_data.get('access_token')
    
    return None


def set_cached_access_token(email: str, access_token: str, expires_at: Optional[str] = None) -> None:
    """
    设置 Access Token 缓存
    
    Args:
        email: 邮箱地址
        access_token: Access Token
        expires_at: 过期时间（可选）
    """
    cache_key = get_access_token_cache_key(email)
    # 存储 token 和过期时间信息
    token_data = {
        'access_token': access_token,
        'expires_at': expires_at,
        'cached_at': datetime.now().isoformat()
    }
    access_token_cache[cache_key] = token_data
    logger.debug(f"Cache set for access token: {email} (cache size: {len(access_token_cache)})")


def clear_cached_access_token(email: str) -> None:
    """
    清除指定邮箱的 Access Token 缓存
    
    Args:
        email: 邮箱地址
    """
    cache_key = get_access_token_cache_key(email)
    if cache_key in access_token_cache:
        del access_token_cache[cache_key]
        logger.debug(f"Cleared access token cache for {email}")


# ============================================================================
# 缓存清理操作
# ============================================================================

def clear_email_cache(email: str = None) -> None:
    """
    清除邮件缓存
    
    Args:
        email: 指定邮箱地址，如果为None则清除所有缓存
    """
    if email:
        # 清除特定邮箱的缓存
        keys_to_delete = []
        for key in list(email_list_cache.keys()):
            if len(key) > 1 and key[1] == email:  # key[1] 是 email
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del email_list_cache[key]
        
        keys_to_delete = []
        for key in list(email_detail_cache.keys()):
            if len(key) > 1 and key[1] == email:  # key[1] 是 email
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del email_detail_cache[key]
        
        logger.info(f"Cleared email cache for {email} "
                   f"({len(keys_to_delete)} list entries, {len(keys_to_delete)} detail entries)")
    else:
        # 清除所有缓存
        list_count = len(email_list_cache)
        detail_count = len(email_detail_cache)
        email_list_cache.clear()
        email_detail_cache.clear()
        logger.info(f"Cleared all email cache ({list_count} list entries, {detail_count} detail entries)")


def clear_all_cache() -> None:
    """
    清除所有缓存（包括邮件、access token和分享页缓存）
    """
    list_count = len(email_list_cache)
    detail_count = len(email_detail_cache)
    token_count = len(access_token_cache)
    share_count = len(share_email_list_cache)
    
    email_list_cache.clear()
    email_detail_cache.clear()
    access_token_cache.clear()
    share_email_list_cache.clear()
    
    logger.info(f"Cleared all caches ({list_count} list, {detail_count} detail, {token_count} token, {share_count} share entries)")


# ============================================================================
# 分享页邮件列表缓存操作
# ============================================================================

def get_cached_share_email_list(
    token: str,
    page: int,
    page_size: int
) -> Optional[Dict[str, Any]]:
    """
    获取缓存的分享页邮件列表
    
    Args:
        token: 分享码
        page: 页码
        page_size: 每页大小
        
    Returns:
        缓存的数据或None
    """
    cache_key = get_share_email_list_cache_key(token, page, page_size)
    
    if cache_key in share_email_list_cache:
        cached_data = share_email_list_cache[cache_key]
        logger.debug(f"Cache hit for share email list: {token}:{page}")
        return cached_data
    
    return None


def set_cached_share_email_list(
    token: str,
    page: int,
    page_size: int,
    data: Dict[str, Any]
) -> None:
    """
    设置分享页邮件列表缓存
    
    Args:
        token: 分享码
        page: 页码
        page_size: 每页大小
        data: 要缓存的数据
    """
    cache_key = get_share_email_list_cache_key(token, page, page_size)
    share_email_list_cache[cache_key] = data
    logger.debug(f"Cache set for share email list: {token}:{page} (cache size: {len(share_email_list_cache)})")


def clear_share_email_cache(token: str = None) -> None:
    """
    清除分享页邮件缓存
    
    Args:
        token: 指定分享码，如果为None则清除所有缓存
    """
    if token:
        # 清除特定token的缓存
        keys_to_delete = []
        for key in list(share_email_list_cache.keys()):
            if len(key) > 1 and key[1] == token:  # key[1] 是 token
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del share_email_list_cache[key]
        
        logger.info(f"Cleared share email cache for token {token} ({len(keys_to_delete)} entries)")
    else:
        # 清除所有缓存
        cache_count = len(share_email_list_cache)
        share_email_list_cache.clear()
        logger.info(f"Cleared all share email cache ({cache_count} entries)")


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        缓存统计信息字典
    """
    return {
        'email_list_cache': {
            'size': len(email_list_cache),
            'max_size': EMAIL_LIST_CACHE_SIZE,
            'ttl': EMAIL_LIST_CACHE_TTL
        },
        'email_detail_cache': {
            'size': len(email_detail_cache),
            'max_size': EMAIL_DETAIL_CACHE_SIZE,
            'ttl': EMAIL_DETAIL_CACHE_TTL
        },
        'access_token_cache': {
            'size': len(access_token_cache),
            'max_size': ACCESS_TOKEN_CACHE_SIZE,
            'ttl': ACCESS_TOKEN_CACHE_TTL
        },
        'share_email_list_cache': {
            'size': len(share_email_list_cache),
            'max_size': SHARE_EMAIL_LIST_CACHE_SIZE,
            'ttl': SHARE_EMAIL_LIST_CACHE_TTL
        }
    }
