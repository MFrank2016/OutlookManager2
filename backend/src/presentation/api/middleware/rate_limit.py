"""
速率限制中间件

基于IP和用户的请求速率限制
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, requests_per_minute: int = None):
        """
        初始化速率限制中间件
        
        Args:
            app: FastAPI应用
            requests_per_minute: 每分钟最大请求数
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.API_RATE_LIMIT_REQUESTS
        self.window_size = 60  # 时间窗口：60秒
        
        # 存储请求记录：{identifier: [(timestamp, count), ...]}
        self._request_records: Dict[str, list] = defaultdict(list)
        
        # 上次清理时间
        self._last_cleanup = time.time()
        
        logger.info(
            f"Rate limit initialized: {self.requests_per_minute} requests per minute"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> JSONResponse:
        """处理请求并检查速率限制"""
        
        # 如果速率限制未启用，直接通过
        if not settings.API_RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # 跳过某些路径（如健康检查）
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)
        
        # 获取客户端标识（IP地址）
        identifier = self._get_identifier(request)
        
        # 检查速率限制
        if not self._check_rate_limit(identifier):
            logger.warning(
                f"Rate limit exceeded for {identifier}",
                extra={"ip": identifier, "limit": self.requests_per_minute}
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {
                        "limit": self.requests_per_minute,
                        "window": f"{self.window_size}s"
                    }
                },
                headers={
                    "Retry-After": "60"
                }
            )
        
        # 记录请求
        self._record_request(identifier)
        
        # 定期清理过期记录
        self._cleanup_if_needed()
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制相关的响应头
        remaining = self._get_remaining_requests(identifier)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_size)
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """
        获取客户端标识
        
        优先使用X-Forwarded-For头，否则使用request.client.host
        """
        # 检查是否有代理转发的真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        # 使用直接连接的IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """
        检查是否超过速率限制
        
        Args:
            identifier: 客户端标识
            
        Returns:
            bool: True表示未超限，False表示超限
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        # 获取该标识的请求记录
        records = self._request_records.get(identifier, [])
        
        # 过滤出时间窗口内的请求
        recent_requests = [ts for ts in records if ts > cutoff_time]
        
        # 检查是否超限
        return len(recent_requests) < self.requests_per_minute
    
    def _record_request(self, identifier: str) -> None:
        """记录请求"""
        current_time = time.time()
        self._request_records[identifier].append(current_time)
    
    def _get_remaining_requests(self, identifier: str) -> int:
        """获取剩余可用请求数"""
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        records = self._request_records.get(identifier, [])
        recent_requests = [ts for ts in records if ts > cutoff_time]
        
        remaining = max(0, self.requests_per_minute - len(recent_requests))
        return remaining
    
    def _cleanup_if_needed(self) -> None:
        """定期清理过期记录"""
        current_time = time.time()
        
        # 每5分钟清理一次
        if current_time - self._last_cleanup < 300:
            return
        
        cutoff_time = current_time - self.window_size
        
        # 清理所有过期记录
        for identifier in list(self._request_records.keys()):
            records = self._request_records[identifier]
            # 保留窗口内的记录
            recent = [ts for ts in records if ts > cutoff_time]
            
            if recent:
                self._request_records[identifier] = recent
            else:
                # 如果没有最近的记录，删除该标识
                del self._request_records[identifier]
        
        self._last_cleanup = current_time
        logger.debug(f"Rate limit records cleaned up. Active identifiers: {len(self._request_records)}")
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """
        判断是否应跳过速率限制
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否跳过
        """
        # 跳过的路径列表
        skip_paths = [
            "/health",
            "/api/docs",
            "/api/redoc",
            "/openapi.json"
        ]
        
        return path in skip_paths

