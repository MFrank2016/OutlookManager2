"""
BatchImportTaskDAO - 批量导入任务表数据访问对象
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_dao import BaseDAO, get_db_connection
from logger_config import logger


class BatchImportTaskDAO(BaseDAO):
    """批量导入任务表 DAO"""
    
    def __init__(self):
        super().__init__("batch_import_tasks")
        self.default_page_size = 20
        self.max_page_size = 100
    
    def get_by_task_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取批量导入任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典或None
        """
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM batch_import_tasks WHERE task_id = {placeholder}", (task_id,))
            row = cursor.fetchone()
            if row:
                task = dict(row)
                # 解析 tags JSON (PostgreSQL 会自动解析为 list，SQLite 返回 string)
                tags = task.get('tags')
                if isinstance(tags, str):
                    task['tags'] = json.loads(tags) if tags else []
                elif tags is None:
                    task['tags'] = []
                # 如果是 list，已经是正确的格式，不需要做任何处理
                
                return task
            return None
    
    def create(
        self,
        task_id: str,
        total_count: int,
        api_method: str = "imap",
        tags: List[str] = None,
        created_by: str = None
    ) -> bool:
        """
        创建批量导入任务
        
        Args:
            task_id: 任务ID
            total_count: 总数量
            api_method: API方法 (imap/graph)
            tags: 标签列表
            created_by: 创建者用户名
            
        Returns:
            是否创建成功
        """
        try:
            tags_json = json.dumps(tags or [])
            data = {
                'task_id': task_id,
                'total_count': total_count,
                'api_method': api_method,
                'tags': tags_json,
                'created_by': created_by
            }
            self.insert(data)
            logger.info(f"Created batch import task: {task_id}, total: {total_count}")
            return True
        except Exception as e:
            logger.error(f"Error creating batch import task: {e}")
            return False
    
    def update_progress(
        self,
        task_id: str,
        success_count: int = None,
        failed_count: int = None,
        processed_count: int = None,
        status: str = None
    ) -> bool:
        """
        更新批量导入任务进度
        
        Args:
            task_id: 任务ID
            success_count: 成功数量
            failed_count: 失败数量
            processed_count: 已处理数量
            status: 状态 (pending, processing, completed, failed)
            
        Returns:
            是否更新成功
        """
        try:
            updates = {}
            
            if success_count is not None:
                updates['success_count'] = success_count
            if failed_count is not None:
                updates['failed_count'] = failed_count
            if processed_count is not None:
                updates['processed_count'] = processed_count
            if status:
                updates['status'] = status
                if status == 'completed' or status == 'failed':
                    updates['completed_at'] = datetime.now().isoformat()
            
            updates['updated_at'] = datetime.now().isoformat()
            
            placeholder = self._get_param_placeholder()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{key} = {placeholder}" for key in updates.keys()])
                values = list(updates.values()) + [task_id]
                
                cursor.execute(
                    f"UPDATE batch_import_tasks SET {set_clause} WHERE task_id = {placeholder}",
                    values
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating batch import task progress: {e}")
            return False


class BatchImportTaskItemDAO(BaseDAO):
    """批量导入任务项表 DAO"""
    
    def __init__(self):
        super().__init__("batch_import_task_items")
        self.default_page_size = 100
        self.max_page_size = 1000
    
    def add_items(
        self,
        task_id: str,
        items: List[Dict[str, str]]
    ) -> bool:
        """
        添加批量导入任务项
        
        Args:
            task_id: 任务ID
            items: 任务项列表，每个项包含 email, refresh_token, client_id
            
        Returns:
            是否添加成功
        """
        placeholder = self._get_param_placeholder()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for item in items:
                    cursor.execute(f"""
                        INSERT INTO batch_import_task_items 
                        (task_id, email, refresh_token, client_id)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                    """, (task_id, item['email'], item['refresh_token'], item['client_id']))
                conn.commit()
                logger.info(f"Added {len(items)} items to batch import task: {task_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding batch import task items: {e}")
            return False
    
    def get_by_task_id(
        self,
        task_id: str,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取批量导入任务项列表
        
        Args:
            task_id: 任务ID
            status: 状态筛选（可选）
            
        Returns:
            任务项列表
        """
        placeholder = self._get_param_placeholder()
        conditions = [f"task_id = {placeholder}"]
        params = [task_id]
        
        if status:
            conditions.append(f"status = {placeholder}")
            params.append(status)
        
        where_clause = self._build_where_clause(conditions, params)
        
        return self.find_all(
            where_clause=where_clause,
            params=params,
            order_by="created_at"
        )
    
    def update_item(
        self,
        task_id: str,
        email: str,
        status: str,
        error_message: str = None
    ) -> bool:
        """
        更新批量导入任务项状态
        
        Args:
            task_id: 任务ID
            email: 邮箱地址
            status: 状态 (pending, success, failed)
            error_message: 错误消息
            
        Returns:
            是否更新成功
        """
        placeholder = self._get_param_placeholder()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE batch_import_task_items 
                    SET status = {placeholder}, error_message = {placeholder}, processed_at = {placeholder}
                    WHERE task_id = {placeholder} AND email = {placeholder}
                """, (status, error_message, datetime.now().isoformat(), task_id, email))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating batch import task item: {e}")
            return False

