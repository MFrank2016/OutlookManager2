"""
Outlook邮件管理系统 - 主应用模块

基于FastAPI和IMAP协议的高性能邮件管理系统
支持多账户管理、邮件查看、搜索过滤等功能

Author: Outlook Manager Team
Version: 2.0.0
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, Any, Optional
from functools import partial

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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
    REFRESH_TOKEN_INTERVAL,
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


def _serialize_datetime(dt: Optional[Any]) -> Optional[str]:
    """将 datetime 对象转换为 ISO 格式字符串"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt  # 如果已经是字符串或None，直接返回

# API请求专用的线程池执行器（用于处理API请求中的同步数据库操作）
# 限制并发数为5，确保API请求能及时响应
api_requests_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="api-request")

# 后台任务专用的线程池执行器（独立于API请求的线程池）
# 限制并发数为2，避免占用过多资源
background_tasks_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bg-task")


# ============================================================================
# 后台任务
# ============================================================================


async def token_refresh_background_task():
    """后台定时任务：每天刷新所有账户的token"""
    logger.info("Token refresh background task started")

    try:
        while True:
            try:
                logger.info("Starting scheduled token refresh for all accounts...")

                # 分批获取所有账户（避免一次性加载过多数据）
                # 使用后台任务专用线程池执行同步数据库操作，避免阻塞事件循环
                page = 1
                page_size = 1000
                all_accounts = []
                loop = asyncio.get_event_loop()
                
                while True:
                    accounts_data, total = await loop.run_in_executor(
                        background_tasks_executor,
                        db.get_all_accounts_db, page, page_size
                    )
                    if not accounts_data:
                        break
                    all_accounts.extend(accounts_data)
                    logger.info(f"Loaded {len(accounts_data)} accounts from page {page}, total loaded: {len(all_accounts)}/{total}")
                    
                    # 如果已经获取了所有账户，退出循环
                    if len(all_accounts) >= total:
                        break
                    page += 1

                if not all_accounts:
                    logger.info("No accounts to refresh")
                    # 使用可中断的sleep，每10分钟检查一次取消信号
                    for _ in range(144):  # 24小时 = 144个10分钟
                        await asyncio.sleep(600)  # 10分钟
                    continue

                logger.info(f"Total accounts loaded: {len(all_accounts)}")

                # 过滤需要刷新的账户（检查7天最小刷新间隔）
                accounts_to_refresh = []
                current_time = datetime.now()
                min_refresh_interval = timedelta(days=7)  # refresh token 过期时间改为 7 天
                
                for account_data in all_accounts:
                    email_id = account_data["email"]
                    last_refresh_time_str = account_data.get("last_refresh_time")
                    
                    # 如果没有最后刷新时间，需要刷新
                    if not last_refresh_time_str:
                        accounts_to_refresh.append(account_data)
                        continue
                    
                    try:
                        # 解析最后刷新时间（处理 datetime 对象或字符串）
                        if isinstance(last_refresh_time_str, datetime):
                            last_refresh_time = last_refresh_time_str
                        else:
                            last_refresh_time = datetime.fromisoformat(last_refresh_time_str.replace('Z', '+00:00'))
                        
                        # 处理时区问题（如果时间戳没有时区信息，假设为本地时间）
                        if last_refresh_time.tzinfo is None:
                            last_refresh_time = last_refresh_time.replace(tzinfo=None)
                            current_time_local = current_time.replace(tzinfo=None)
                        else:
                            current_time_local = current_time
                        
                        # 计算距离上次刷新的时间间隔
                        time_since_refresh = current_time_local - last_refresh_time
                        
                        # 如果距离上次刷新超过7天，则需要刷新
                        if time_since_refresh >= min_refresh_interval:
                            accounts_to_refresh.append(account_data)
                        else:
                            days_remaining = (min_refresh_interval - time_since_refresh).total_seconds() / 86400
                            logger.debug(
                                f"Skipping {email_id}: last refreshed {time_since_refresh.days} days ago, "
                                f"need to wait {days_remaining:.1f} days more"
                            )
                    except (ValueError, TypeError, AttributeError) as e:
                        # 如果时间解析失败，需要刷新
                        logger.warning(f"Failed to parse last_refresh_time for {email_id}: {e}, will refresh")
                        accounts_to_refresh.append(account_data)
                
                logger.info(
                    f"Accounts to refresh: {len(accounts_to_refresh)}/{len(all_accounts)} "
                    f"(skipped {len(all_accounts) - len(accounts_to_refresh)} within 7 days interval)"
                )
                
                if not accounts_to_refresh:
                    logger.info("No accounts need token refresh (all within 7 days interval)")
                    # 等待1小时后再次检查
                    for _ in range(6):  # 1小时 = 6个10分钟
                        await asyncio.sleep(600)  # 10分钟
                    continue

                # 使用信号量限制并发数为2
                semaphore = asyncio.Semaphore(2)
                
                async def refresh_single_token(account_data: dict):
                    """刷新单个账户的token（使用信号量限制并发）"""
                    async with semaphore:
                        email_id = account_data["email"]
                        try:
                            # 构建凭证对象
                            credentials = AccountCredentials(
                                email=email_id,
                                refresh_token=account_data["refresh_token"],
                                client_id=account_data["client_id"],
                                tags=account_data.get("tags", []),
                                last_refresh_time=_serialize_datetime(account_data.get("last_refresh_time")),
                                next_refresh_time=_serialize_datetime(account_data.get("next_refresh_time")),
                                refresh_status=account_data.get("refresh_status", "pending"),
                                refresh_error=account_data.get("refresh_error"),
                                api_method=account_data.get("api_method", "imap"),  # 支持graph邮箱刷新
                            )

                            # 刷新token
                            result = await refresh_account_token(credentials)

                            # 更新账户信息
                            current_time = datetime.now().isoformat()
                            next_refresh = datetime.now() + timedelta(days=7)  # refresh token 过期时间改为 7 天

                            if result["success"]:
                                # 使用后台任务专用线程池执行同步数据库操作
                                loop = asyncio.get_event_loop()
                                # 更新 refresh token 和刷新时间
                                await loop.run_in_executor(
                                    background_tasks_executor,
                                    partial(
                                        db.update_account,
                                        email_id,
                                        refresh_token=result["new_refresh_token"],
                                        last_refresh_time=current_time,
                                        next_refresh_time=next_refresh.isoformat(),
                                        refresh_status="success",
                                        refresh_error=None,
                                    )
                                )
                                # 保存 access token 和过期时间
                                await loop.run_in_executor(
                                    background_tasks_executor,
                                    partial(
                                        db.update_account_access_token,
                                        email_id,
                                        result["new_access_token"],
                                        result["access_token_expires_at"],
                                    )
                                )
                                logger.info(f"Successfully refreshed token for {email_id}")
                                return True
                            else:
                                # 使用后台任务专用线程池执行同步数据库操作
                                loop = asyncio.get_event_loop()
                                await loop.run_in_executor(
                                    background_tasks_executor,
                                    partial(
                                        db.update_account,
                                        email_id,
                                        refresh_status="failed",
                                        refresh_error=result.get("error", "Unknown error"),
                                    )
                                )
                                logger.error(
                                    f"Failed to refresh token for {email_id}: {result.get('error')}"
                                )
                                return False

                        except Exception as e:
                            logger.error(f"Error refreshing token for {email_id}: {e}")
                            # 使用后台任务专用线程池执行同步数据库操作
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                background_tasks_executor,
                                partial(
                                    db.update_account,
                                    email_id, 
                                    refresh_status="failed", 
                                    refresh_error=str(e)
                                )
                            )
                            return False
                
                # 并发执行所有token刷新任务
                logger.info(f"Starting concurrent token refresh for {len(accounts_to_refresh)} accounts (max 2 concurrent)")
                tasks = [refresh_single_token(account_data) for account_data in accounts_to_refresh]
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    logger.info("Token refresh task cancelled, stopping...")
                    # 取消所有正在运行的任务
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    raise
                
                # 统计结果
                refresh_count = sum(1 for r in results if r is True)
                failed_count = len(results) - refresh_count
                
                logger.info(
                    f"Token refresh completed: {refresh_count} succeeded, {failed_count} failed"
                )
                # 等待刷新token间隔（使用可中断的sleep）
                sleep_interval = min(REFRESH_TOKEN_INTERVAL, 10)
                sleep_count = REFRESH_TOKEN_INTERVAL // sleep_interval
                for _ in range(sleep_count):
                    await asyncio.sleep(sleep_interval)
            except asyncio.CancelledError:
                logger.info("Token refresh background task cancelled")
                raise
            except Exception as e:
                logger.exception("Error in token refresh background task")
                # 出错后等待1小时再重试（使用可中断的sleep）
                for _ in range(6):  # 1小时 = 6个10分钟
                    await asyncio.sleep(600)  # 10分钟
    except asyncio.CancelledError:
        logger.info("Token refresh background task stopped")
        raise


async def email_sync_background_task():
    """
    后台邮件同步任务

    定期自动获取所有邮箱的邮件数据并存入SQLite缓存
    默认每5分钟运行一次
    """
    logger.info("Email sync background task started")
    logger.info(f"Sync interval: {EMAIL_SYNC_INTERVAL} seconds ({EMAIL_SYNC_INTERVAL // 60} minutes)")
    
    # 首次启动延迟30秒，等待服务完全启动
    try:
        await asyncio.sleep(100)
    except asyncio.CancelledError:
        logger.info("Email sync background task cancelled during startup")
        raise

    try:
        while True:
            try:
                logger.info("=== Running scheduled email sync ===")

                # 分批获取所有账户（避免一次性加载过多数据）
                # 使用后台任务专用线程池执行同步数据库操作，避免阻塞事件循环
                page = 1
                page_size = 1000
                all_accounts = []
                total = 0
                loop = asyncio.get_event_loop()
                
                while True:
                    accounts, total = await loop.run_in_executor(
                        background_tasks_executor,
                        db.get_all_accounts_db, page, page_size
                    )
                    if not accounts:
                        break
                    all_accounts.extend(accounts)
                    logger.info(f"Loaded {len(accounts)} accounts from page {page}, total loaded: {len(all_accounts)}/{total}")
                    
                    # 如果已经获取了所有账户，退出循环
                    if len(all_accounts) >= total:
                        break
                    page += 1
                
                if total == 0:
                    logger.info("No accounts found, skipping sync")
                    # 使用可中断的sleep
                    sleep_interval = min(EMAIL_SYNC_INTERVAL, 60)  # 最多等待60秒
                    sleep_count = EMAIL_SYNC_INTERVAL // sleep_interval
                    for _ in range(sleep_count):
                        await asyncio.sleep(sleep_interval)
                    continue

                logger.info(f"Found {total} accounts to sync")

                # 使用信号量限制并发数为2
                semaphore = asyncio.Semaphore(2)
                
                async def sync_single_account(account: dict):
                    """同步单个账户的邮件（使用信号量限制并发）"""
                    async with semaphore:
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

                            logger.info(
                                f"[{email}] Successfully synced {len(result.emails)} emails "
                                f"(total: {result.total_emails})"
                            )
                            return True

                        except Exception as e:
                            logger.error(f"[{email}] Failed to sync emails: {e}")
                            # 继续处理下一个账户，不中断整个流程
                            return False
                        finally:
                            # 每个账户之间间隔2秒，避免过于频繁
                            try:
                                await asyncio.sleep(2)
                            except asyncio.CancelledError:
                                logger.info(f"Email sync for {email} cancelled")
                                raise
                
                # 并发执行所有邮件同步任务
                logger.info(f"Starting concurrent email sync for {total} accounts (max 2 concurrent)")
                tasks = [sync_single_account(account) for account in all_accounts]
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    logger.info("Email sync task cancelled, stopping...")
                    # 取消所有正在运行的任务
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    raise
                
                # 统计结果
                sync_count = sum(1 for r in results if r is True)
                error_count = len(results) - sync_count

                logger.info(
                    f"=== Email sync completed. Success: {sync_count}/{total}, "
                    f"Errors: {error_count} ==="
                )

                # 等待下一次同步（使用可中断的sleep）
                sleep_interval = min(EMAIL_SYNC_INTERVAL, 10) 
                sleep_count = EMAIL_SYNC_INTERVAL // sleep_interval
                for _ in range(sleep_count):
                    await asyncio.sleep(sleep_interval)

            except asyncio.CancelledError:
                logger.info("Email sync task cancelled")
                raise

            except Exception as e:
                logger.exception("Error in email sync background task")
                # 出错后等待一段时间再重试（使用可中断的sleep）
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    logger.info("Email sync background task cancelled during error recovery")
                    raise
    except asyncio.CancelledError:
        logger.info("Email sync background task stopped")
        raise


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
        
        # 获取所有账户（使用后台任务专用线程池执行同步数据库操作）
        loop = asyncio.get_event_loop()
        accounts_data, total_accounts = await loop.run_in_executor(
            background_tasks_executor,
            db.get_all_accounts_db, 1, 10000
        )
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
                
                # 获取账户凭证
                credentials = await get_account_credentials(email_id)
                
                # 预加载收件箱邮件（不强制刷新，优先使用缓存）
                from email_service import list_emails
                result = await list_emails(
                    credentials=credentials,
                    folder='INBOX',
                    page=1,
                    page_size=CACHE_WARMUP_EMAILS_PER_ACCOUNT,
                    force_refresh=False
                )
                
                logger.info(f"Warmed up {len(result.emails)} emails for {email_id}")
                
            except Exception as e:
                logger.warning(f"Failed to warmup cache for {account['email']}: {e}")
                continue
        
        logger.info("Cache warmup completed")
        
    except Exception as e:
        logger.exception("Error during cache warmup")


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

    # 启动后台Token刷新任务（已优化：使用线程池执行同步数据库操作）
    refresh_task = asyncio.create_task(token_refresh_background_task())
    logger.info("Token refresh background task scheduled (using thread pool for DB operations)")
    
    # 启动后台邮件同步任务（已优化：使用线程池执行同步数据库操作）
    email_sync_task = None
    if AUTO_SYNC_EMAILS_ENABLED:
        email_sync_task = asyncio.create_task(email_sync_background_task())
        logger.info("Email sync background task scheduled (using thread pool for DB operations)")
        logger.info(f"Auto sync interval: {EMAIL_SYNC_INTERVAL} seconds ({EMAIL_SYNC_INTERVAL // 60} minutes)")
    else:
        logger.info("Email auto sync is disabled")
    
    # 启动缓存预热（已优化：使用线程池执行同步数据库操作）
    asyncio.create_task(warmup_cache())

    yield

    # 应用关闭
    logger.info(f"Shutting down {APP_TITLE}...")

    # 取消后台任务（带超时）
    tasks_to_cancel = []
    if refresh_task:
        tasks_to_cancel.append(refresh_task)
    if email_sync_task:
        tasks_to_cancel.append(email_sync_task)
    
    # 取消所有任务
    for task in tasks_to_cancel:
        if not task.done():
            task.cancel()
            logger.debug(f"Cancelled task: {task.get_name()}")
    
    # 等待任务取消完成（带超时）
    if tasks_to_cancel:
        try:
            # 等待任务完成或取消，最多等待3秒
            done, pending = await asyncio.wait(
                tasks_to_cancel,
                timeout=3.0,
                return_when=asyncio.ALL_COMPLETED
            )
            
            if pending:
                logger.warning(f"{len(pending)} background tasks still pending after timeout, forcing shutdown")
                # 强制取消剩余任务（不等待）
                for task in pending:
                    if not task.done():
                        task.cancel()
            else:
                logger.info("All background tasks cancelled successfully")
        except Exception as e:
            logger.error(f"Error cancelling background tasks: {e}")
            # 即使出错也继续关闭流程

    # 关闭线程池
    logger.info("Shutting down thread pools...")
    try:
        api_requests_executor.shutdown(wait=False)
        background_tasks_executor.shutdown(wait=False)
        logger.info("Thread pools shut down successfully")
    except Exception as e:
        logger.error(f"Error shutting down thread pools: {e}")

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

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    start_time = asyncio.get_event_loop().time()
    logger.info(f"→ {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"← {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"✗ {request.method} {request.url.path} - Error: {e} - Time: {process_time:.3f}s", exc_info=True)
        raise

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

# 添加全局异常处理器（在路由注册之后）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，确保所有异常都被记录"""
    import traceback
    from fastapi import HTTPException
    
    # 如果是 HTTPException，直接抛出（不记录，因为这是预期的错误）
    if isinstance(exc, HTTPException):
        raise exc
    
    # 其他未预期的异常才记录
    error_msg = f"Unhandled exception: {type(exc).__name__}: {str(exc)}"
    logger.error(f"{error_msg}\nURL: {request.url}\nMethod: {request.method}\n{traceback.format_exc()}")
    
    # 返回 500 错误
    return JSONResponse(
        status_code=500,
        content={"detail": f"内部服务器错误: {str(exc)}"}
    )


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
