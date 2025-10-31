"""
Outlook邮件管理系统 - 主应用模块

基于FastAPI和IMAP协议的高性能邮件管理系统
支持多账户管理、邮件查看、搜索过滤等功能

Author: Outlook Manager Team
Version: 2.0.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 导入配置和日志
from config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, HOST, PORT
from logger_config import setup_logger

# 导入自定义模块
import admin_api
import auth
import database as db
from imap_pool import imap_pool
from models import AccountCredentials
from oauth_service import refresh_account_token
from routes import main_router

# 初始化日志系统
logger = setup_logger()


# ============================================================================
# 后台任务
# ============================================================================


async def token_refresh_background_task():
    """后台定时任务：每天刷新所有账户的token"""
    logger.info("Token refresh background task started")

    while True:
        try:
            logger.info("Starting scheduled token refresh for all accounts...")

            # 从数据库读取所有账户
            accounts_data, _ = db.get_all_accounts_db(page=1, page_size=1000)

            if not accounts_data:
                logger.info("No accounts to refresh")
                await asyncio.sleep(24 * 60 * 60)  # 等待1天
                continue

            # 逐个刷新token
            refresh_count = 0
            failed_count = 0

            for account_data in accounts_data:
                email_id = account_data["email"]
                try:
                    # 构建凭证对象
                    credentials = AccountCredentials(
                        email=email_id,
                        refresh_token=account_data["refresh_token"],
                        client_id=account_data["client_id"],
                        tags=account_data.get("tags", []),
                        last_refresh_time=account_data.get("last_refresh_time"),
                        next_refresh_time=account_data.get("next_refresh_time"),
                        refresh_status=account_data.get("refresh_status", "pending"),
                        refresh_error=account_data.get("refresh_error"),
                    )

                    # 刷新token
                    result = await refresh_account_token(credentials)

                    # 更新账户信息
                    current_time = datetime.now().isoformat()
                    next_refresh = datetime.now() + timedelta(days=3)

                    if result["success"]:
                        db.update_account(
                            email_id,
                            refresh_token=result["new_refresh_token"],
                            last_refresh_time=current_time,
                            next_refresh_time=next_refresh.isoformat(),
                            refresh_status="success",
                            refresh_error=None,
                        )
                        refresh_count += 1
                        logger.info(f"Successfully refreshed token for {email_id}")
                    else:
                        db.update_account(
                            email_id,
                            refresh_status="failed",
                            refresh_error=result.get("error", "Unknown error"),
                        )
                        failed_count += 1
                        logger.error(
                            f"Failed to refresh token for {email_id}: {result.get('error')}"
                        )

                except Exception as e:
                    logger.error(f"Error refreshing token for {email_id}: {e}")
                    db.update_account(
                        email_id, refresh_status="failed", refresh_error=str(e)
                    )
                    failed_count += 1

            logger.info(
                f"Token refresh completed: {refresh_count} succeeded, {failed_count} failed"
            )
            # 等待1天
            await asyncio.sleep(24 * 60 * 60)  # 1天 = 86400秒
        except Exception as e:
            logger.error(f"Error in token refresh background task: {e}")
            await asyncio.sleep(60 * 60)  # 出错后等待1小时再重试


# ============================================================================
# FastAPI应用生命周期管理
# ============================================================================


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI应用生命周期管理

    处理应用启动和关闭时的资源管理
    """
    # 应用启动
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}...")

    # 初始化数据库
    logger.info("Initializing database...")
    db.init_database()
    logger.info("Database initialized successfully")

    # 初始化默认管理员（如果不存在）
    auth.init_default_admin()
    
    # 初始化API Key（如果不存在）
    api_key = db.init_default_api_key()
    logger.info("API Key initialized")
    print(f"系统API Key: {api_key}")
    print(f"使用方式: 在请求头中添加 X-API-Key: {api_key}")

    # 启动后台Token刷新任务
    refresh_task = asyncio.create_task(token_refresh_background_task())
    logger.info("Token refresh background task scheduled")

    yield

    # 应用关闭
    logger.info(f"Shutting down {APP_TITLE}...")

    # 取消后台任务
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        logger.info("Token refresh background task cancelled")

    logger.info("Closing IMAP connection pool...")
    imap_pool.close_all_connections()
    logger.info("Application shutdown complete.")


# ============================================================================
# FastAPI应用初始化
# ============================================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册管理面板路由
app.include_router(admin_api.router)

# 注册主路由（包含所有业务路由）
app.include_router(main_router)


# ============================================================================
# 基础路由
# ============================================================================


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    return FileResponse("static/index.html")


@app.get("/api")
async def api_status():
    """API状态检查"""
    return {
        "message": "Outlook邮件API服务正在运行",
        "version": APP_VERSION,
        "endpoints": {
            "get_accounts": "GET /accounts",
            "register_account": "POST /accounts",
            "get_emails": "GET /emails/{email_id}?refresh=true",
            "get_dual_view_emails": "GET /emails/{email_id}/dual-view",
            "get_email_detail": "GET /emails/{email_id}/{message_id}",
            "refresh_token": "POST /accounts/{email_id}/refresh-token",
            "clear_cache": "DELETE /cache/{email_id}",
            "clear_all_cache": "DELETE /cache",
        },
    }


# ============================================================================
# 启动配置
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {APP_TITLE} on {HOST}:{PORT}")
    logger.info(f"Access the web interface at: http://localhost:{PORT}")
    logger.info(f"Access the API documentation at: http://localhost:{PORT}/docs")

    uvicorn.run(app, host=HOST, port=PORT, log_level="info", access_log=True)
