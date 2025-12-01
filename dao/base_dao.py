"""
BaseDAO - 所有 DAO 的基类

提供公共的数据访问方法，包括分页查询、默认分页大小等
"""

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_FILE = "data.db"

# 默认分页配置
DEFAULT_PAGE_SIZE = 10
DEFAULT_MAX_PAGE_SIZE = 100
DEFAULT_MAX_SINGLE_QUERY = 10000


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


class BaseDAO:
    """
    DAO 基类
    
    提供公共的数据访问方法
    """
    
    def __init__(self, table_name: str):
        """
        初始化 DAO
        
        Args:
            table_name: 表名
        """
        self.table_name = table_name
        self.default_page_size = DEFAULT_PAGE_SIZE
        self.max_page_size = DEFAULT_MAX_PAGE_SIZE
        self.max_single_query = DEFAULT_MAX_SINGLE_QUERY
    
    def _normalize_page_size(self, page_size: Optional[int] = None) -> int:
        """
        规范化分页大小
        
        Args:
            page_size: 分页大小
            
        Returns:
            规范化后的分页大小
        """
        if page_size is None:
            return self.default_page_size
        return min(max(1, page_size), self.max_page_size)
    
    def _normalize_page(self, page: int) -> int:
        """
        规范化页码
        
        Args:
            page: 页码
            
        Returns:
            规范化后的页码（从1开始）
        """
        return max(1, page)
    
    def _build_where_clause(
        self,
        conditions: List[str],
        params: List[Any]
    ) -> str:
        """
        构建 WHERE 子句
        
        Args:
            conditions: 条件列表
            params: 参数列表
            
        Returns:
            WHERE 子句字符串
        """
        if not conditions:
            return "1=1"
        return " AND ".join(conditions)
    
    def _dict_from_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        将 Row 对象转换为字典
        
        Args:
            row: SQLite Row 对象
            
        Returns:
            字典
        """
        return dict(row)
    
    def _dicts_from_rows(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """
        将 Row 对象列表转换为字典列表
        
        Args:
            rows: SQLite Row 对象列表
            
        Returns:
            字典列表
        """
        return [dict(row) for row in rows]
    
    def count(
        self,
        where_clause: str = "1=1",
        params: List[Any] = None
    ) -> int:
        """
        统计记录数
        
        Args:
            where_clause: WHERE 子句
            params: 参数列表
            
        Returns:
            记录数
        """
        params = params or []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}",
                params
            )
            return cursor.fetchone()[0]
    
    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据 ID 查找记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            记录字典或 None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (record_id,)
            )
            row = cursor.fetchone()
            return self._dict_from_row(row) if row else None
    
    def find_all(
        self,
        where_clause: str = "1=1",
        params: List[Any] = None,
        order_by: str = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查找所有记录（支持条件、排序、分页）
        
        Args:
            where_clause: WHERE 子句
            params: 参数列表
            order_by: 排序字段（如 "id DESC"）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            记录列表
        """
        params = params or []
        sql = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit is not None:
            sql += f" LIMIT ?"
            params.append(limit)
        
        if offset is not None:
            sql += f" OFFSET ?"
            params.append(offset)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return self._dicts_from_rows(rows)
    
    def find_paginated(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        where_clause: str = "1=1",
        params: List[Any] = None,
        order_by: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        分页查询
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            where_clause: WHERE 子句
            params: 参数列表
            order_by: 排序字段
            
        Returns:
            (记录列表, 总数)
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)
        params = params or []
        
        # 获取总数
        total = self.count(where_clause, params)
        
        # 获取分页数据
        offset = (page - 1) * page_size
        records = self.find_all(
            where_clause=where_clause,
            params=params,
            order_by=order_by,
            limit=page_size,
            offset=offset
        )
        
        return records, total
    
    def insert(self, data: Dict[str, Any]) -> int:
        """
        插入记录
        
        Args:
            data: 数据字典
            
        Returns:
            新记录的 ID
        """
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        columns_str = ", ".join(columns)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})",
                list(data.values())
            )
            conn.commit()
            return cursor.lastrowid
    
    def update(
        self,
        record_id: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        更新记录
        
        Args:
            record_id: 记录 ID
            data: 要更新的数据
            
        Returns:
            是否更新成功
        """
        if not data:
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [record_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, record_id: int) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            是否删除成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (record_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_by_condition(
        self,
        where_clause: str,
        params: List[Any] = None
    ) -> int:
        """
        根据条件删除记录
        
        Args:
            where_clause: WHERE 子句
            params: 参数列表
            
        Returns:
            删除的记录数
        """
        params = params or []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE {where_clause}",
                params
            )
            conn.commit()
            return cursor.rowcount
    
    def execute_query(
        self,
        sql: str,
        params: List[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行自定义查询
        
        Args:
            sql: SQL 语句
            params: 参数列表
            
        Returns:
            查询结果列表
        """
        params = params or []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return self._dicts_from_rows(rows)
    
    def execute_update(
        self,
        sql: str,
        params: List[Any] = None
    ) -> int:
        """
        执行更新操作（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL 语句
            params: 参数列表
            
        Returns:
            受影响的行数
        """
        params = params or []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount

