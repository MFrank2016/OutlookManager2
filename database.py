"""
SQLite数据库管理模块

提供数据库初始化、表操作、数据查询等功能
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_FILE = "data.db"


@contextmanager
def get_db_connection():
    """
    获取数据库连接的上下文管理器
    
    自动处理连接的创建和关闭
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # 返回字典式结果
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
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
        
        # 创建 admins 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        """)
        
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
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(key)")
        
        conn.commit()
        logger.info("Database initialized successfully")


# ============================================================================
# Accounts 表操作
# ============================================================================

def get_account_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    根据邮箱地址获取账户信息
    
    Args:
        email: 邮箱地址
        
    Returns:
        账户信息字典或None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            account = dict(row)
            # 解析 tags JSON
            account['tags'] = json.loads(account['tags']) if account['tags'] else []
            return account
        return None


def get_all_accounts_db(
    page: int = 1,
    page_size: int = 10,
    email_search: Optional[str] = None,
    tag_search: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取所有账户列表（支持分页和搜索）
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        email_search: 邮箱模糊搜索
        tag_search: 标签模糊搜索
        
    Returns:
        (账户列表, 总数)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if email_search:
            conditions.append("email LIKE ?")
            params.append(f"%{email_search}%")
        
        if tag_search:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag_search}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) FROM accounts WHERE {where_clause}", params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute(
            f"SELECT * FROM accounts WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        )
        rows = cursor.fetchall()
        
        accounts = []
        for row in rows:
            account = dict(row)
            account['tags'] = json.loads(account['tags']) if account['tags'] else []
            accounts.append(account)
        
        return accounts, total


def create_account(
    email: str,
    refresh_token: str,
    client_id: str,
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    创建新账户
    
    Args:
        email: 邮箱地址
        refresh_token: 刷新令牌
        client_id: 客户端ID
        tags: 标签列表
        
    Returns:
        创建的账户信息
    """
    tags = tags or []
    tags_json = json.dumps(tags, ensure_ascii=False)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (email, refresh_token, client_id, tags)
            VALUES (?, ?, ?, ?)
        """, (email, refresh_token, client_id, tags_json))
        
        account_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Created account: {email}")
        return get_account_by_email(email)


def update_account(email: str, **kwargs) -> bool:
    """
    更新账户信息
    
    Args:
        email: 邮箱地址
        **kwargs: 要更新的字段
        
    Returns:
        是否更新成功
    """
    if not kwargs:
        return False
    
    # 处理 tags 字段
    if 'tags' in kwargs:
        kwargs['tags'] = json.dumps(kwargs['tags'], ensure_ascii=False)
    
    # 添加更新时间
    kwargs['updated_at'] = datetime.now().isoformat()
    
    # 构建 UPDATE 语句
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [email]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE accounts SET {set_clause} WHERE email = ?",
            values
        )
        conn.commit()
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Updated account: {email}")
        return success


def delete_account(email: str) -> bool:
    """
    删除账户
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否删除成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE email = ?", (email,))
        conn.commit()
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Deleted account: {email}")
        return success


# ============================================================================
# Admins 表操作
# ============================================================================

def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    根据用户名获取管理员信息
    
    Args:
        username: 用户名
        
    Returns:
        管理员信息字典或None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None


def create_admin(username: str, password_hash: str, email: str = None) -> Dict[str, Any]:
    """
    创建管理员账户
    
    Args:
        username: 用户名
        password_hash: 密码哈希
        email: 邮箱（可选）
        
    Returns:
        创建的管理员信息
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admins (username, password_hash, email)
            VALUES (?, ?, ?)
        """, (username, password_hash, email))
        
        conn.commit()
        logger.info(f"Created admin: {username}")
        return get_admin_by_username(username)


def update_admin_login_time(username: str) -> bool:
    """
    更新管理员最后登录时间
    
    Args:
        username: 用户名
        
    Returns:
        是否更新成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE admins SET last_login = ? WHERE username = ?",
            (datetime.now().isoformat(), username)
        )
        conn.commit()
        return cursor.rowcount > 0


def update_admin_password(username: str, new_password_hash: str) -> bool:
    """
    更新管理员密码
    
    Args:
        username: 用户名
        new_password_hash: 新密码哈希
        
    Returns:
        是否更新成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE admins SET password_hash = ? WHERE username = ?",
            (new_password_hash, username)
        )
        conn.commit()
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Updated password for admin: {username}")
        return success


def get_all_admins() -> List[Dict[str, Any]]:
    """
    获取所有管理员列表
    
    Returns:
        管理员列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, is_active, created_at, last_login FROM admins")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================================
# System Config 表操作
# ============================================================================

def get_config(key: str) -> Optional[str]:
    """
    获取系统配置值
    
    Args:
        key: 配置键
        
    Returns:
        配置值或None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return row['value']
        return None


def get_all_configs() -> List[Dict[str, Any]]:
    """
    获取所有系统配置
    
    Returns:
        配置列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_config ORDER BY key")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def set_config(key: str, value: str, description: str = None) -> bool:
    """
    设置系统配置
    
    Args:
        key: 配置键
        value: 配置值
        description: 描述
        
    Returns:
        是否设置成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_config (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                description = excluded.description,
                updated_at = excluded.updated_at
        """, (key, value, description, datetime.now().isoformat()))
        
        conn.commit()
        logger.info(f"Set config: {key} = {value}")
        return cursor.rowcount > 0


def delete_config(key: str) -> bool:
    """
    删除系统配置
    
    Args:
        key: 配置键
        
    Returns:
        是否删除成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM system_config WHERE key = ?", (key,))
        conn.commit()
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Deleted config: {key}")
        return success


# ============================================================================
# 通用表操作（用于管理面板）
# ============================================================================

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
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_table_data(
    table_name: str,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
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
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
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

