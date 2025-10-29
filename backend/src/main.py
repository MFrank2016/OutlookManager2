"""
FastAPI主应用入口

Outlook邮件管理系统v3.0
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.infrastructure.database.session import close_database, init_database
from src.infrastructure.logging import setup_logging
from src.presentation.api.middleware import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from src.presentation.api.v1.routers import (
    accounts_router,
    admin_router,
    auth_router,
    emails_router,
)
from src.presentation.api.v1.schemas import HealthResponse

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("Application starting...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 初始化数据库
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    logger.info("Application started successfully")
    
    yield
    
    # 关闭
    logger.info("Application shutting down...")
    
    # 关闭数据库连接
    await close_database()
    
    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于DDD架构的Outlook邮件管理系统",
    docs_url="/api/docs" if settings.API_DOCS_ENABLED else None,
    redoc_url="/api/redoc" if settings.API_DOCS_ENABLED else None,
    lifespan=lifespan
)

# ============================================================================
# 中间件配置
# ============================================================================

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 速率限制中间件（最外层）
app.add_middleware(RateLimitMiddleware)

# 日志中间件
app.add_middleware(LoggingMiddleware)

# 错误处理中间件（最内层）
app.add_middleware(ErrorHandlerMiddleware)

# ============================================================================
# 路由配置
# ============================================================================

# API v1路由
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(accounts_router, prefix=settings.API_V1_PREFIX)
app.include_router(emails_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


# ============================================================================
# 基础路由
# ============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}",
        "docs": "/api/docs" if settings.API_DOCS_ENABLED else "disabled"
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/ping", tags=["system"])
async def ping():
    """Ping端点"""
    return {"message": "pong"}


# ============================================================================
# 异常处理器
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404处理"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Resource not found",
            "path": str(request.url)
        }
    )


# ============================================================================
# 应用启动
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

