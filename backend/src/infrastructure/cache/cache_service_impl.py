"""
缓存服务实现

支持内存缓存和Redis缓存
"""

import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from src.application.interfaces import ICacheService
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MemoryCacheService(ICacheService):
    """内存缓存服务实现（使用cachetools）"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self._cache = TTLCache(maxsize=max_size, ttl=default_ttl)
        self._default_ttl = default_ttl
        logger.info(f"Memory cache initialized: max_size={max_size}, ttl={default_ttl}")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = self._cache.get(key)
            if value is not None:
                # 反序列化
                return json.loads(value) if isinstance(value, str) else value
            return None
        except Exception as e:
            logger.warning(f"Failed to get cache key {key}: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            # 序列化值
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            self._cache[key] = serialized_value
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self._cache
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        try:
            # 简单实现：遍历所有键
            import fnmatch
            
            keys_to_delete = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            return len(keys_to_delete)
        except Exception as e:
            logger.warning(f"Failed to clear pattern {pattern}: {str(e)}")
            return 0
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余有效期（内存缓存不支持精确TTL查询）"""
        if key in self._cache:
            return self._default_ttl  # 返回默认TTL
        return None


class RedisCacheService(ICacheService):
    """Redis缓存服务实现（占位）"""
    
    def __init__(self, redis_url: str, default_ttl: int = 60):
        """
        初始化Redis缓存
        
        Args:
            redis_url: Redis连接URL
            default_ttl: 默认过期时间（秒）
        """
        # 注意：这是一个占位实现
        # 实际需要使用aioredis库
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        logger.warning("Redis cache not fully implemented, using memory cache fallback")
        self._fallback = MemoryCacheService(default_ttl=default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        return await self._fallback.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        return await self._fallback.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self._fallback.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self._fallback.exists(key)
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        return await self._fallback.clear_pattern(pattern)
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余有效期"""
        return await self._fallback.get_ttl(key)


def get_cache_service() -> ICacheService:
    """
    获取缓存服务实例
    
    Returns:
        ICacheService: 缓存服务实例
    """
    if settings.REDIS_URL:
        return RedisCacheService(
            redis_url=settings.REDIS_URL,
            default_ttl=settings.CACHE_TTL
        )
    else:
        return MemoryCacheService(default_ttl=settings.CACHE_TTL)

