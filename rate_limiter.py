"""
通用限流模块 - 令牌桶算法实现

提供基于令牌桶算法的限流功能，支持自动清理过期数据
"""

import time
import threading
from typing import Dict

from logger_config import logger


class TokenBucket:
    """
    令牌桶限流器
    
    令牌桶算法：
    - 桶容量：max_tokens
    - 令牌生成速率：refill_rate tokens/second
    - 每次请求消耗1个令牌
    - 如果桶中有令牌，允许请求；否则拒绝请求
    """
    
    def __init__(self, max_tokens: int, refill_rate: float, cleanup_interval: int = 600):
        """
        初始化令牌桶
        
        Args:
            max_tokens: 桶的最大容量（令牌数）
            refill_rate: 令牌生成速率（每秒生成的令牌数）
            cleanup_interval: 清理过期数据的间隔（秒），默认600秒（10分钟）
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.cleanup_interval = cleanup_interval
        
        # 存储每个key的令牌桶状态
        # key -> {"tokens": float, "last_refill": float}
        self.buckets: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.last_cleanup = time.time()
    
    def _refill_tokens(self, key: str, now: float) -> float:
        """
        为指定key的令牌桶补充令牌
        
        Args:
            key: 限流的key
            now: 当前时间戳
            
        Returns:
            补充后的令牌数量
        """
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.max_tokens,
                "last_refill": now
            }
            return self.max_tokens
        
        bucket = self.buckets[key]
        elapsed = now - bucket["last_refill"]
        
        # 计算应该补充的令牌数
        tokens_to_add = elapsed * self.refill_rate
        new_tokens = min(self.max_tokens, bucket["tokens"] + tokens_to_add)
        
        bucket["tokens"] = new_tokens
        bucket["last_refill"] = now
        
        return new_tokens
    
    def _cleanup_old_buckets(self, now: float):
        """
        清理超过清理间隔的旧数据
        
        Args:
            now: 当前时间戳
        """
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        with self.lock:
            # 再次检查，避免重复清理
            if now - self.last_cleanup < self.cleanup_interval:
                return
            
            keys_to_remove = []
            for key, bucket in self.buckets.items():
                # 如果超过清理间隔没有使用，删除该bucket
                if now - bucket["last_refill"] > self.cleanup_interval:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.buckets[key]
            
            self.last_cleanup = now
            
            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")
    
    def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        尝试获取令牌
        
        Args:
            key: 限流的key
            tokens: 需要消耗的令牌数，默认1
            
        Returns:
            True: 允许请求
            False: 拒绝请求（限流）
        """
        now = time.time()
        
        with self.lock:
            # 定期清理旧数据
            self._cleanup_old_buckets(now)
            
            # 补充令牌
            current_tokens = self._refill_tokens(key, now)
            
            # 检查是否有足够的令牌
            if current_tokens >= tokens:
                self.buckets[key]["tokens"] -= tokens
                return True
            else:
                return False
    
    def get_remaining_tokens(self, key: str) -> float:
        """
        获取指定key的剩余令牌数
        
        Args:
            key: 限流的key
            
        Returns:
            剩余令牌数
        """
        now = time.time()
        
        with self.lock:
            self._cleanup_old_buckets(now)
            return self._refill_tokens(key, now)


# 全局限流器实例
# 每分钟30次 = 每秒0.5个令牌，桶容量30
_share_token_rate_limiter = TokenBucket(
    max_tokens=30,
    refill_rate=30.0 / 60.0,  # 每分钟30次 = 每秒0.5个令牌
    cleanup_interval=600  # 10分钟清理一次
)


def check_share_token_rate_limit(token: str) -> bool:
    """
    检查分享token的限流
    
    Args:
        token: 分享token
        
    Returns:
        True: 允许请求
        False: 拒绝请求（限流）
    """
    return _share_token_rate_limiter.acquire(token)


def get_share_token_remaining(token: str) -> float:
    """
    获取分享token的剩余请求次数
    
    Args:
        token: 分享token
        
    Returns:
        剩余令牌数（可理解为剩余请求次数）
    """
    return _share_token_rate_limiter.get_remaining_tokens(token)


def create_rate_limiter(max_tokens: int, refill_rate: float, cleanup_interval: int = 600) -> TokenBucket:
    """
    创建新的限流器实例
    
    Args:
        max_tokens: 桶的最大容量
        refill_rate: 令牌生成速率（每秒）
        cleanup_interval: 清理间隔（秒）
        
    Returns:
        TokenBucket实例
    """
    return TokenBucket(max_tokens, refill_rate, cleanup_interval)

