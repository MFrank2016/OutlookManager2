"""
缓存管理模块

提供内存缓存和SQLite缓存的统一管理接口
"""

import logging
import time

from config import CACHE_EXPIRE_TIME

# 获取日志记录器
logger = logging.getLogger(__name__)

# 内存缓存存储
email_cache = {}  # 邮件列表缓存
email_count_cache = {}  # 邮件总数缓存，用于检测新邮件


def get_cache_key(email: str, folder: str, page: int, page_size: int) -> str:
    """
    生成缓存键

    Args:
        email: 邮箱地址
        folder: 文件夹名称
        page: 页码
        page_size: 每页大小

    Returns:
        str: 缓存键
    """
    return f"{email}:{folder}:{page}:{page_size}"


def get_cached_emails(cache_key: str, force_refresh: bool = False):
    """
    获取缓存的邮件列表

    Args:
        cache_key: 缓存键
        force_refresh: 是否强制刷新缓存

    Returns:
        缓存的数据或None
    """
    if force_refresh:
        # 强制刷新，删除现有缓存
        if cache_key in email_cache:
            del email_cache[cache_key]
            logger.debug(f"Force refresh: removed cache for {cache_key}")
        return None

    if cache_key in email_cache:
        cached_data, timestamp = email_cache[cache_key]
        if time.time() - timestamp < CACHE_EXPIRE_TIME:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
        else:
            # 缓存已过期，删除
            del email_cache[cache_key]
            logger.debug(f"Cache expired for {cache_key}")

    return None


def set_cached_emails(cache_key: str, data) -> None:
    """
    设置邮件列表缓存

    Args:
        cache_key: 缓存键
        data: 要缓存的数据
    """
    email_cache[cache_key] = (data, time.time())
    logger.debug(f"Cache set for {cache_key}")


def clear_email_cache(email: str = None) -> None:
    """
    清除邮件缓存

    Args:
        email: 指定邮箱地址，如果为None则清除所有缓存
    """
    if email:
        # 清除特定邮箱的缓存
        keys_to_delete = [
            key for key in email_cache.keys() if key.startswith(f"{email}:")
        ]
        for key in keys_to_delete:
            del email_cache[key]
        logger.info(f"Cleared cache for {email} ({len(keys_to_delete)} entries)")
    else:
        # 清除所有缓存
        cache_count = len(email_cache)
        email_cache.clear()
        email_count_cache.clear()
        logger.info(f"Cleared all email cache ({cache_count} entries)")

