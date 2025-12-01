"""
EmailCacheDAO - 邮件列表缓存表数据访问对象
"""

from typing import Any, Dict, List, Optional, Tuple
import logging

from .base_dao import BaseDAO, get_db_connection

logger = logging.getLogger(__name__)


class EmailCacheDAO(BaseDAO):
    """邮件列表缓存表 DAO"""
    
    def __init__(self):
        super().__init__("emails_cache")
        self.default_page_size = 100
        self.max_page_size = 500
    
    def cache_emails(self, email_account: str, emails: List[Dict[str, Any]]) -> bool:
        """
        批量缓存邮件列表（带LRU清理）
        
        Args:
            email_account: 邮箱账号
            emails: 邮件列表数据
            
        Returns:
            是否缓存成功
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for email in emails:
                    # 计算缓存大小（估算）
                    cache_size = (
                        len(email.get('subject') or '') +
                        len(email.get('from_email') or '') +
                        len(email.get('verification_code') or '')
                    )
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO emails_cache 
                        (email_account, message_id, folder, subject, from_email, date, 
                         is_read, has_attachments, sender_initial, verification_code, body_preview, cache_size, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        email_account,
                        email.get('message_id'),
                        email.get('folder'),
                        email.get('subject'),
                        email.get('from_email'),
                        email.get('date'),
                        1 if email.get('is_read') else 0,
                        1 if email.get('has_attachments') else 0,
                        email.get('sender_initial', '?'),
                        email.get('verification_code'),
                        email.get('body_preview'),
                        cache_size
                    ))
                
                conn.commit()
                logger.info(f"Cached {len(emails)} emails for account {email_account}")
            
            # 检查并触发LRU清理（延迟导入避免循环依赖）
            try:
                from dao.email_detail_cache_dao import EmailDetailCacheDAO
                detail_dao = EmailDetailCacheDAO()
                cache_stats = detail_dao.check_cache_size()
                if (cache_stats['emails_cache']['usage_percent'] > 90 or 
                    cache_stats['details_cache']['usage_percent'] > 90):
                    logger.info("Cache usage high, triggering LRU cleanup")
                    cleanup_result = detail_dao.cleanup_lru_cache()
                    logger.info(f"LRU cleanup completed: {cleanup_result}")
            except ImportError:
                pass  # 如果导入失败，跳过清理
            
            return True
        except Exception as e:
            logger.error(f"Error caching emails: {e}")
            return False
    
    def get_cached_emails(
        self,
        email_account: str,
        page: int = 1,
        page_size: Optional[int] = None,
        folder: Optional[str] = None,
        sender_search: Optional[str] = None,
        subject_search: Optional[str] = None,
        sort_by: str = 'date',
        sort_order: str = 'desc',
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        从缓存获取邮件列表（支持搜索、排序、分页、时间范围）
        
        Args:
            email_account: 邮箱账号
            page: 页码（从1开始）
            page_size: 每页数量
            folder: 文件夹过滤
            sender_search: 发件人模糊搜索
            subject_search: 主题模糊搜索
            sort_by: 排序字段（默认date）
            sort_order: 排序方向（asc或desc）
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            
        Returns:
            (邮件列表, 总数)
        """
        conditions = ["email_account = ?"]
        params = [email_account]
        
        if folder and folder != 'all':
            conditions.append("folder = ?")
            params.append(folder)
        
        if sender_search:
            conditions.append("from_email LIKE ?")
            params.append(f"%{sender_search}%")
        
        if subject_search:
            conditions.append("subject LIKE ?")
            params.append(f"%{subject_search}%")
            
        if start_time:
            conditions.append("date >= ?")
            params.append(start_time)
            
        if end_time:
            conditions.append("date <= ?")
            params.append(end_time)
        
        where_clause = self._build_where_clause(conditions, params)
        
        # 验证排序字段
        allowed_sort_fields = ['date', 'subject', 'from_email']
        if sort_by not in allowed_sort_fields:
            sort_by = 'date'
        
        # 验证排序方向
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        order_by = f"{sort_by} {sort_order.upper()}"
        
        # 获取总数
        total = self.count(where_clause, params)
        
        # 获取分页数据
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)
        offset = (page - 1) * page_size
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT message_id, folder, subject, from_email, date, 
                       is_read, has_attachments, sender_initial, verification_code, body_preview
                FROM emails_cache 
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """, params + [page_size, offset])
            
            rows = cursor.fetchall()
            
            # 更新访问统计（批量更新）
            if rows:
                message_ids = [row[0] for row in rows]
                placeholders = ','.join(['?'] * len(message_ids))
                cursor.execute(f"""
                    UPDATE emails_cache 
                    SET access_count = access_count + 1,
                    last_accessed_at = CURRENT_TIMESTAMP
                    WHERE email_account = ? AND message_id IN ({placeholders})
                """, [email_account] + message_ids)
            
            emails = []
            for row in rows:
                emails.append({
                    'message_id': row[0],
                    'folder': row[1],
                    'subject': row[2],
                    'from_email': row[3],
                    'date': row[4],
                    'is_read': bool(row[5]),
                    'has_attachments': bool(row[6]),
                    'sender_initial': row[7],
                    'verification_code': row[8],
                    'body_preview': row[9]
                })
            
            return emails, total
    
    def clear_by_account(self, email_account: str) -> bool:
        """
        清除指定账户的邮件缓存
        
        Args:
            email_account: 邮箱账号
            
        Returns:
            是否清除成功
        """
        return self.delete_by_condition("email_account = ?", [email_account]) > 0
    
    def delete_email(self, email_account: str, message_id: str) -> bool:
        """
        从缓存中删除指定邮件
        
        Args:
            email_account: 邮箱账号
            message_id: 邮件ID
            
        Returns:
            是否删除成功
        """
        return self.delete_by_condition(
            "email_account = ? AND message_id = ?",
            [email_account, message_id]
        ) > 0
    
    def get_count_by_account(self, email_account: str, folder: Optional[str] = None) -> int:
        """
        获取账户的邮件总数（用于检测新邮件）
        
        Args:
            email_account: 邮箱账号
            folder: 文件夹（可选）
            
        Returns:
            邮件总数
        """
        conditions = ["email_account = ?"]
        params = [email_account]
        
        if folder and folder != 'all':
            conditions.append("folder = ?")
            params.append(folder)
        
        where_clause = self._build_where_clause(conditions, params)
        return self.count(where_clause, params)

