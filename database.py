"""
SQLite数据库管理模块

提供数据库初始化、表操作、数据查询等功能
"""

import json
import sqlite3
import zlib
import base64
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging

from config import COMPRESS_BODY_THRESHOLD

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_FILE = "data.db"


# ============================================================================
# 压缩/解压缩工具函数
# ============================================================================

def compress_text(text: Optional[str]) -> Optional[str]:
    """
    压缩文本（超过阈值才压缩）
    
    Args:
        text: 要压缩的文本
        
    Returns:
        压缩后的base64编码字符串，或原文本
    """
    if not text or len(text) < COMPRESS_BODY_THRESHOLD:
        return text
    
    try:
        compressed = zlib.compress(text.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        logger.debug(f"Compressed text from {len(text)} to {len(encoded)} bytes")
        return encoded
    except Exception as e:
        logger.warning(f"Failed to compress text: {e}")
        return text


def decompress_text(text: Optional[str]) -> Optional[str]:
    """
    解压缩文本
    
    Args:
        text: 压缩的base64编码字符串
        
    Returns:
        解压缩后的文本，或原文本
    """
    if not text:
        return text
    
    try:
        # 尝试解压缩
        decoded = base64.b64decode(text.encode('utf-8'))
        decompressed = zlib.decompress(decoded).decode('utf-8')
        return decompressed
    except Exception:
        # 如果解压失败，说明可能不是压缩的文本，直接返回
        return text


@contextmanager
def get_db_connection():
    """
    获取数据库连接的上下文管理器
    
    自动处理连接的创建和关闭
    包含数据库完整性检查和错误处理
    """
    conn = None
    try:
        # 尝试连接数据库
        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        conn.row_factory = sqlite3.Row  # 返回字典式结果
        
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        
        # 快速完整性检查（仅在连接时检查一次，避免每次查询都检查）
        # 注意：完整检查可能很慢，所以只在连接时做快速检查
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check")
            result = cursor.fetchone()
            if result and result[0] != "ok":
                logger.error(f"Database quick check failed: {result[0]}")
                raise sqlite3.DatabaseError(f"Database integrity check failed: {result[0]}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Database integrity error: {e}")
            if conn:
                conn.close()
            raise
        except Exception as e:
            # 如果 quick_check 不可用，尝试 integrity_check（可能较慢）
            logger.warning(f"Quick check failed, trying integrity_check: {e}")
            try:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check(1)")
                result = cursor.fetchone()
                if result and result[0] != "ok":
                    logger.error(f"Database integrity check failed: {result[0]}")
                    raise sqlite3.DatabaseError(f"Database integrity check failed: {result[0]}")
            except Exception:
                # 如果检查也失败，记录警告但继续（可能是旧版本SQLite）
                logger.warning("Could not perform database integrity check")
        
        yield conn
        conn.commit()
    except sqlite3.DatabaseError as e:
        if conn:
            conn.rollback()
        error_msg = str(e)
        if "malformed" in error_msg.lower() or "corrupt" in error_msg.lower():
            logger.error(f"Database corruption detected: {e}")
            logger.error("Please run scripts/repair_database.py to repair the database")
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_database() -> None:
    """
    初始化数据库，创建所有必要的表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 创建 accounts 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                refresh_token TEXT NOT NULL,
                client_id TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                last_refresh_time TEXT,
                next_refresh_time TEXT,
                refresh_status TEXT DEFAULT 'pending',
                refresh_error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 检查是否存在旧的 admins 表，如果存在则迁移到 users 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admins'
        """)
        has_admins_table = cursor.fetchone() is not None
        
        # 创建 users 表（原 admins 表）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                bound_accounts TEXT DEFAULT '[]',
                permissions TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        """)
        
        # 如果存在旧的 admins 表，迁移数据
        if has_admins_table:
            logger.info("Migrating data from admins table to users table...")
            try:
                # 检查 users 表是否为空
                cursor.execute("SELECT COUNT(*) FROM users")
                users_count = cursor.fetchone()[0]
                
                if users_count == 0:
                    # 迁移所有管理员数据到 users 表，设置 role='admin'
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, email, role, is_active, created_at, last_login)
                        SELECT username, password_hash, email, 'admin', is_active, created_at, last_login
                        FROM admins
                    """)
                    logger.info(f"Migrated {cursor.rowcount} admin accounts to users table")
                
                # 删除旧的 admins 表
                cursor.execute("DROP TABLE IF EXISTS admins")
                logger.info("Dropped old admins table")
            except Exception as e:
                logger.warning(f"Migration from admins to users failed (may be already migrated): {e}")
        
        # 尝试添加新字段（如果表已存在但没有这些字段）
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            logger.info("Added role column to users table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN bound_accounts TEXT DEFAULT '[]'")
            logger.info("Added bound_accounts column to users table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '[]'")
            logger.info("Added permissions column to users table")
        except Exception:
            pass
        
        # 创建 system_config 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建邮件列表缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_account TEXT NOT NULL,
                message_id TEXT NOT NULL,
                folder TEXT NOT NULL,
                subject TEXT,
                from_email TEXT,
                date TEXT,
                is_read INTEGER DEFAULT 0,
                has_attachments INTEGER DEFAULT 0,
                sender_initial TEXT,
                verification_code TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email_account, message_id)
            )
        """)
        
        # 尝试添加 verification_code 列（如果表已存在但没有此列）
        try:
            cursor.execute("ALTER TABLE emails_cache ADD COLUMN verification_code TEXT")
            logger.info("Added verification_code column to emails_cache table")
        except Exception:
            # 列已存在，忽略错误
            pass
        
        # 尝试添加 body_preview 列
        try:
            cursor.execute("ALTER TABLE emails_cache ADD COLUMN body_preview TEXT")
            logger.info("Added body_preview column to emails_cache table")
        except Exception:
            # 列已存在，忽略错误
            pass
        
        # 创建邮件详情缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_details_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_account TEXT NOT NULL,
                message_id TEXT NOT NULL,
                subject TEXT,
                from_email TEXT,
                to_email TEXT,
                date TEXT,
                body_plain TEXT,
                body_html TEXT,
                verification_code TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email_account, message_id)
            )
        """)
        
        # 尝试添加 verification_code 列（如果表已存在但没有此列）
        try:
            cursor.execute("ALTER TABLE email_details_cache ADD COLUMN verification_code TEXT")
            logger.info("Added verification_code column to email_details_cache table")
        except Exception:
            # 列已存在，忽略错误
            pass
        
        # 添加 LRU 相关字段 - emails_cache
        try:
            cursor.execute("ALTER TABLE emails_cache ADD COLUMN access_count INTEGER DEFAULT 0")
            logger.info("Added access_count column to emails_cache table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE emails_cache ADD COLUMN last_accessed_at TEXT")
            logger.info("Added last_accessed_at column to emails_cache table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE emails_cache ADD COLUMN cache_size INTEGER DEFAULT 0")
            logger.info("Added cache_size column to emails_cache table")
        except Exception:
            pass
        
        # 添加 LRU 相关字段 - email_details_cache
        try:
            cursor.execute("ALTER TABLE email_details_cache ADD COLUMN access_count INTEGER DEFAULT 0")
            logger.info("Added access_count column to email_details_cache table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE email_details_cache ADD COLUMN last_accessed_at TEXT")
            logger.info("Added last_accessed_at column to email_details_cache table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE email_details_cache ADD COLUMN body_size INTEGER DEFAULT 0")
            logger.info("Added body_size column to email_details_cache table")
        except Exception:
            pass
        
        # 添加 Access Token 缓存字段 - accounts
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN access_token TEXT")
            logger.info("Added access_token column to accounts table")
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN token_expires_at TEXT")
            logger.info("Added token_expires_at column to accounts table")
        except Exception:
            pass
        
        # 添加 API 方法字段 - accounts
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN api_method TEXT DEFAULT 'imap'")
            logger.info("Added api_method column to accounts table")
        except Exception:
            pass
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_account ON emails_cache(email_account)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_date ON emails_cache(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_details_cache_account ON email_details_cache(email_account)")
        
        # 性能优化索引 - emails_cache
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_folder ON emails_cache(folder)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_from_email ON emails_cache(from_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_subject ON emails_cache(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_account_folder ON emails_cache(email_account, folder)")
        
        # 性能优化索引 - email_details_cache
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_details_cache_message ON email_details_cache(message_id)")
        
        # LRU 相关索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_cache_last_accessed ON emails_cache(last_accessed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_details_cache_last_accessed ON email_details_cache(last_accessed_at)")
        
        # 创建 share_tokens 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                email_account_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                subject_keyword TEXT,
                sender_keyword TEXT,
                expiry_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_share_tokens_token ON share_tokens(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_share_tokens_account ON share_tokens(email_account_id)")
        
        # 创建批量导入任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_import_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                total_count INTEGER NOT NULL,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                processed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                api_method TEXT DEFAULT 'imap',
                tags TEXT DEFAULT '[]',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        # 创建批量导入任务详情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_import_task_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                email TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                client_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                FOREIGN KEY (task_id) REFERENCES batch_import_tasks(task_id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_import_tasks_task_id ON batch_import_tasks(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_import_tasks_status ON batch_import_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_import_task_items_task_id ON batch_import_task_items(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_import_task_items_status ON batch_import_task_items(status)")

        conn.commit()
        logger.info("Database initialized successfully")


# ============================================================================
# 原实现已迁移到 dao 目录
# 所有函数现在通过向后兼容层（文件末尾）委托给对应的 DAO
# ============================================================================


# ============================================================================
# 向后兼容层 - 将所有函数委托给对应的 DAO
# ============================================================================

# 延迟导入 DAO 以避免循环依赖
_account_dao = None
_user_dao = None
_config_dao = None
_email_cache_dao = None
_email_detail_cache_dao = None
_share_token_dao = None
_batch_import_task_dao = None
_batch_import_task_item_dao = None

def _get_account_dao():
    """获取 AccountDAO 实例（单例）"""
    global _account_dao
    if _account_dao is None:
        from dao.account_dao import AccountDAO
        _account_dao = AccountDAO()
    return _account_dao

def _get_user_dao():
    """获取 UserDAO 实例（单例）"""
    global _user_dao
    if _user_dao is None:
        from dao.user_dao import UserDAO
        _user_dao = UserDAO()
    return _user_dao

def _get_config_dao():
    """获取 ConfigDAO 实例（单例）"""
    global _config_dao
    if _config_dao is None:
        from dao.config_dao import ConfigDAO
        _config_dao = ConfigDAO()
    return _config_dao

def _get_email_cache_dao():
    """获取 EmailCacheDAO 实例（单例）"""
    global _email_cache_dao
    if _email_cache_dao is None:
        from dao.email_cache_dao import EmailCacheDAO
        _email_cache_dao = EmailCacheDAO()
    return _email_cache_dao

def _get_email_detail_cache_dao():
    """获取 EmailDetailCacheDAO 实例（单例）"""
    global _email_detail_cache_dao
    if _email_detail_cache_dao is None:
        from dao.email_detail_cache_dao import EmailDetailCacheDAO
        _email_detail_cache_dao = EmailDetailCacheDAO()
    return _email_detail_cache_dao

def _get_share_token_dao():
    """获取 ShareTokenDAO 实例（单例）"""
    global _share_token_dao
    if _share_token_dao is None:
        from dao.share_token_dao import ShareTokenDAO
        _share_token_dao = ShareTokenDAO()
    return _share_token_dao

def _get_batch_import_task_dao():
    """获取 BatchImportTaskDAO 实例（单例）"""
    global _batch_import_task_dao
    if _batch_import_task_dao is None:
        from dao.batch_import_task_dao import BatchImportTaskDAO
        _batch_import_task_dao = BatchImportTaskDAO()
    return _batch_import_task_dao

def _get_batch_import_task_item_dao():
    """获取 BatchImportTaskItemDAO 实例（单例）"""
    global _batch_import_task_item_dao
    if _batch_import_task_item_dao is None:
        from dao.batch_import_task_dao import BatchImportTaskItemDAO
        _batch_import_task_item_dao = BatchImportTaskItemDAO()
    return _batch_import_task_item_dao


# Accounts 表操作 - 委托给 AccountDAO
def get_account_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _get_account_dao().get_by_email(email)

def get_all_accounts_db(page: int = 1, page_size: int = 10, email_search: Optional[str] = None, tag_search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    return _get_account_dao().get_all(page, page_size, email_search, tag_search)

def get_accounts_by_filters(
    page: int = 1,
    page_size: int = 10,
    email_search: Optional[str] = None,
    tag_search: Optional[str] = None,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    refresh_status: Optional[str] = None,
    time_filter: Optional[str] = None,
    after_date: Optional[str] = None,
    refresh_start_date: Optional[str] = None,
    refresh_end_date: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    return _get_account_dao().get_by_filters(
        page, page_size, email_search, tag_search, include_tags, exclude_tags,
        refresh_status, time_filter, after_date, refresh_start_date, refresh_end_date
    )

def create_account(email: str, refresh_token: str, client_id: str, tags: List[str] = None, api_method: str = "imap") -> Dict[str, Any]:
    return _get_account_dao().create(email, refresh_token, client_id, tags, api_method)

def update_account(email: str, **kwargs) -> bool:
    return _get_account_dao().update_account(email, **kwargs)

def delete_account(email: str) -> bool:
    return _get_account_dao().delete_account(email)

def get_account_access_token(email: str) -> Optional[Dict[str, str]]:
    return _get_account_dao().get_access_token(email)

def update_account_access_token(email: str, access_token: str, expires_at: str) -> bool:
    return _get_account_dao().update_access_token(email, access_token, expires_at)

def get_random_accounts(include_tags: Optional[List[str]] = None, exclude_tags: Optional[List[str]] = None, page: int = 1, page_size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    return _get_account_dao().get_random(include_tags, exclude_tags, page, page_size)

def add_tag_to_account(email: str, tag: str) -> bool:
    return _get_account_dao().add_tag(email, tag)


# Users 表操作 - 委托给 UserDAO
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    return _get_user_dao().get_by_username(username)

def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    return _get_user_dao().get_by_username(username)

def create_user(username: str, password_hash: str, email: str = None, role: str = "user", bound_accounts: List[str] = None, permissions: List[str] = None, is_active: bool = True) -> Dict[str, Any]:
    return _get_user_dao().create(username, password_hash, email, role, bound_accounts, permissions, is_active)

def create_admin(username: str, password_hash: str, email: str = None) -> Dict[str, Any]:
    return _get_user_dao().create(username, password_hash, email, role="admin")

def update_user_login_time(username: str) -> bool:
    return _get_user_dao().update_login_time(username)

def update_admin_login_time(username: str) -> bool:
    return _get_user_dao().update_login_time(username)

def update_user_password(username: str, new_password_hash: str) -> bool:
    return _get_user_dao().update_password(username, new_password_hash)

def update_admin_password(username: str, new_password_hash: str) -> bool:
    return _get_user_dao().update_password(username, new_password_hash)

def get_all_users(page: int = 1, page_size: int = 50, role_filter: Optional[str] = None, search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    return _get_user_dao().get_all(page, page_size, role_filter, search)

def get_all_admins() -> List[Dict[str, Any]]:
    return _get_user_dao().get_by_role("admin")

def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    return _get_user_dao().get_by_role(role)

def update_user(username: str, **kwargs) -> bool:
    return _get_user_dao().update_user(username, **kwargs)

def update_user_permissions(username: str, permissions: List[str]) -> bool:
    return _get_user_dao().update_user(username, permissions=permissions)

def bind_accounts_to_user(username: str, account_emails: List[str]) -> bool:
    return _get_user_dao().update_user(username, bound_accounts=account_emails)

def get_user_bound_accounts(username: str) -> List[str]:
    user = _get_user_dao().get_by_username(username)
    if user:
        return user.get('bound_accounts', [])
    return []

def delete_user(username: str) -> bool:
    return _get_user_dao().delete_user(username)


# System Config 表操作 - 委托给 ConfigDAO
def get_config(key: str) -> Optional[str]:
    return _get_config_dao().get(key)

def get_all_configs() -> List[Dict[str, Any]]:
    return _get_config_dao().get_all()

def set_config(key: str, value: str, description: str = None) -> bool:
    return _get_config_dao().set(key, value, description)

def delete_config(key: str) -> bool:
    return _get_config_dao().delete_config(key)

def get_api_key() -> Optional[str]:
    return _get_config_dao().get_api_key()

def set_api_key(api_key: str) -> bool:
    return _get_config_dao().set_api_key(api_key)

def init_default_api_key() -> str:
    return _get_config_dao().init_default_api_key()


# Share Tokens 表操作 - 委托给 ShareTokenDAO
def create_share_token(token: str, email_account_id: str, start_time: str, end_time: Optional[str] = None, subject_keyword: Optional[str] = None, sender_keyword: Optional[str] = None, expiry_time: Optional[str] = None, is_active: bool = True) -> int:
    return _get_share_token_dao().create(token, email_account_id, start_time, end_time, subject_keyword, sender_keyword, expiry_time, is_active)

def get_share_token(token: str) -> Optional[Dict[str, Any]]:
    return _get_share_token_dao().get_by_token(token)

def update_share_token(token_id: int, **kwargs) -> bool:
    return _get_share_token_dao().update_token(token_id, **kwargs)

def delete_share_token(token_id: int) -> bool:
    return _get_share_token_dao().delete_token(token_id)

def list_share_tokens(email_account_id: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
    return _get_share_token_dao().list_tokens(email_account_id, page, page_size)


# 邮件缓存操作 - 委托给 EmailCacheDAO 和 EmailDetailCacheDAO
def cache_emails(email_account: str, emails: List[Dict[str, Any]]) -> bool:
    return _get_email_cache_dao().cache_emails(email_account, emails)

def get_cached_emails(email_account: str, page: int = 1, page_size: int = 100, folder: Optional[str] = None, sender_search: Optional[str] = None, subject_search: Optional[str] = None, sort_by: str = 'date', sort_order: str = 'desc', start_time: Optional[str] = None, end_time: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    return _get_email_cache_dao().get_cached_emails(email_account, page, page_size, folder, sender_search, subject_search, sort_by, sort_order, start_time, end_time)

def cache_email_detail(email_account: str, email_detail: Dict[str, Any]) -> bool:
    return _get_email_detail_cache_dao().cache_detail(email_account, email_detail)

def get_cached_email_detail(email_account: str, message_id: str) -> Optional[Dict[str, Any]]:
    return _get_email_detail_cache_dao().get_cached_detail(email_account, message_id)

def check_cache_size() -> Dict[str, Any]:
    return _get_email_detail_cache_dao().check_cache_size()

def cleanup_lru_cache() -> Dict[str, int]:
    return _get_email_detail_cache_dao().cleanup_lru_cache()

def clear_email_cache_db(email_account: str) -> bool:
    result1 = _get_email_cache_dao().clear_by_account(email_account)
    result2 = _get_email_detail_cache_dao().clear_by_account(email_account)
    return result1 or result2

def delete_email_from_cache(email_account: str, message_id: str) -> bool:
    result1 = _get_email_cache_dao().delete_email(email_account, message_id)
    result2 = _get_email_detail_cache_dao().delete_email(email_account, message_id)
    return result1 or result2

def get_email_count_by_account(email_account: str, folder: Optional[str] = None) -> int:
    return _get_email_cache_dao().get_count_by_account(email_account, folder)


# 批量导入任务操作 - 委托给 BatchImportTaskDAO
def create_batch_import_task(task_id: str, total_count: int, api_method: str = "imap", tags: List[str] = None, created_by: str = None) -> bool:
    return _get_batch_import_task_dao().create(task_id, total_count, api_method, tags, created_by)

def add_batch_import_task_items(task_id: str, items: List[Dict[str, str]]) -> bool:
    return _get_batch_import_task_item_dao().add_items(task_id, items)

def get_batch_import_task(task_id: str) -> Optional[Dict[str, Any]]:
    return _get_batch_import_task_dao().get_by_task_id(task_id)

def update_batch_import_task_progress(task_id: str, success_count: int = None, failed_count: int = None, processed_count: int = None, status: str = None) -> bool:
    return _get_batch_import_task_dao().update_progress(task_id, success_count, failed_count, processed_count, status)

def update_batch_import_task_item(task_id: str, email: str, status: str, error_message: str = None) -> bool:
    return _get_batch_import_task_item_dao().update_item(task_id, email, status, error_message)

def get_batch_import_task_items(task_id: str, status: str = None) -> List[Dict[str, Any]]:
    return _get_batch_import_task_item_dao().get_by_task_id(task_id, status)


# 通用表操作（用于管理面板）- 保留原实现
def get_all_tables() -> List[str]:
    """
    获取数据库中所有表名
    
    Returns:
        表名列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        rows = cursor.fetchall()
        return [row['name'] for row in rows]

def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    获取表结构信息
    
    Args:
        table_name: 表名
        
    Returns:
        表结构列表
    """
    # 验证表名，防止SQL注入
    if not table_name or not table_name.replace('_', '').replace('-', '').isalnum():
        raise ValueError(f"Invalid table name: {table_name}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.DatabaseError as e:
            error_msg = str(e)
            if "malformed" in error_msg.lower() or "corrupt" in error_msg.lower():
                logger.error(f"Database corruption detected when accessing table schema for {table_name}: {e}")
                logger.error("Please run scripts/repair_database.py to repair the database")
                raise sqlite3.DatabaseError(f"数据库表 {table_name} 可能已损坏，请运行修复脚本: {e}")
            raise

def get_table_data(table_name: str, page: int = 1, page_size: int = 50, search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取表数据（支持分页和搜索）
    
    Args:
        table_name: 表名
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        
    Returns:
        (数据列表, 总数)
    """
    # 验证表名，防止SQL注入
    if not table_name or not table_name.replace('_', '').replace('-', '').isalnum():
        raise ValueError(f"Invalid table name: {table_name}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # 获取表结构，用于构建搜索条件
            schema = get_table_schema(table_name)
            columns = [col['name'] for col in schema]
            
            # 构建搜索条件
            where_clause = "1=1"
            params = []
            
            if search:
                # 在所有文本列中搜索
                search_conditions = " OR ".join([f"{col} LIKE ?" for col in columns])
                where_clause = f"({search_conditions})"
                params = [f"%{search}%"] * len(columns)
            
            # 获取总数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}", params)
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows], total
        except sqlite3.DatabaseError as e:
            error_msg = str(e)
            if "malformed" in error_msg.lower() or "corrupt" in error_msg.lower():
                logger.error(f"Database corruption detected when accessing table {table_name}: {e}")
                logger.error("Please run scripts/repair_database.py to repair the database")
                raise sqlite3.DatabaseError(f"数据库表 {table_name} 可能已损坏，请运行修复脚本: {e}")
            raise

def insert_table_record(table_name: str, data: Dict[str, Any]) -> int:
    """
    插入表记录
    
    Args:
        table_name: 表名
        data: 数据字典
        
    Returns:
        新记录的ID
    """
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    columns_str = ", ".join(columns)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
            list(data.values())
        )
        conn.commit()
        return cursor.lastrowid

def update_table_record(table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
    """
    更新表记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        data: 要更新的数据
        
    Returns:
        是否更新成功
    """
    set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
    values = list(data.values()) + [record_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_table_record(table_name: str, record_id: int) -> bool:
    """
    删除表记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        
    Returns:
        是否删除成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0

