"""
BaseDAO - 所有 DAO 的基类

提供公共的数据访问方法，包括分页查询、默认分页大小等
支持SQLite和PostgreSQL
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

# 导入database模块的get_db_connection和配置
from database import get_db_connection
from config import DB_TYPE

logger = logging.getLogger(__name__)

# 默认分页配置
DEFAULT_PAGE_SIZE = 10
DEFAULT_MAX_PAGE_SIZE = 100
DEFAULT_MAX_SINGLE_QUERY = 10000


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
    
    def _dict_from_row(self, row) -> Dict[str, Any]:
        """
        将 Row 对象转换为字典
        
        Args:
            row: SQLite Row 或 PostgreSQL RealDictRow 对象
            
        Returns:
            字典
        """
        if hasattr(row, 'keys'):
            return dict(row)
        return dict(row) if row else {}
    
    def _dicts_from_rows(self, rows: List) -> List[Dict[str, Any]]:
        """
        将 Row 对象列表转换为字典列表
        
        Args:
            rows: SQLite Row 或 PostgreSQL RealDictRow 对象列表
            
        Returns:
            字典列表
        """
        return [dict(row) for row in rows] if rows else []
    
    def _extract_scalar_value(self, row: Any) -> Any:
        """
        从查询结果行中提取标量值（兼容SQLite Row、RealDictRow等）
        
        Args:
            row: 查询结果行
        
        Returns:
            标量值或 None
        """
        if row is None:
            return None
        if isinstance(row, dict):
            # RealDictRow / sqlite Row （当作映射）
            for value in row.values():
                return value
            return None
        if isinstance(row, (list, tuple)):
            return row[0] if row else None
        # 其他类型，尝试使用索引访问
        try:
            return row[0]
        except (KeyError, TypeError, IndexError):
            return row
    
    def _get_param_placeholder(self) -> str:
        """
        获取参数占位符
        
        Returns:
            '?' for SQLite, '%s' for PostgreSQL
        """
        return "%s" if DB_TYPE == "postgresql" else "?"
    
    def _replace_sql_placeholders(self, sql: str) -> str:
        """
        替换SQL中的占位符
        
        Args:
            sql: 包含?占位符的SQL语句
            
        Returns:
            替换后的SQL语句（PostgreSQL使用%s，SQLite使用?）
        """
        if DB_TYPE == "postgresql":
            return sql.replace("?", "%s")
        return sql
    
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
            result = cursor.fetchone()
            value = self._extract_scalar_value(result)
            return value if value is not None else 0
    
    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据 ID 查找记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            记录字典或 None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = {placeholder}",
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
        placeholder = self._get_param_placeholder()
        sql = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit is not None:
            sql += f" LIMIT {placeholder}"
            params.append(limit)
        
        if offset is not None:
            sql += f" OFFSET {placeholder}"
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
        placeholder = self._get_param_placeholder()
        placeholders = ", ".join([placeholder] * len(columns))
        columns_str = ", ".join(columns)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if DB_TYPE == "postgresql":
                cursor.execute(
                    f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders}) RETURNING id",
                    list(data.values())
                )
                result = cursor.fetchone()
                value = self._extract_scalar_value(result)
                conn.commit()
                return value if value is not None else 0
            else:
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
        
        placeholder = self._get_param_placeholder()
        set_clause = ", ".join([f"{key} = {placeholder}" for key in data.keys()])
        values = list(data.values()) + [record_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE id = {placeholder}",
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
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = {placeholder}",
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

