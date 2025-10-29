"""
错误处理中间件

统一处理应用中的异常
"""

import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.constants import ERROR_CODE_HTTP_STATUS, ErrorCode
from src.domain.exceptions import DomainException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ):
        """处理请求并捕获异常"""
        try:
            response = await call_next(request)
            return response
            
        except DomainException as e:
            # 领域异常 - 转换为HTTP响应
            http_status = ERROR_CODE_HTTP_STATUS.get(
                e.code,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            logger.warning(
                f"Domain exception: {e.code} - {e.message}",
                extra={"details": e.details}
            )
            
            return JSONResponse(
                status_code=http_status,
                content={
                    "success": False,
                    "error_code": e.code.value,
                    "message": e.message,
                    "details": e.details
                }
            )
            
        except Exception as e:
            # 未预期的异常
            logger.error(
                f"Unexpected error: {str(e)}",
                exc_info=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error_code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "Internal server error",
                    "details": {}
                }
            )

