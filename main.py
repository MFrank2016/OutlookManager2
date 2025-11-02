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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 导入配置和日志
from config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    AUTO_SYNC_EMAILS_ENABLED,
    EMAIL_SYNC_INTERVAL,
    EMAIL_SYNC_PAGE_SIZE,
    HOST,
    PORT,
)
from logger_config import setup_logger

# 导入自定义模块
import admin_api
import auth
import database as db
from account_service import get_account_credentials
from email_service import list_emails
from imap_pool import imap_pool
from models import AccountCredentials
from oauth_service import refresh_account_token
from routes import main_router

# 初始化日志系统
logger = setup_logger()

# 初始化Jinja2模板
templates = Jinja2Templates(directory="static/templates")


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


async def email_sync_background_task():
    """
    后台邮件同步任务

    定期自动获取所有邮箱的邮件数据并存入SQLite缓存
    默认每5分钟运行一次
    """
    logger.info("Email sync background task started")
    logger.info(f"Sync interval: {EMAIL_SYNC_INTERVAL} seconds ({EMAIL_SYNC_INTERVAL // 60} minutes)")
    
    # 首次启动延迟30秒，等待服务完全启动
    await asyncio.sleep(30)

    while True:
        try:
            logger.info("=== Running scheduled email sync ===")

            # 获取所有账户
            accounts, total = db.get_all_accounts_db(page=1, page_size=1000)
            
            if total == 0:
                logger.info("No accounts found, skipping sync")
                await asyncio.sleep(EMAIL_SYNC_INTERVAL)
                continue

            logger.info(f"Found {total} accounts to sync")

            sync_count = 0
            error_count = 0

            for account in accounts:
                email = account.get("email")
                try:
                    logger.info(f"[{email}] Starting email sync...")

                    # 获取账户凭证
                    credentials = await get_account_credentials(email)

                    # 获取邮件列表（包含收件箱和垃圾邮件）
                    result = await list_emails(
                        credentials=credentials,
                        folder="all",  # 获取所有文件夹
                        page=1,
                        page_size=EMAIL_SYNC_PAGE_SIZE,
                        force_refresh=True,  # 强制从服务器获取最新数据
                        sender_search=None,
                        subject_search=None,
                        sort_by="date",
                        sort_order="desc",
                    )

                    sync_count += 1
                    logger.info(
                        f"[{email}] Successfully synced {len(result.emails)} emails "
                        f"(total: {result.total_emails})"
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(f"[{email}] Failed to sync emails: {e}")
                    # 继续处理下一个账户，不中断整个流程

                # 每个账户之间间隔2秒，避免过于频繁
                await asyncio.sleep(2)

            logger.info(
                f"=== Email sync completed. Success: {sync_count}/{total}, "
                f"Errors: {error_count} ==="
            )

            # 等待下一次同步
            await asyncio.sleep(EMAIL_SYNC_INTERVAL)

        except asyncio.CancelledError:
            logger.info("Email sync task cancelled")
            raise

        except Exception as e:
            logger.error(f"Error in email sync background task: {e}")
            # 出错后等待一段时间再重试
            await asyncio.sleep(60)


# ============================================================================
# 缓存预热
# ============================================================================


async def warmup_cache():
    """
    缓存预热：启动时预加载活跃账户的邮件
    """
    from config import (
        CACHE_WARMUP_ENABLED,
        CACHE_WARMUP_ACCOUNTS,
        CACHE_WARMUP_EMAILS_PER_ACCOUNT
    )
    
    if not CACHE_WARMUP_ENABLED:
        logger.info("Cache warmup is disabled")
        return
    
    try:
        logger.info("Starting cache warmup...")
        
        # 获取所有账户
        accounts_data, total_accounts = db.get_all_accounts_db(page=1, page_size=1000)
        if not accounts_data:
            logger.info("No accounts found for cache warmup")
            return
        
        # 按最后刷新时间排序，选择最活跃的账户
        active_accounts = sorted(
            accounts_data,
            key=lambda x: x.get('last_refresh_time') or '',
            reverse=True
        )[:CACHE_WARMUP_ACCOUNTS]
        
        logger.info(f"Warming up cache for {len(active_accounts)} accounts")
        
        for account in active_accounts:
            try:
                email_id = account['email']
                logger.info(f"Warming up cache for account: {email_id}")
                
                # 预加载收件箱邮件（不强制刷新，优先使用缓存）
                from email_service import list_emails
                result = await list_emails(
                    email_id=email_id,
                    page=1,
                    page_size=CACHE_WARMUP_EMAILS_PER_ACCOUNT,
                    folder='INBOX',
                    force_refresh=False
                )
                
                logger.info(f"Warmed up {len(result.get('emails', []))} emails for {email_id}")
                
            except Exception as e:
                logger.warning(f"Failed to warmup cache for {account['email']}: {e}")
                continue
        
        logger.info("Cache warmup completed")
        
    except Exception as e:
        logger.error(f"Error during cache warmup: {e}")


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
    
    # 启动后台邮件同步任务
    email_sync_task = None
    if AUTO_SYNC_EMAILS_ENABLED:
        email_sync_task = asyncio.create_task(email_sync_background_task())
        logger.info("Email sync background task scheduled")
        logger.info(f"Auto sync interval: {EMAIL_SYNC_INTERVAL} seconds ({EMAIL_SYNC_INTERVAL // 60} minutes)")
    else:
        logger.info("Email auto sync is disabled")
    
    # 启动缓存预热（异步，不阻塞启动）
    asyncio.create_task(warmup_cache())

    yield

    # 应用关闭
    logger.info(f"Shutting down {APP_TITLE}...")

    # 取消后台任务（带超时）
    tasks_to_cancel = [refresh_task]
    if email_sync_task:
        tasks_to_cancel.append(email_sync_task)
    
    for task in tasks_to_cancel:
        task.cancel()
    
    try:
        await asyncio.wait_for(asyncio.gather(*tasks_to_cancel, return_exceptions=True), timeout=3.0)
        logger.info("All background tasks cancelled")
    except asyncio.TimeoutError:
        logger.warning("Background tasks cancellation timeout, forcing shutdown")
    except Exception as e:
        logger.error(f"Error cancelling background tasks: {e}")

    # 关闭IMAP连接池（使用线程，防止阻塞）
    logger.info("Closing IMAP connection pool...")
    try:
        # 在executor中运行，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, imap_pool.close_all_connections),
            timeout=5.0  # 5秒超时
        )
        logger.info("IMAP connection pool closed successfully")
    except asyncio.TimeoutError:
        logger.warning("IMAP connection pool close timeout, forcing shutdown")
    except Exception as e:
        logger.error(f"Error closing IMAP connection pool: {e}")
    
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
async def root(request: Request):
    """根路径 - 返回前端页面（使用Jinja2模板渲染）"""
    try:
        # 尝试使用Jinja2模板渲染
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        # 如果模板渲染失败，回退到静态文件
        logger.warning(f"Template rendering failed, falling back to static file: {e}")
    return FileResponse("static/index.html")


@app.get("/favicon.ico")
async def favicon():
    """返回网站图标"""
    import os
    favicon_path = "static/favicon.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/png")
    # 如果没有favicon文件，返回204 No Content
    from fastapi import Response
    return Response(status_code=204)


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
