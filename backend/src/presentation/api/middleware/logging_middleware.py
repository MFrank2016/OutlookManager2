"""
请求日志中间件

记录所有HTTP请求和响应
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """处理请求并记录日志"""
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # 记录请求开始
        logger.info(
            f"Request started: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client": client_host,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # 在开发环境记录请求体
        if settings.DEBUG and method in ["POST", "PUT", "PATCH"]:
            try:
                # 注意：读取body后需要重新设置，但FastAPI会处理这个
                body = await request.body()
                if body:
                    logger.debug(
                        f"Request body: {body.decode('utf-8', errors='replace')[:500]}",
                        extra={"request_id": request_id}
                    )
            except Exception as e:
                logger.warning(f"Failed to log request body: {str(e)}")
        
        # 将request_id添加到request.state，以便路由中使用
        request.state.request_id = request_id
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加自定义响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            # 记录响应
            logger.info(
                f"Request completed: {method} {url} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.4f}s"
                }
            )
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            
            logger.error(
                f"Request failed: {method} {url} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "process_time": f"{process_time:.4f}s"
                },
                exc_info=True
            )
            
            # 重新抛出异常，让错误处理中间件处理
            raise

