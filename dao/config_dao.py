"""
ConfigDAO - 系统配置表数据访问对象
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from .base_dao import BaseDAO, get_db_connection

logger = logging.getLogger(__name__)


class ConfigDAO(BaseDAO):
    """系统配置表 DAO"""
    
    def __init__(self):
        super().__init__("system_config")
        self.default_page_size = 100
        self.max_page_size = 1000
    
    def get(self, key: str) -> Optional[str]:
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
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        获取所有系统配置
        
        Returns:
            配置列表
        """
        return self.find_all(order_by="key")
    
    def set(
        self,
        key: str,
        value: str,
        description: str = None
    ) -> bool:
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
    
    def delete_config(self, key: str) -> bool:
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
    
    def get_api_key(self) -> Optional[str]:
        """
        获取系统API Key
        
        Returns:
            API Key或None
        """
        return self.get("api_key")
    
    def set_api_key(self, api_key: str) -> bool:
        """
        设置系统API Key
        
        Args:
            api_key: API Key值
            
        Returns:
            是否设置成功
        """
        return self.set("api_key", api_key, "系统API Key，用于API访问认证")
    
    def init_default_api_key(self) -> str:
        """
        初始化默认API Key（如果不存在）
        
        Returns:
            API Key
        """
        import secrets
        
        existing_key = self.get_api_key()
        if existing_key:
            logger.info("API Key already exists")
            return existing_key
        
        # 生成新的API Key
        new_key = secrets.token_urlsafe(32)
        self.set_api_key(new_key)
        logger.info(f"Generated new API Key: {new_key}")
        
        return new_key

