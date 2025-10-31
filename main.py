"""
Outlook邮件管理系统 - 主应用模块

基于FastAPI和IMAP协议的高性能邮件管理系统
支持多账户管理、邮件查看、搜索过滤等功能

Author: Outlook Manager Team
Version: 2.0.0
"""

import asyncio
import email
import imaplib
import logging
import os
import re
import socket
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from itertools import groupby
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from queue import Empty, Queue
from typing import AsyncGenerator, List, Optional

import httpx
from email.header import decode_header
from email.utils import parsedate_to_datetime
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

# 导入自定义模块
import admin_api
import auth
import database as db


# ============================================================================
# 配置常量
# ============================================================================

# OAuth2配置
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
OAUTH_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"

# IMAP服务器配置
IMAP_SERVER = "outlook.live.com"
IMAP_PORT = 993

# 连接池配置
MAX_CONNECTIONS = 5
CONNECTION_TIMEOUT = 30
SOCKET_TIMEOUT = 15

# 缓存配置
CACHE_EXPIRE_TIME = 60  # 缓存过期时间（秒）

# 日志配置
LOG_DIR = "logs"
LOG_FILE = "outlook_manager.log"
LOG_RETENTION_DAYS = 30

# 确保日志目录存在
Path(LOG_DIR).mkdir(exist_ok=True)

# 配置日志系统
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 清除现有处理器
logger.handlers.clear()

# 文件处理器 - 按天轮转，保留30天
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, LOG_FILE),
    when="midnight",
    interval=1,
    backupCount=LOG_RETENTION_DAYS,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info("Logging system initialized")


# ============================================================================
# 数据模型 (Pydantic Models)
# ============================================================================


class AccountCredentials(BaseModel):
    """账户凭证模型"""

    email: EmailStr
    refresh_token: str
    client_id: str
    tags: Optional[List[str]] = Field(default=[])
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"
    refresh_error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "user@outlook.com",
                "refresh_token": "0.AXoA...",
                "client_id": "your-client-id",
                "tags": ["工作", "个人"],
                "last_refresh_time": "2024-01-01T12:00:00",
                "refresh_status": "success",
            }
        }


class EmailItem(BaseModel):
    """邮件项目模型"""

    message_id: str
    folder: str
    subject: str
    from_email: str
    date: str
    is_read: bool = False
    has_attachments: bool = False
    sender_initial: str = "?"

    class Config:
        schema_extra = {
            "example": {
                "message_id": "INBOX-123",
                "folder": "INBOX",
                "subject": "Welcome to Augment Code",
                "from_email": "noreply@augmentcode.com",
                "date": "2024-01-01T12:00:00",
                "is_read": False,
                "has_attachments": False,
                "sender_initial": "A",
            }
        }


class EmailListResponse(BaseModel):
    """邮件列表响应模型"""

    email_id: str
    folder_view: str
    page: int
    page_size: int
    total_emails: int
    emails: List[EmailItem]


class DualViewEmailResponse(BaseModel):
    """双栏视图邮件响应模型"""

    email_id: str
    inbox_emails: List[EmailItem]
    junk_emails: List[EmailItem]
    inbox_total: int
    junk_total: int


class EmailDetailsResponse(BaseModel):
    """邮件详情响应模型"""

    message_id: str
    subject: str
    from_email: str
    to_email: str
    date: str
    body_plain: Optional[str] = None
    body_html: Optional[str] = None


class AccountResponse(BaseModel):
    """账户操作响应模型"""

    email_id: str
    message: str


class AccountInfo(BaseModel):
    """账户信息模型"""

    email_id: str
    client_id: str
    status: str = "active"
    tags: List[str] = []
    last_refresh_time: Optional[str] = None
    next_refresh_time: Optional[str] = None
    refresh_status: str = "pending"


class AccountListResponse(BaseModel):
    """账户列表响应模型"""

    total_accounts: int
    page: int
    page_size: int
    total_pages: int
    accounts: List[AccountInfo]


class UpdateTagsRequest(BaseModel):
    """更新标签请求模型"""

    tags: List[str]


class AddTagRequest(BaseModel):
    """添加标签请求模型"""

    tag: str


# ============================================================================
# IMAP连接池管理
# ============================================================================


class IMAPConnectionPool:
    """
    IMAP连接池管理器

    提供连接复用、自动重连、连接状态监控等功能
    优化IMAP连接性能，减少连接建立开销
    """

    def __init__(self, max_connections: int = MAX_CONNECTIONS):
        """
        初始化连接池

        Args:
            max_connections: 每个邮箱的最大连接数
        """
        self.max_connections = max_connections
        self.connections = {}  # {email: Queue of connections}
        self.connection_count = {}  # {email: active connection count}
        self.lock = threading.Lock()
        logger.info(
            f"Initialized IMAP connection pool with max_connections={max_connections}"
        )

    def _create_connection(self, email: str, access_token: str) -> imaplib.IMAP4_SSL:
        """
        创建新的IMAP连接

        Args:
            email: 邮箱地址
            access_token: OAuth2访问令牌

        Returns:
            IMAP4_SSL: 已认证的IMAP连接

        Raises:
            Exception: 连接创建失败
        """
        try:
            # 设置全局socket超时
            socket.setdefaulttimeout(SOCKET_TIMEOUT)

            # 创建SSL IMAP连接
            imap_client = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

            # 设置连接超时
            imap_client.sock.settimeout(CONNECTION_TIMEOUT)

            # XOAUTH2认证
            auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01".encode(
                "utf-8"
            )
            imap_client.authenticate("XOAUTH2", lambda _: auth_string)

            logger.info(f"Successfully created IMAP connection for {email}")
            return imap_client

        except Exception as e:
            logger.error(f"Failed to create IMAP connection for {email}: {e}")
            raise

    def get_connection(self, email: str, access_token: str) -> imaplib.IMAP4_SSL:
        """
        获取IMAP连接（从池中复用或创建新连接）

        Args:
            email: 邮箱地址
            access_token: OAuth2访问令牌

        Returns:
            IMAP4_SSL: 可用的IMAP连接

        Raises:
            Exception: 无法获取连接
        """
        with self.lock:
            # 初始化邮箱的连接池
            if email not in self.connections:
                self.connections[email] = Queue(maxsize=self.max_connections)
                self.connection_count[email] = 0

            connection_queue = self.connections[email]

            # 尝试从池中获取现有连接
            try:
                connection = connection_queue.get_nowait()
                # 测试连接有效性
                try:
                    connection.noop()
                    logger.debug(f"Reused existing IMAP connection for {email}")
                    return connection
                except Exception:
                    # 连接已失效，需要创建新连接
                    logger.debug(
                        f"Existing connection invalid for {email}, creating new one"
                    )
                    self.connection_count[email] -= 1
            except Empty:
                # 池中没有可用连接
                pass

            # 检查是否可以创建新连接
            if self.connection_count[email] < self.max_connections:
                connection = self._create_connection(email, access_token)
                self.connection_count[email] += 1
                return connection
            else:
                # 达到最大连接数，等待可用连接
                logger.warning(
                    f"Max connections ({self.max_connections}) reached for {email}, waiting..."
                )
                try:
                    return connection_queue.get(timeout=30)
                except Exception as e:
                    logger.error(f"Timeout waiting for connection for {email}: {e}")
                    raise

    def return_connection(self, email: str, connection: imaplib.IMAP4_SSL) -> None:
        """
        归还连接到池中

        Args:
            email: 邮箱地址
            connection: 要归还的IMAP连接
        """
        if email not in self.connections:
            logger.warning(
                f"Attempting to return connection for unknown email: {email}"
            )
            return

        try:
            # 测试连接状态
            connection.noop()
            # 连接有效，归还到池中
            self.connections[email].put_nowait(connection)
            logger.debug(f"Successfully returned IMAP connection for {email}")
        except Exception as e:
            # 连接已失效，减少计数并丢弃
            with self.lock:
                if email in self.connection_count:
                    self.connection_count[email] = max(
                        0, self.connection_count[email] - 1
                    )
            logger.debug(f"Discarded invalid connection for {email}: {e}")

    def close_all_connections(self, email: str = None) -> None:
        """
        关闭所有连接

        Args:
            email: 指定邮箱地址，如果为None则关闭所有邮箱的连接
        """
        with self.lock:
            if email:
                # 关闭指定邮箱的所有连接
                if email in self.connections:
                    closed_count = 0
                    while not self.connections[email].empty():
                        try:
                            conn = self.connections[email].get_nowait()
                            conn.logout()
                            closed_count += 1
                        except Exception as e:
                            logger.debug(f"Error closing connection: {e}")

                    self.connection_count[email] = 0
                    logger.info(f"Closed {closed_count} connections for {email}")
            else:
                # 关闭所有邮箱的连接
                total_closed = 0
                for email_key in list(self.connections.keys()):
                    count_before = self.connection_count.get(email_key, 0)
                    self.close_all_connections(email_key)
                    total_closed += count_before
                logger.info(f"Closed total {total_closed} connections for all accounts")


# ============================================================================
# 全局实例和缓存管理
# ============================================================================

# 全局连接池实例
imap_pool = IMAPConnectionPool()

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


# ============================================================================
# 邮件处理辅助函数
# ============================================================================


def decode_header_value(header_value: str) -> str:
    """
    解码邮件头字段

    处理各种编码格式的邮件头部信息，如Subject、From等

    Args:
        header_value: 原始头部值

    Returns:
        str: 解码后的字符串
    """
    if not header_value:
        return ""

    try:
        decoded_parts = decode_header(str(header_value))
        decoded_string = ""

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    # 使用指定编码或默认UTF-8解码
                    encoding = charset if charset else "utf-8"
                    decoded_string += part.decode(encoding, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    # 编码失败时使用UTF-8强制解码
                    decoded_string += part.decode("utf-8", errors="replace")
            else:
                decoded_string += str(part)

        return decoded_string.strip()
    except Exception as e:
        logger.warning(f"Failed to decode header value '{header_value}': {e}")
        return str(header_value) if header_value else ""


def extract_email_content(email_message: email.message.EmailMessage) -> tuple[str, str]:
    """
    提取邮件的纯文本和HTML内容

    Args:
        email_message: 邮件消息对象

    Returns:
        tuple[str, str]: (纯文本内容, HTML内容)
    """
    body_plain = ""
    body_html = ""

    try:
        if email_message.is_multipart():
            # 处理多部分邮件
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 跳过附件
                if "attachment" not in content_disposition.lower():
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)

                        if payload:
                            decoded_content = payload.decode(charset, errors="replace")

                            if content_type == "text/plain" and not body_plain:
                                body_plain = decoded_content
                            elif content_type == "text/html" and not body_html:
                                body_html = decoded_content

                    except Exception as e:
                        logger.warning(
                            f"Failed to decode email part ({content_type}): {e}"
                        )
        else:
            # 处理单部分邮件
            try:
                charset = email_message.get_content_charset() or "utf-8"
                payload = email_message.get_payload(decode=True)

                if payload:
                    content = payload.decode(charset, errors="replace")
                    content_type = email_message.get_content_type()

                    if content_type == "text/plain":
                        body_plain = content
                    elif content_type == "text/html":
                        body_html = content
                    else:
                        # 默认当作纯文本处理
                        body_plain = content

            except Exception as e:
                logger.warning(f"Failed to decode single-part email body: {e}")

    except Exception as e:
        logger.error(f"Error extracting email content: {e}")

    return body_plain.strip(), body_html.strip()


# ============================================================================
# 账户凭证管理模块
# ============================================================================


async def get_account_credentials(email_id: str) -> AccountCredentials:
    """
    从SQLite数据库获取指定邮箱的账户凭证

    Args:
        email_id: 邮箱地址

    Returns:
        AccountCredentials: 账户凭证对象

    Raises:
        HTTPException: 账户不存在或数据库读取失败
    """
    try:
        # 从数据库获取账户信息
        account = db.get_account_by_email(email_id)

        # 检查账户是否存在
        if not account:
            logger.warning(f"Account {email_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Account {email_id} not found")

        # 验证账户数据完整性
        required_fields = ["refresh_token", "client_id"]
        missing_fields = [field for field in required_fields if not account.get(field)]

        if missing_fields:
            logger.error(
                f"Account {email_id} missing required fields: {missing_fields}"
            )
            raise HTTPException(
                status_code=500, detail="Account configuration incomplete"
            )

        return AccountCredentials(
            email=account["email"],
            refresh_token=account["refresh_token"],
            client_id=account["client_id"],
            tags=account.get("tags", []),
            last_refresh_time=account.get("last_refresh_time"),
            next_refresh_time=account.get("next_refresh_time"),
            refresh_status=account.get("refresh_status", "pending"),
            refresh_error=account.get("refresh_error"),
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting account credentials for {email_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def save_account_credentials(
    email_id: str, credentials: AccountCredentials
) -> None:
    """保存账户凭证到SQLite数据库"""
    try:
        # 检查账户是否已存在
        existing_account = db.get_account_by_email(email_id)

        if existing_account:
            # 更新现有账户
            db.update_account(
                email_id,
                refresh_token=credentials.refresh_token,
                client_id=credentials.client_id,
                tags=credentials.tags if hasattr(credentials, "tags") else [],
                last_refresh_time=credentials.last_refresh_time,
                next_refresh_time=credentials.next_refresh_time,
                refresh_status=credentials.refresh_status,
                refresh_error=credentials.refresh_error,
            )
        else:
            # 创建新账户
            db.create_account(
                email=email_id,
                refresh_token=credentials.refresh_token,
                client_id=credentials.client_id,
                tags=credentials.tags if hasattr(credentials, "tags") else [],
            )

            # 更新额外字段
            if credentials.last_refresh_time or credentials.next_refresh_time:
                db.update_account(
                    email_id,
                    last_refresh_time=credentials.last_refresh_time,
                    next_refresh_time=credentials.next_refresh_time,
                    refresh_status=credentials.refresh_status,
                    refresh_error=credentials.refresh_error,
                )

        logger.info(f"Account credentials saved for {email_id}")
    except Exception as e:
        logger.error(f"Error saving account credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to save account")


async def get_all_accounts(
    page: int = 1,
    page_size: int = 10,
    email_search: Optional[str] = None,
    tag_search: Optional[str] = None,
) -> AccountListResponse:
    """获取所有已加载的邮箱账户列表，支持分页和搜索"""
    try:
        # 从数据库获取账户列表
        accounts_data, total_accounts = db.get_all_accounts_db(
            page=page,
            page_size=page_size,
            email_search=email_search,
            tag_search=tag_search,
        )

        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get(
                    "client_id"
                ):
                    status = "invalid"
            except Exception:
                status = "error"

            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
            )
            all_accounts.append(account)

        # 计算分页信息
        total_pages = (
            (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        )

        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )

    except Exception as e:
        logger.error(f"Error getting accounts list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# OAuth2令牌管理模块
# ============================================================================


async def get_access_token(credentials: AccountCredentials) -> str:
    """
    使用refresh_token获取access_token

    Args:
        credentials: 账户凭证信息

    Returns:
        str: OAuth2访问令牌

    Raises:
        HTTPException: 令牌获取失败
    """
    # 构建OAuth2请求数据
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": OAUTH_SCOPE,
    }

    try:
        # 发送令牌请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            response.raise_for_status()

            # 解析响应
            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error(f"No access token in response for {credentials.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Failed to obtain access token from response",
                )

            logger.info(f"Successfully obtained access token for {credentials.email}")
            return access_token

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP {e.response.status_code} error getting access token for {credentials.email}: {e}"
        )
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token or client credentials"
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except httpx.RequestError as e:
        logger.error(f"Request error getting access token for {credentials.email}: {e}")
        raise HTTPException(
            status_code=500, detail="Network error during token acquisition"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting access token for {credentials.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Token acquisition failed")


async def refresh_account_token(credentials: AccountCredentials) -> dict:
    """
    刷新账户的refresh_token

    Args:
        credentials: 账户凭证信息

    Returns:
        dict: {
            'success': bool,
            'new_refresh_token': str (if success),
            'new_access_token': str (if success),
            'error': str (if failed)
        }
    """
    # 构建OAuth2请求数据
    token_request_data = {
        "client_id": credentials.client_id,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
        "scope": OAUTH_SCOPE,
    }

    try:
        # 发送令牌请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            response.raise_for_status()

            # 解析响应
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")

            if not new_access_token:
                logger.error(
                    f"No access token in refresh response for {credentials.email}"
                )
                return {"success": False, "error": "No access token in response"}

            if not new_refresh_token:
                logger.warning(
                    f"No new refresh token in response for {credentials.email}, using existing one"
                )
                new_refresh_token = credentials.refresh_token

            logger.info(f"Successfully refreshed token for {credentials.email}")
            return {
                "success": True,
                "new_refresh_token": new_refresh_token,
                "new_access_token": new_access_token,
            }

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} error refreshing token"
        logger.error(f"{error_msg} for {credentials.email}: {e}")
        return {"success": False, "error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Network error refreshing token: {str(e)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{error_msg} for {credentials.email}")
        return {"success": False, "error": error_msg}


# ============================================================================
# IMAP核心服务 - 邮件列表
# ============================================================================


async def list_emails(
    credentials: AccountCredentials,
    folder: str,
    page: int,
    page_size: int,
    force_refresh: bool = False,
) -> EmailListResponse:
    """获取邮件列表 - 优化版本"""

    # 检查缓存
    cache_key = get_cache_key(credentials.email, folder, page, page_size)
    cached_result = get_cached_emails(cache_key, force_refresh)
    if cached_result:
        return cached_result

    access_token = await get_access_token(credentials)

    def _sync_list_emails():
        imap_client = None
        try:
            # 从连接池获取连接
            imap_client = imap_pool.get_connection(credentials.email, access_token)

            all_emails_data = []

            # 根据folder参数决定要获取的文件夹
            folders_to_check = []
            if folder == "inbox":
                folders_to_check = ["INBOX"]
            elif folder == "junk":
                folders_to_check = ["Junk"]
            else:  # folder == "all"
                folders_to_check = ["INBOX", "Junk"]

            for folder_name in folders_to_check:
                try:
                    # 选择文件夹
                    imap_client.select(f'"{folder_name}"', readonly=True)

                    # 搜索所有邮件
                    status, messages = imap_client.search(None, "ALL")
                    if status != "OK" or not messages or not messages[0]:
                        continue

                    message_ids = messages[0].split()

                    # 按日期排序所需的数据（邮件ID和日期）
                    # 为了避免获取所有邮件的日期，我们假设ID顺序与日期大致相关
                    message_ids.reverse()  # 通常ID越大越新

                    for msg_id in message_ids:
                        all_emails_data.append(
                            {"message_id_raw": msg_id, "folder": folder_name}
                        )

                except Exception as e:
                    logger.warning(f"Failed to access folder {folder_name}: {e}")
                    continue

            # 对所有文件夹的邮件进行统一分页
            total_emails = len(all_emails_data)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_email_meta = all_emails_data[start_index:end_index]

            email_items = []
            # 按文件夹分组批量获取
            paginated_email_meta.sort(key=lambda x: x["folder"])

            for folder_name, group in groupby(
                paginated_email_meta, key=lambda x: x["folder"]
            ):
                try:
                    imap_client.select(f'"{folder_name}"', readonly=True)

                    msg_ids_to_fetch = [item["message_id_raw"] for item in group]
                    if not msg_ids_to_fetch:
                        continue

                    # 批量获取邮件头 - 优化获取字段
                    msg_id_sequence = b",".join(msg_ids_to_fetch)
                    # 只获取必要的头部信息，减少数据传输
                    status, msg_data = imap_client.fetch(
                        msg_id_sequence,
                        "(FLAGS BODY.PEEK[HEADER.FIELDS (SUBJECT DATE FROM MESSAGE-ID)])",
                    )

                    if status != "OK":
                        continue

                    # 解析批量获取的数据
                    for i in range(0, len(msg_data), 2):
                        header_data = msg_data[i][1]

                        # 从返回的原始数据中解析出msg_id
                        # e.g., b'1 (BODY[HEADER.FIELDS (SUBJECT DATE FROM)] {..}'
                        match = re.match(rb"(\d+)\s+\(", msg_data[i][0])
                        if not match:
                            continue
                        fetched_msg_id = match.group(1)

                        msg = email.message_from_bytes(header_data)

                        subject = decode_header_value(
                            msg.get("Subject", "(No Subject)")
                        )
                        from_email = decode_header_value(
                            msg.get("From", "(Unknown Sender)")
                        )
                        date_str = msg.get("Date", "")

                        try:
                            date_obj = (
                                parsedate_to_datetime(date_str)
                                if date_str
                                else datetime.now()
                            )
                            formatted_date = date_obj.isoformat()
                        except Exception:
                            date_obj = datetime.now()
                            formatted_date = date_obj.isoformat()

                        message_id = f"{folder_name}-{fetched_msg_id.decode()}"

                        # 提取发件人首字母
                        sender_initial = "?"
                        if from_email:
                            # 尝试提取邮箱用户名的首字母
                            email_match = re.search(r"([a-zA-Z])", from_email)
                            if email_match:
                                sender_initial = email_match.group(1).upper()

                        email_item = EmailItem(
                            message_id=message_id,
                            folder=folder_name,
                            subject=subject,
                            from_email=from_email,
                            date=formatted_date,
                            is_read=False,  # 简化处理，实际可通过IMAP flags判断
                            has_attachments=False,  # 简化处理，实际需要检查邮件结构
                            sender_initial=sender_initial,
                        )
                        email_items.append(email_item)

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch bulk emails from {folder_name}: {e}"
                    )
                    continue

            # 按日期重新排序最终结果
            email_items.sort(key=lambda x: x.date, reverse=True)

            # 归还连接到池中
            imap_pool.return_connection(credentials.email, imap_client)

            result = EmailListResponse(
                email_id=credentials.email,
                folder_view=folder,
                page=page,
                page_size=page_size,
                total_emails=total_emails,
                emails=email_items,
            )

            # 设置缓存
            set_cached_emails(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            if imap_client:
                try:
                    # 如果出错，尝试归还连接或关闭
                    if hasattr(imap_client, "state") and imap_client.state != "LOGOUT":
                        imap_pool.return_connection(credentials.email, imap_client)
                    else:
                        # 连接已断开，从池中移除
                        pass
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail="Failed to retrieve emails")

    # 在线程池中运行同步代码
    return await asyncio.to_thread(_sync_list_emails)


# ============================================================================
# IMAP核心服务 - 邮件详情
# ============================================================================


async def get_email_details(
    credentials: AccountCredentials, message_id: str
) -> EmailDetailsResponse:
    """获取邮件详细内容 - 优化版本"""
    # 解析复合message_id
    try:
        folder_name, msg_id = message_id.split("-", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    access_token = await get_access_token(credentials)

    def _sync_get_email_details():
        imap_client = None
        try:
            # 从连接池获取连接
            imap_client = imap_pool.get_connection(credentials.email, access_token)

            # 选择正确的文件夹
            imap_client.select(folder_name)

            # 获取完整邮件内容
            status, msg_data = imap_client.fetch(msg_id, "(RFC822)")

            if status != "OK" or not msg_data:
                raise HTTPException(status_code=404, detail="Email not found")

            # 解析邮件
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 提取基本信息
            subject = decode_header_value(msg.get("Subject", "(No Subject)"))
            from_email = decode_header_value(msg.get("From", "(Unknown Sender)"))
            to_email = decode_header_value(msg.get("To", "(Unknown Recipient)"))
            date_str = msg.get("Date", "")

            # 格式化日期
            try:
                if date_str:
                    date_obj = parsedate_to_datetime(date_str)
                    formatted_date = date_obj.isoformat()
                else:
                    formatted_date = datetime.now().isoformat()
            except Exception:
                formatted_date = datetime.now().isoformat()

            # 提取邮件内容
            body_plain, body_html = extract_email_content(msg)

            # 归还连接到池中
            imap_pool.return_connection(credentials.email, imap_client)

            return EmailDetailsResponse(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                date=formatted_date,
                body_plain=body_plain if body_plain else None,
                body_html=body_html if body_html else None,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            if imap_client:
                try:
                    # 如果出错，尝试归还连接
                    if hasattr(imap_client, "state") and imap_client.state != "LOGOUT":
                        imap_pool.return_connection(credentials.email, imap_client)
                except Exception:
                    pass
            raise HTTPException(
                status_code=500, detail="Failed to retrieve email details"
            )

    # 在线程池中运行同步代码
    return await asyncio.to_thread(_sync_get_email_details)


# ============================================================================
# FastAPI应用和API端点
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
            # 继续运行，不中断任务


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI应用生命周期管理

    处理应用启动和关闭时的资源管理
    """
    # 应用启动
    logger.info("Starting Outlook Email Management System v2.0...")

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

    logger.info(
        f"IMAP connection pool initialized with max_connections={MAX_CONNECTIONS}"
    )

    # 启动后台Token刷新任务
    refresh_task = asyncio.create_task(token_refresh_background_task())
    logger.info("Token refresh background task scheduled")

    yield

    # 应用关闭
    logger.info("Shutting down Outlook Email Management System...")

    # 取消后台任务
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        logger.info("Token refresh background task cancelled")

    logger.info("Closing IMAP connection pool...")
    imap_pool.close_all_connections()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Outlook邮件API服务",
    description="基于FastAPI和IMAP协议的高性能邮件管理系统",
    version="2.0.0",
    lifespan=lifespan,
)

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


# ============================================================================
# 认证API端点
# ============================================================================


@app.post("/auth/login", response_model=auth.Token, tags=["认证"])
async def login(request: auth.LoginRequest):
    """
    管理员登录

    返回JWT访问令牌
    """
    admin = auth.authenticate_admin(request.username, request.password)

    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    db.update_admin_login_time(request.username)

    # 创建访问令牌
    access_token = auth.create_access_token(data={"sub": admin["username"]})

    logger.info(f"Admin {request.username} logged in successfully")

    return auth.Token(access_token=access_token)


@app.get("/auth/me", response_model=auth.AdminInfo, tags=["认证"])
async def get_current_user(admin: dict = Depends(auth.get_current_admin)):
    """
    获取当前登录的管理员信息
    """
    return auth.AdminInfo(
        id=admin["id"],
        username=admin["username"],
        email=admin.get("email"),
        is_active=bool(admin["is_active"]),
        created_at=admin["created_at"],
        last_login=admin.get("last_login"),
    )


@app.post("/auth/change-password", tags=["认证"])
async def change_password(
    request: auth.ChangePasswordRequest, admin: dict = Depends(auth.get_current_admin)
):
    """
    修改管理员密码
    """
    # 验证旧密码
    if not auth.verify_password(request.old_password, admin["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码
    new_password_hash = auth.hash_password(request.new_password)
    success = db.update_admin_password(admin["username"], new_password_hash)

    if success:
        logger.info(f"Admin {admin['username']} changed password")
        return {"message": "密码修改成功"}
    else:
        raise HTTPException(status_code=500, detail="密码修改失败")


# ============================================================================
# 账户管理API端点
# ============================================================================


@app.get("/accounts/random", response_model=AccountListResponse, tags=["账户管理"])
async def get_random_accounts(
    include_tags: Optional[str] = Query(None, description="必须包含的标签，多个用逗号分隔"),
    exclude_tags: Optional[str] = Query(None, description="必须不包含的标签，多个用逗号分隔"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，范围1-100"),
    admin: dict = Depends(auth.get_current_admin),
):
    """随机获取邮箱账户列表（支持标签筛选和分页）"""
    try:
        # 解析标签列表
        include_tag_list = [tag.strip() for tag in include_tags.split(",")] if include_tags else None
        exclude_tag_list = [tag.strip() for tag in exclude_tags.split(",")] if exclude_tags else None
        
        # 从数据库获取随机账户
        accounts_data, total_accounts = db.get_random_accounts(
            include_tags=include_tag_list,
            exclude_tags=exclude_tag_list,
            page=page,
            page_size=page_size
        )
        
        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get("client_id"):
                    status = "invalid"
            except Exception:
                status = "error"
            
            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
            )
            all_accounts.append(account)
        
        # 计算分页信息
        total_pages = (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        
        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )
    except Exception as e:
        logger.error(f"Error getting random accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/accounts", response_model=AccountListResponse, tags=["账户管理"])
async def get_accounts(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，范围1-100"),
    email_search: Optional[str] = Query(None, description="邮箱账号模糊搜索"),
    tag_search: Optional[str] = Query(None, description="标签模糊搜索"),
    refresh_status: Optional[str] = Query(None, description="刷新状态筛选 (all, never_refreshed, success, failed, pending, custom)"),
    time_filter: Optional[str] = Query(None, description="时间过滤器 (today, week, month, custom)"),
    after_date: Optional[str] = Query(None, description="自定义日期（ISO格式）"),
    refresh_start_date: Optional[str] = Query(None, description="刷新起始日期（ISO格式，用于自定义日期范围）"),
    refresh_end_date: Optional[str] = Query(None, description="刷新截止日期（ISO格式，用于自定义日期范围）"),
    admin: dict = Depends(auth.get_current_admin),
):
    """获取所有已加载的邮箱账户列表，支持分页和多维度搜索"""
    try:
        logger.info(f"[API] GET /accounts 收到请求:")
        logger.info(f"  page={page}, page_size={page_size}")
        logger.info(f"  email_search={email_search}, tag_search={tag_search}")
        logger.info(f"  refresh_status={refresh_status}, time_filter={time_filter}")
        logger.info(f"  after_date={after_date}")
        logger.info(f"  refresh_start_date={refresh_start_date}")
        logger.info(f"  refresh_end_date={refresh_end_date}")
        
        # 使用新的筛选函数
        accounts_data, total_accounts = db.get_accounts_by_filters(
            page=page,
            page_size=page_size,
            email_search=email_search,
            tag_search=tag_search,
            refresh_status=refresh_status,
            time_filter=time_filter,
            after_date=after_date,
            refresh_start_date=refresh_start_date,
            refresh_end_date=refresh_end_date,
        )
        
        logger.info(f"[API] 查询结果: 总数={total_accounts}, 返回={len(accounts_data)}条")
        
        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get("client_id"):
                    status = "invalid"
            except Exception:
                status = "error"
            
            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
            )
            all_accounts.append(account)
        
        # 计算分页信息
        total_pages = (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        
        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )
        
    except Exception as e:
        logger.error(f"Error getting accounts list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/accounts", response_model=AccountResponse, tags=["账户管理"])
async def register_account(
    credentials: AccountCredentials, admin: dict = Depends(auth.get_current_admin)
):
    """注册或更新邮箱账户"""
    try:
        # 验证凭证有效性
        await get_access_token(credentials)

        # 保存凭证
        await save_account_credentials(credentials.email, credentials)

        return AccountResponse(
            email_id=credentials.email,
            message="Account verified and saved successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering account: {e}")
        raise HTTPException(status_code=500, detail="Account registration failed")


# ============================================================================
# 邮件管理API端点
# ============================================================================


@app.get("/emails/{email_id}", response_model=EmailListResponse, tags=["邮件管理"])
async def get_emails(
    email_id: str,
    folder: str = Query("all", regex="^(inbox|junk|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    refresh: bool = Query(False, description="强制刷新缓存"),
    admin: dict = Depends(auth.get_current_admin),
):
    """获取邮件列表"""
    credentials = await get_account_credentials(email_id)
    return await list_emails(credentials, folder, page, page_size, refresh)


@app.get("/emails/{email_id}/dual-view", tags=["邮件管理"])
async def get_dual_view_emails(
    email_id: str,
    inbox_page: int = Query(1, ge=1),
    junk_page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(auth.get_current_admin),
):
    """获取双栏视图邮件（收件箱和垃圾箱）"""
    credentials = await get_account_credentials(email_id)

    # 并行获取收件箱和垃圾箱邮件
    inbox_response = await list_emails(credentials, "inbox", inbox_page, page_size)
    junk_response = await list_emails(credentials, "junk", junk_page, page_size)

    return DualViewEmailResponse(
        email_id=email_id,
        inbox_emails=inbox_response.emails,
        junk_emails=junk_response.emails,
        inbox_total=inbox_response.total_emails,
        junk_total=junk_response.total_emails,
    )


@app.put("/accounts/{email_id}/tags", response_model=AccountResponse, tags=["账户管理"])
async def update_account_tags(
    email_id: str,
    request: UpdateTagsRequest,
    admin: dict = Depends(auth.get_current_admin),
):
    """更新账户标签"""
    try:
        # 检查账户是否存在
        credentials = await get_account_credentials(email_id)

        # 更新标签
        credentials.tags = request.tags

        # 保存更新后的凭证
        await save_account_credentials(email_id, credentials)

        return AccountResponse(
            email_id=email_id, message="Account tags updated successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to update account tags")


@app.post("/accounts/{email_id}/tags/add", response_model=AccountResponse, tags=["账户管理"])
async def add_account_tag(
    email_id: str,
    request: AddTagRequest,
    admin: dict = Depends(auth.get_current_admin),
):
    """为账户添加标签（如果标签已存在则不处理）"""
    try:
        # 使用数据库函数添加标签
        success = db.add_tag_to_account(email_id, request.tag)
        
        if not success:
            # 账户不存在
            raise HTTPException(status_code=404, detail=f"Account {email_id} not found")
        
        # 检查标签是否已存在
        account = db.get_account_by_email(email_id)
        if request.tag in account.get('tags', []):
            return AccountResponse(
                email_id=email_id, 
                message=f"Tag '{request.tag}' already exists for account."
            )
        else:
            return AccountResponse(
                email_id=email_id, 
                message=f"Tag '{request.tag}' added successfully."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tag to account: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tag to account")


@app.get(
    "/emails/{email_id}/{message_id}",
    response_model=EmailDetailsResponse,
    tags=["邮件管理"],
)
async def get_email_detail(
    email_id: str, message_id: str, admin: dict = Depends(auth.get_current_admin)
):
    """获取邮件详细内容"""
    credentials = await get_account_credentials(email_id)
    return await get_email_details(credentials, message_id)


@app.delete("/accounts/{email_id}", response_model=AccountResponse, tags=["账户管理"])
async def delete_account(email_id: str, admin: dict = Depends(auth.get_current_admin)):
    """删除邮箱账户"""
    try:
        # 检查账户是否存在
        await get_account_credentials(email_id)

        # 从数据库删除账户
        success = db.delete_account(email_id)

        if success:
            return AccountResponse(
                email_id=email_id, message="Account deleted successfully."
            )
        else:
            raise HTTPException(status_code=404, detail="Account not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    return FileResponse("static/index.html")


# ============================================================================
# 缓存管理API端点
# ============================================================================


@app.delete("/cache/{email_id}", tags=["缓存管理"])
async def clear_cache(email_id: str, admin: dict = Depends(auth.get_current_admin)):
    """清除指定邮箱的缓存"""
    clear_email_cache(email_id)
    logger.info(f"Cache cleared for {email_id} by {admin['username']}")
    return {"message": f"Cache cleared for {email_id}"}


@app.delete("/cache", tags=["缓存管理"])
async def clear_all_cache(admin: dict = Depends(auth.get_current_admin)):
    """清除所有缓存"""
    clear_email_cache()
    logger.info(f"All cache cleared by {admin['username']}")
    return {"message": "All cache cleared"}


# ============================================================================
# Token刷新API端点
# ============================================================================


@app.post(
    "/accounts/{email_id}/refresh-token",
    response_model=AccountResponse,
    tags=["账户管理"],
)
async def manual_refresh_token(
    email_id: str, admin: dict = Depends(auth.get_current_admin)
):
    """手动刷新指定账户的token"""
    try:
        # 获取账户凭证
        credentials = await get_account_credentials(email_id)

        # 调用刷新函数
        result = await refresh_account_token(credentials)

        if result["success"]:
            # 更新凭证对象
            current_time = datetime.now().isoformat()
            next_refresh = datetime.now() + timedelta(days=3)

            credentials.refresh_token = result["new_refresh_token"]
            credentials.last_refresh_time = current_time
            credentials.next_refresh_time = next_refresh.isoformat()
            credentials.refresh_status = "success"
            credentials.refresh_error = None

            # 保存更新后的凭证
            await save_account_credentials(email_id, credentials)

            logger.info(f"Token refreshed for {email_id} by {admin['username']}")

            return AccountResponse(
                email_id=email_id,
                message=f"Token refreshed successfully at {current_time}",
            )
        else:
            # 更新失败状态
            credentials.refresh_status = "failed"
            credentials.refresh_error = result.get("error", "Unknown error")
            await save_account_credentials(email_id, credentials)

            raise HTTPException(
                status_code=500,
                detail=f"Token refresh failed: {result.get('error', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error manually refreshing token for {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


class BatchRefreshResult(BaseModel):
    """批量刷新结果模型"""
    total_processed: int
    success_count: int
    failed_count: int
    details: List[dict]


@app.post(
    "/accounts/batch-refresh-tokens",
    response_model=BatchRefreshResult,
    tags=["账户管理"],
)
async def batch_refresh_tokens(
    email_search: Optional[str] = Query(None, description="邮箱账号模糊搜索"),
    tag_search: Optional[str] = Query(None, description="标签模糊搜索"),
    refresh_status: Optional[str] = Query(None, description="刷新状态筛选 (all, never_refreshed, success, failed, pending, custom)"),
    time_filter: Optional[str] = Query(None, description="时间过滤器 (today, week, month, custom)"),
    after_date: Optional[str] = Query(None, description="自定义日期（ISO格式）"),
    refresh_start_date: Optional[str] = Query(None, description="刷新起始日期（ISO格式，用于自定义日期范围）"),
    refresh_end_date: Optional[str] = Query(None, description="刷新截止日期（ISO格式，用于自定义日期范围）"),
    admin: dict = Depends(auth.get_current_admin),
):
    """批量刷新符合条件的账户Token"""
    try:
        logger.info(f"Admin {admin['username']} initiated batch token refresh with filters: "
                   f"email_search={email_search}, tag_search={tag_search}, "
                   f"refresh_status={refresh_status}, time_filter={time_filter}, "
                   f"refresh_start_date={refresh_start_date}, refresh_end_date={refresh_end_date}")
        
        # 获取符合筛选条件的所有账户
        accounts_data, total_accounts = db.get_accounts_by_filters(
            page=1,
            page_size=10000,  # 获取所有符合条件的账户
            email_search=email_search,
            tag_search=tag_search,
            refresh_status=refresh_status,
            time_filter=time_filter,
            after_date=after_date,
            refresh_start_date=refresh_start_date,
            refresh_end_date=refresh_end_date,
        )
        
        if not accounts_data:
            logger.info("No accounts match the filter criteria")
            return BatchRefreshResult(
                total_processed=0,
                success_count=0,
                failed_count=0,
                details=[]
            )
        
        # 逐个刷新token
        success_count = 0
        failed_count = 0
        details = []
        
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
                    success_count += 1
                    details.append({
                        "email": email_id,
                        "status": "success",
                        "message": "Token refreshed successfully"
                    })
                    logger.info(f"Successfully refreshed token for {email_id} in batch")
                else:
                    error_msg = result.get("error", "Unknown error")
                    db.update_account(
                        email_id,
                        refresh_status="failed",
                        refresh_error=error_msg,
                    )
                    failed_count += 1
                    details.append({
                        "email": email_id,
                        "status": "failed",
                        "message": error_msg
                    })
                    logger.error(f"Failed to refresh token for {email_id} in batch: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error refreshing token for {email_id} in batch: {e}")
                db.update_account(
                    email_id,
                    refresh_status="failed",
                    refresh_error=error_msg,
                )
                failed_count += 1
                details.append({
                    "email": email_id,
                    "status": "failed",
                    "message": error_msg
                })
        
        logger.info(f"Batch token refresh completed by {admin['username']}: "
                   f"{success_count} succeeded, {failed_count} failed out of {total_accounts}")
        
        return BatchRefreshResult(
            total_processed=total_accounts,
            success_count=success_count,
            failed_count=failed_count,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Error in batch token refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Batch refresh failed: {str(e)}")


@app.get("/api")
async def api_status():
    """API状态检查"""
    return {
        "message": "Outlook邮件API服务正在运行",
        "version": "1.0.0",
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

    # 启动配置
    HOST = "0.0.0.0"
    PORT = 8000

    logger.info(f"Starting Outlook Email Management System on {HOST}:{PORT}")
    logger.info("Access the web interface at: http://localhost:8000")
    logger.info("Access the API documentation at: http://localhost:8000/docs")

    uvicorn.run(app, host=HOST, port=PORT, log_level="info", access_log=True)
