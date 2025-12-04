"""
ShareTokenDAO - 分享码表数据访问对象
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .base_dao import BaseDAO, get_db_connection
from config import DB_TYPE
from logger_config import logger


class ShareTokenDAO(BaseDAO):
    """分享码表 DAO"""
    
    def __init__(self):
        super().__init__("share_tokens")
        self.default_page_size = 50
        self.max_page_size = 100
    
    def _serialize_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将字典中的 datetime 对象转换为 ISO 格式字符串（PostgreSQL 需要）
        
        Args:
            data: 包含 datetime 字段的字典
            
        Returns:
            转换后的字典
        """
        if DB_TYPE != "postgresql":
            return data
        
        result = dict(data)
        datetime_fields = ['start_time', 'end_time', 'expiry_time', 'created_at']
        
        for field in datetime_fields:
            if field in result and result[field] is not None:
                if isinstance(result[field], datetime):
                    result[field] = result[field].isoformat()
        
        return result
    
    def get_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取分享码信息
        
        Args:
            token: 分享码
            
        Returns:
            分享码信息字典或None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM share_tokens WHERE token = {placeholder}", (token,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                return self._serialize_datetime_fields(data)
            return None
    
    def create(
        self,
        token: str,
        email_account_id: str,
        start_time: str,
        end_time: Optional[str] = None,
        subject_keyword: Optional[str] = None,
        sender_keyword: Optional[str] = None,
        expiry_time: Optional[str] = None,
        is_active: bool = True,
        max_emails: int = 10
    ) -> int:
        """
        创建分享码
        
        Args:
            token: 分享码
            email_account_id: 邮箱账户ID
            start_time: 开始时间
            end_time: 结束时间
            subject_keyword: 主题关键词
            sender_keyword: 发件人关键词
            expiry_time: 过期时间
            is_active: 是否激活
            max_emails: 最多返回邮件数量
            
        Returns:
            新记录的 ID
        """
        # PostgreSQL 使用 True/False，SQLite 使用 1/0
        is_active_val = is_active if DB_TYPE == "postgresql" else (1 if is_active else 0)
        
        data = {
            'token': token,
            'email_account_id': email_account_id,
            'start_time': start_time,
            'end_time': end_time,
            'subject_keyword': subject_keyword,
            'sender_keyword': sender_keyword,
            'expiry_time': expiry_time,
            'is_active': is_active_val,
            'max_emails': max_emails
        }
        return self.insert(data)
    
    def update_token(self, token_id: int, **kwargs) -> bool:
        """
        更新分享码信息
        
        Args:
            token_id: 分享码ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        return self.update(token_id, kwargs)
    
    def delete_token(self, token_id: int) -> bool:
        """
        删除分享码
        
        Args:
            token_id: 分享码ID
            
        Returns:
            是否删除成功
        """
        return self.delete(token_id)
    
    def list_tokens(
        self,
        email_account_id: Optional[str] = None,
        account_search: Optional[str] = None,
        token_search: Optional[str] = None,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        列出分享码
        
        Args:
            email_account_id: 邮箱账户ID（精确匹配，可选）
            account_search: 账户模糊搜索（可选）
            token_search: Token模糊搜索（可选）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (分享码列表, 总数)
        """
        conditions = []
        params = []
        
        placeholder = self._get_param_placeholder()
        
        # 精确匹配账户（优先级高于模糊搜索）
        if email_account_id:
            conditions.append(f"email_account_id = {placeholder}")
            params.append(email_account_id)
        elif account_search:
            # 账户模糊搜索
            if DB_TYPE == "postgresql":
                conditions.append(f"email_account_id ILIKE {placeholder}")
            else:
                conditions.append(f"email_account_id LIKE {placeholder}")
            params.append(f"%{account_search}%")
        
        # Token模糊搜索
        if token_search:
            if DB_TYPE == "postgresql":
                conditions.append(f"token ILIKE {placeholder}")
            else:
                conditions.append(f"token LIKE {placeholder}")
            params.append(f"%{token_search}%")
        
        where_clause = self._build_where_clause(conditions, params)
        
        records, total = self.find_paginated(
            page=page,
            page_size=page_size,
            where_clause=where_clause,
            params=params,
            order_by="created_at DESC"
        )
        
        # 转换 datetime 字段为字符串（PostgreSQL 需要）
        serialized_records = [self._serialize_datetime_fields(record) for record in records]
        
        return serialized_records, total

