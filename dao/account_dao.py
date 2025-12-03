"""
AccountDAO - 账户表数据访问对象
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging

from .base_dao import BaseDAO, get_db_connection
from config import DB_TYPE

logger = logging.getLogger(__name__)


class AccountDAO(BaseDAO):
    """账户表 DAO"""
    
    def __init__(self):
        super().__init__("accounts")
        self.default_page_size = 10
        self.max_page_size = 100
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        根据邮箱地址获取账户信息
        
        Args:
            email: 邮箱地址
            
        Returns:
            账户信息字典或None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM accounts WHERE email = {placeholder}", (email,))
            row = cursor.fetchone()
            
            if row:
                account = dict(row)
                # 解析 tags JSON (PostgreSQL 可能会返回 dict，SQLite 返回 string)
                tags = account.get('tags')
                if isinstance(tags, str):
                    account['tags'] = json.loads(tags) if tags else []
                elif tags is None:
                    account['tags'] = []
                elif isinstance(tags, dict):
                    # PostgreSQL 可能返回空字典，转换为空列表
                    account['tags'] = []
                elif not isinstance(tags, list):
                    # 其他类型，转换为空列表
                    account['tags'] = []
                # 如果是 list，已经是正确的格式，不需要做任何处理
                
                return account
            return None
    
    def get_all(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
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
        placeholder = self._get_param_placeholder()
        conditions = []
        params = []
        
        if email_search:
            conditions.append(f"email LIKE {placeholder}")
            params.append(f"%{email_search}%")
        
        # 对于PostgreSQL，tags是jsonb类型，需要转换为文本才能使用LIKE
        # 对于SQLite，tags是TEXT类型，可以直接使用LIKE
        tags_column = "tags::text" if DB_TYPE == "postgresql" else "tags"
        
        if tag_search:
            conditions.append(f"{tags_column} LIKE {placeholder}")
            params.append(f"%{tag_search}%")
        
        where_clause = self._build_where_clause(conditions, params)
        
        # 使用稳定的排序：按创建时间倒序，如果创建时间相同或为NULL，则按ID倒序
        # 这样可以确保排序结果稳定
        if DB_TYPE == "postgresql":
            # PostgreSQL: 使用 COALESCE 处理 NULL 值，并使用 id 作为次要排序
            order_by = "created_at DESC, id DESC"
        else:
            # SQLite: 使用 COALESCE 处理 NULL 值，并使用 id 作为次要排序
            order_by = "created_at DESC, id DESC"
        
        records, total = self.find_paginated(
            page=page,
            page_size=page_size,
            where_clause=where_clause,
            params=params,
            order_by=order_by
        )
        
        # 解析 tags JSON
        for account in records:
            tags = account.get('tags')
            if isinstance(tags, str):
                account['tags'] = json.loads(tags) if tags else []
            elif tags is None:
                account['tags'] = []
            elif isinstance(tags, dict):
                # PostgreSQL 可能返回空字典，转换为空列表
                account['tags'] = []
            elif not isinstance(tags, list):
                # 其他类型，转换为空列表
                account['tags'] = []
        
        return records, total
    
    def get_by_filters(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
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
        """
        获取符合筛选条件的账户列表（支持分页和多维度筛选）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            email_search: 邮箱模糊搜索
            tag_search: 标签模糊搜索（已废弃，使用include_tags代替）
            include_tags: 必须包含的标签列表（同时包含所有指定标签）
            exclude_tags: 必须不包含的标签列表（不包含任何指定标签）
            refresh_status: 刷新状态筛选 (never_refreshed, failed, success, pending, all)
            time_filter: 时间过滤器 (today, week, month, custom)
            after_date: 自定义日期（用于custom时间过滤，ISO格式）
            refresh_start_date: 刷新起始日期（ISO格式）
            refresh_end_date: 刷新截止日期（ISO格式）
            
        Returns:
            (账户列表, 总数)
        """
        conditions = []
        params = []
        
        # 邮箱搜索
        placeholder = self._get_param_placeholder()
        if email_search:
            conditions.append(f"email LIKE {placeholder}")
            params.append(f"%{email_search}%")
        
        # 标签搜索（向后兼容，如果提供了tag_search，转换为include_tags）
        if tag_search and not include_tags:
            include_tags = [tag.strip() for tag in tag_search.split(",") if tag.strip()]
        
        # 对于PostgreSQL，tags是jsonb类型，需要转换为文本才能使用LIKE
        # 对于SQLite，tags是TEXT类型，可以直接使用LIKE
        tags_column = "tags::text" if DB_TYPE == "postgresql" else "tags"
        
        # 包含标签筛选（必须同时包含所有指定标签）
        if include_tags:
            for tag in include_tags:
                conditions.append(f"{tags_column} LIKE {placeholder}")
                params.append(f'%"{tag}"%')  # JSON格式的标签匹配
        
        # 排除标签筛选（必须不包含任何指定标签）
        if exclude_tags:
            for tag in exclude_tags:
                conditions.append(f"{tags_column} NOT LIKE {placeholder}")
                params.append(f'%"{tag}"%')  # JSON格式的标签匹配
        
        # 刷新状态筛选
        if refresh_status and refresh_status != 'all':
            if refresh_status == 'never_refreshed':
                conditions.append("last_refresh_time IS NULL")
            elif refresh_status == 'failed':
                conditions.append("refresh_status = 'failed'")
            elif refresh_status == 'success':
                conditions.append("refresh_status = 'success'")
            elif refresh_status == 'pending':
                conditions.append("refresh_status = 'pending'")
        
        # 时间范围筛选
        if time_filter:
            current_time = datetime.now()
            
            if time_filter == 'today':
                today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(f"(last_refresh_time IS NULL OR last_refresh_time < {placeholder})")
                params.append(today_start.isoformat())
            elif time_filter == 'week':
                week_ago = current_time - timedelta(days=7)
                conditions.append(f"(last_refresh_time IS NULL OR last_refresh_time < {placeholder})")
                params.append(week_ago.isoformat())
            elif time_filter == 'month':
                month_ago = current_time - timedelta(days=30)
                conditions.append(f"(last_refresh_time IS NULL OR last_refresh_time < {placeholder})")
                params.append(month_ago.isoformat())
            elif time_filter == 'custom' and after_date:
                conditions.append(f"(last_refresh_time IS NULL OR last_refresh_time < {placeholder})")
                params.append(after_date)
        
        # 自定义日期范围筛选
        if refresh_start_date and refresh_end_date:
            conditions.append(f"(last_refresh_time >= {placeholder} AND last_refresh_time <= {placeholder})")
            params.append(refresh_start_date)
            params.append(refresh_end_date)
            logger.info(f"[筛选] 添加日期范围筛选: {refresh_start_date} 至 {refresh_end_date}")
        
        where_clause = self._build_where_clause(conditions, params)
        
        logger.info(f"[筛选] SQL WHERE子句: {where_clause}")
        logger.info(f"[筛选] SQL参数: {params}")
        
        # 使用稳定的排序：按创建时间倒序，如果创建时间相同或为NULL，则按ID倒序
        # 这样可以确保排序结果稳定
        if DB_TYPE == "postgresql":
            # PostgreSQL: 使用 COALESCE 处理 NULL 值，并使用 id 作为次要排序
            order_by = "COALESCE(created_at, '1970-01-01'::timestamp) DESC, id DESC"
        else:
            # SQLite: 使用 COALESCE 处理 NULL 值，并使用 id 作为次要排序
            order_by = "COALESCE(created_at, '1970-01-01') DESC, id DESC"
        
        records, total = self.find_paginated(
            page=page,
            page_size=page_size,
            where_clause=where_clause,
            params=params,
            order_by=order_by
        )
        
        # 解析 tags JSON
        for account in records:
            tags = account.get('tags')
            if isinstance(tags, str):
                account['tags'] = json.loads(tags) if tags else []
            elif tags is None:
                account['tags'] = []
            elif isinstance(tags, dict):
                # PostgreSQL 可能返回空字典，转换为空列表
                account['tags'] = []
            elif not isinstance(tags, list):
                # 其他类型，转换为空列表
                account['tags'] = []
        
        logger.info(f"[筛选] 符合条件的总数: {total}")
        return records, total
    
    def create(
        self,
        email: str,
        refresh_token: str,
        client_id: str,
        tags: List[str] = None,
        api_method: str = "imap"
    ) -> Dict[str, Any]:
        """
        创建新账户
        
        Args:
            email: 邮箱地址
            refresh_token: 刷新令牌
            client_id: 客户端ID
            tags: 标签列表
            api_method: API方法
            
        Returns:
            创建的账户信息
        """
        tags = tags or []
        tags_json = json.dumps(tags, ensure_ascii=False)
        
        data = {
            'email': email,
            'refresh_token': refresh_token,
            'client_id': client_id,
            'tags': tags_json,
            'api_method': api_method
        }
        
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO accounts (email, refresh_token, client_id, tags, api_method)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (email, refresh_token, client_id, tags_json, api_method))
            conn.commit()
            
            logger.info(f"Created account: {email}")
            return self.get_by_email(email)
    
    def update_account(self, email: str, **kwargs) -> bool:
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
        placeholder = self._get_param_placeholder()
        set_clause = ", ".join([f"{key} = {placeholder}" for key in kwargs.keys()])
        values = list(kwargs.values()) + [email]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE accounts SET {set_clause} WHERE email = {placeholder}",
                values
            )
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated account: {email}")
            return success
    
    def delete_account(self, email: str) -> bool:
        """
        删除账户
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否删除成功
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM accounts WHERE email = {placeholder}", (email,))
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted account: {email}")
            return success
    
    def get_access_token(self, email: str) -> Optional[Dict[str, str]]:
        """
        获取账户的缓存 access token 信息
        
        Args:
            email: 邮箱地址
            
        Returns:
            包含 access_token 和 token_expires_at 的字典，如果不存在则返回 None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT access_token, token_expires_at FROM accounts WHERE email = {placeholder}",
                (email,)
            )
            row = cursor.fetchone()
            
            if row and row['access_token'] and row['token_expires_at']:
                return {
                    'access_token': row['access_token'],
                    'token_expires_at': row['token_expires_at']
                }
            return None
    
    def update_access_token(self, email: str, access_token: str, expires_at: str) -> bool:
        """
        更新账户的 access token 和过期时间
        
        Args:
            email: 邮箱地址
            access_token: OAuth2 访问令牌
            expires_at: 令牌过期时间（ISO格式字符串）
            
        Returns:
            是否更新成功
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE accounts 
                SET access_token = {placeholder}, token_expires_at = {placeholder}, updated_at = {placeholder}
                WHERE email = {placeholder}
                """,
                (access_token, expires_at, datetime.now().isoformat(), email)
            )
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated access token for account: {email}, expires at: {expires_at}")
            return success
    
    def get_random(
        self,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        随机获取账户列表（支持标签筛选和分页）
        
        Args:
            include_tags: 必须包含的标签列表
            exclude_tags: 必须不包含的标签列表
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            (账户列表, 总数)
        """
        placeholder = self._get_param_placeholder()
        conditions = []
        params = []
        
        # 对于PostgreSQL，tags是jsonb类型，需要转换为文本才能使用LIKE
        # 对于SQLite，tags是TEXT类型，可以直接使用LIKE
        tags_column = "tags::text" if DB_TYPE == "postgresql" else "tags"
        
        # 包含标签筛选
        if include_tags:
            for tag in include_tags:
                conditions.append(f"{tags_column} LIKE {placeholder}")
                params.append(f'%"{tag}"%')  # JSON格式的标签匹配
        
        # 排除标签筛选
        if exclude_tags:
            for tag in exclude_tags:
                conditions.append(f"{tags_column} NOT LIKE {placeholder}")
                params.append(f'%"{tag}"%')  # JSON格式的标签匹配
        
        where_clause = self._build_where_clause(conditions, params)
        
        # 获取总数
        total = self.count(where_clause, params)
        
        # 获取随机分页数据
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)
        offset = (page - 1) * page_size
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM accounts WHERE {where_clause} ORDER BY RANDOM() LIMIT {placeholder} OFFSET {placeholder}",
                params + [page_size, offset]
            )
            rows = cursor.fetchall()
            
            accounts = []
            for row in rows:
                account = dict(row)
                # 解析 tags JSON
                tags = account.get('tags')
                if isinstance(tags, str):
                    account['tags'] = json.loads(tags) if tags else []
                elif tags is None:
                    account['tags'] = []
                accounts.append(account)
            
            logger.info(f"Random accounts query: {len(accounts)} accounts found (total: {total})")
            return accounts, total
    
    def add_tag(self, email: str, tag: str) -> bool:
        """
        为账户添加标签（如果标签已存在则不处理）
        
        Args:
            email: 邮箱地址
            tag: 要添加的标签
            
        Returns:
            是否成功（账户不存在返回False）
        """
        account = self.get_by_email(email)
        
        if not account:
            logger.warning(f"Account {email} not found, cannot add tag")
            return False
        
        current_tags = account.get('tags', [])
        
        # 如果标签已存在，不处理
        if tag in current_tags:
            logger.info(f"Tag '{tag}' already exists for account {email}")
            return True
        
        # 添加新标签
        current_tags.append(tag)
        
        # 更新账户
        success = self.update_account(email, tags=current_tags)
        
        if success:
            logger.info(f"Added tag '{tag}' to account {email}")
        
        return success

