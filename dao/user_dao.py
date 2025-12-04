"""
UserDAO - 用户表数据访问对象
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .base_dao import BaseDAO, get_db_connection
from config import DB_TYPE
from logger_config import logger


class UserDAO(BaseDAO):
    """用户表 DAO"""
    
    def __init__(self):
        super().__init__("users")
        self.default_page_size = 50
        self.max_page_size = 1000
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典或None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM users WHERE username = {placeholder}", (username,))
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                # 解析 JSON 字段 (PostgreSQL 会自动解析为 list，SQLite 返回 string)
                bound_accounts = user.get('bound_accounts')
                if isinstance(bound_accounts, str):
                    user['bound_accounts'] = json.loads(bound_accounts or '[]')
                elif bound_accounts is None:
                    user['bound_accounts'] = []
                
                permissions = user.get('permissions')
                if isinstance(permissions, str):
                    user['permissions'] = json.loads(permissions or '[]')
                elif permissions is None:
                    user['permissions'] = []
                    
                return user
            return None
    
    def get_all(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        role_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取所有用户列表（支持分页和筛选）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            role_filter: 角色筛选 (admin/user)
            search: 搜索关键词（用户名或邮箱）
            
        Returns:
            (用户列表, 总数)
        """
        placeholder = self._get_param_placeholder()
        conditions = []
        params = []
        
        if role_filter:
            conditions.append(f"role = {placeholder}")
            params.append(role_filter)
        
        if search:
            conditions.append(f"(username LIKE {placeholder} OR email LIKE {placeholder})")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_clause = self._build_where_clause(conditions, params)
        
        records, total = self.find_paginated(
            page=page,
            page_size=page_size,
            where_clause=where_clause,
            params=params,
            order_by="created_at DESC"
        )
        
        # 解析 JSON 字段
        for user in records:
            # PostgreSQL 会自动解析为 list，SQLite 返回 string
            bound_accounts = user.get('bound_accounts')
            if isinstance(bound_accounts, str):
                user['bound_accounts'] = json.loads(bound_accounts or '[]')
            elif bound_accounts is None:
                user['bound_accounts'] = []
            
            permissions = user.get('permissions')
            if isinstance(permissions, str):
                user['permissions'] = json.loads(permissions or '[]')
            elif permissions is None:
                user['permissions'] = []
        
        return records, total
    
    def create(
        self,
        username: str,
        password_hash: str,
        email: str = None,
        role: str = "user",
        bound_accounts: List[str] = None,
        permissions: List[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        创建用户账户
        
        Args:
            username: 用户名
            password_hash: 密码哈希
            email: 邮箱（可选）
            role: 角色 (admin/user)
            bound_accounts: 绑定的邮箱账户列表
            permissions: 权限列表
            is_active: 账户是否启用
            
        Returns:
            创建的用户信息
        """
        from permissions import get_default_permissions
        
        bound_accounts = bound_accounts or []
        permissions = permissions or get_default_permissions(role)
        
        bound_accounts_json = json.dumps(bound_accounts, ensure_ascii=False)
        permissions_json = json.dumps(permissions, ensure_ascii=False)
        
        data = {
            'username': username,
            'password_hash': password_hash,
            'email': email,
            'role': role,
            'bound_accounts': bound_accounts_json,
            'permissions': permissions_json,
            'is_active': 1 if is_active else 0
        }
        
        placeholder = self._get_param_placeholder()
        # PostgreSQL 使用 True/False，SQLite 使用 1/0
        is_active_val = is_active if DB_TYPE == "postgresql" else (1 if is_active else 0)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO users (username, password_hash, email, role, bound_accounts, permissions, is_active)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                username, password_hash, email, role,
                bound_accounts_json, permissions_json, is_active_val
            ))
            conn.commit()
            logger.info(f"Created user: {username} (role: {role})")
            return self.get_by_username(username)
    
    def update_user(self, username: str, **kwargs) -> bool:
        """
        更新用户信息
        
        Args:
            username: 用户名
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        if not kwargs:
            return False
        
        # 防止通过通用更新方法直接更新密码，必须使用专门的 update_password 方法
        if 'password_hash' in kwargs or 'password' in kwargs:
            logger.warning(f"Attempted to update password for {username} via update_user method. Use update_password instead.")
            raise ValueError("密码不能通过 update_user 方法更新，请使用专门的 update_password 方法")
        
        # 处理 JSON 字段
        if 'bound_accounts' in kwargs:
            kwargs['bound_accounts'] = json.dumps(kwargs['bound_accounts'], ensure_ascii=False)
        
        if 'permissions' in kwargs:
            kwargs['permissions'] = json.dumps(kwargs['permissions'], ensure_ascii=False)
        
        # 构建 UPDATE 语句
        placeholder = self._get_param_placeholder()
        set_clause = ", ".join([f"{key} = {placeholder}" for key in kwargs.keys()])
        values = list(kwargs.values()) + [username]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE users SET {set_clause} WHERE username = {placeholder}",
                values
            )
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated user: {username}")
            return success
    
    def update_login_time(self, username: str) -> bool:
        """
        更新用户最后登录时间
        
        Args:
            username: 用户名
            
        Returns:
            是否更新成功
        """
        return self.update_user(username, last_login=datetime.now().isoformat())
    
    def update_password(self, username: str, new_password_hash: str) -> bool:
        """
        更新用户密码
        
        Args:
            username: 用户名
            new_password_hash: 新密码哈希
            
        Returns:
            是否更新成功
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE users SET password_hash = {placeholder} WHERE username = {placeholder}",
                (new_password_hash, username)
            )
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated password for user: {username}")
            return success
    
    def delete_user(self, username: str) -> bool:
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            是否删除成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_param_placeholder()
            cursor.execute(f"DELETE FROM users WHERE username = {placeholder}", (username,))
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted user: {username}")
            return success
    
    def get_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        按角色获取用户列表
        
        Args:
            role: 角色 (admin/user)
            
        Returns:
            用户列表
        """
        users, _ = self.get_all(role_filter=role, page_size=1000)
        return users

