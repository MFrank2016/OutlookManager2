"""
EmailDetailCacheDAO - 邮件详情缓存表数据访问对象
"""

from typing import Any, Dict, List, Optional
import logging

from .base_dao import BaseDAO, get_db_connection

# 导入压缩工具函数（从 database 模块）
try:
    from database import compress_text, decompress_text
except ImportError:
    # 如果无法导入，定义本地版本（避免循环导入）
    import zlib
    import base64
    from typing import Optional
    from config import COMPRESS_BODY_THRESHOLD
    
    def compress_text(text: Optional[str]) -> Optional[str]:
        if not text or len(text) < COMPRESS_BODY_THRESHOLD:
            return text
        try:
            compressed = zlib.compress(text.encode('utf-8'))
            encoded = base64.b64encode(compressed).decode('utf-8')
            return encoded
        except Exception:
            return text
    
    def decompress_text(text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        try:
            decoded = base64.b64decode(text.encode('utf-8'))
            decompressed = zlib.decompress(decoded).decode('utf-8')
            return decompressed
        except Exception:
            return text

logger = logging.getLogger(__name__)


class EmailDetailCacheDAO(BaseDAO):
    """邮件详情缓存表 DAO"""
    
    def __init__(self):
        super().__init__("email_details_cache")
        self.default_page_size = 100
        self.max_page_size = 500
    
    def cache_detail(self, email_account: str, email_detail: Dict[str, Any]) -> bool:
        """
        缓存单封邮件详情（带压缩）
        
        Args:
            email_account: 邮箱账号
            email_detail: 邮件详情数据
            
        Returns:
            是否缓存成功
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 压缩邮件正文
                body_plain = email_detail.get('body_plain')
                body_html = email_detail.get('body_html')
                
                original_size = (len(body_plain) if body_plain else 0) + (len(body_html) if body_html else 0)
                
                compressed_plain = compress_text(body_plain)
                compressed_html = compress_text(body_html)
                
                compressed_size = (len(compressed_plain) if compressed_plain else 0) + (len(compressed_html) if compressed_html else 0)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO email_details_cache 
                    (email_account, message_id, subject, from_email, to_email, 
                     date, body_plain, body_html, verification_code, body_size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    email_account,
                    email_detail.get('message_id'),
                    email_detail.get('subject'),
                    email_detail.get('from_email'),
                    email_detail.get('to_email'),
                    email_detail.get('date'),
                    compressed_plain,
                    compressed_html,
                    email_detail.get('verification_code'),
                    compressed_size
                ))
                
                conn.commit()
                
                if original_size > 0:
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    logger.info(f"Cached email detail for {email_account}: {email_detail.get('message_id')} "
                               f"(compressed {original_size} -> {compressed_size} bytes, {compression_ratio:.1f}% reduction)")
                else:
                    logger.info(f"Cached email detail for {email_account}: {email_detail.get('message_id')}")
                
                return True
        except Exception as e:
            logger.error(f"Error caching email detail: {e}")
            return False
    
    def get_cached_detail(self, email_account: str, message_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的邮件详情（自动解压缩）
        
        Args:
            email_account: 邮箱账号
            message_id: 邮件ID
            
        Returns:
            邮件详情字典或None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 更新访问统计
            cursor.execute("""
                UPDATE email_details_cache 
                SET access_count = access_count + 1,
                    last_accessed_at = CURRENT_TIMESTAMP
                WHERE email_account = ? AND message_id = ?
            """, (email_account, message_id))
            
            cursor.execute("""
                SELECT message_id, subject, from_email, to_email, date, 
                       body_plain, body_html, verification_code
                FROM email_details_cache 
                WHERE email_account = ? AND message_id = ?
            """, (email_account, message_id))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'message_id': row[0],
                    'subject': row[1],
                    'from_email': row[2],
                    'to_email': row[3],
                    'date': row[4],
                    'body_plain': decompress_text(row[5]),
                    'body_html': decompress_text(row[6]),
                    'verification_code': row[7]
                }
            return None
    
    def clear_by_account(self, email_account: str) -> bool:
        """
        清除指定账户的邮件详情缓存
        
        Args:
            email_account: 邮箱账号
            
        Returns:
            是否清除成功
        """
        return self.delete_by_condition("email_account = ?", [email_account]) > 0
    
    def delete_email(self, email_account: str, message_id: str) -> bool:
        """
        从缓存中删除指定邮件详情
        
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
    
    def check_cache_size(self) -> Dict[str, Any]:
        """
        检查缓存大小和记录数
        
        Returns:
            缓存统计信息字典
        """
        from config import MAX_CACHE_SIZE_MB, MAX_EMAILS_CACHE_COUNT, MAX_EMAIL_DETAILS_CACHE_COUNT
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取数据库文件大小
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size_bytes = cursor.fetchone()[0]
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            # 获取邮件列表缓存统计
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(cache_size), 0) FROM emails_cache")
            emails_count, emails_size = cursor.fetchone()
            
            # 获取邮件详情缓存统计
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(body_size), 0) FROM email_details_cache")
            details_count, details_size = cursor.fetchone()
            
            return {
                'db_size_mb': round(db_size_mb, 2),
                'max_size_mb': MAX_CACHE_SIZE_MB,
                'size_usage_percent': round((db_size_mb / MAX_CACHE_SIZE_MB) * 100, 2),
                'emails_cache': {
                    'count': emails_count,
                    'max_count': MAX_EMAILS_CACHE_COUNT,
                    'size_bytes': emails_size,
                    'usage_percent': round((emails_count / MAX_EMAILS_CACHE_COUNT) * 100, 2)
                },
                'details_cache': {
                    'count': details_count,
                    'max_count': MAX_EMAIL_DETAILS_CACHE_COUNT,
                    'size_bytes': details_size,
                    'usage_percent': round((details_count / MAX_EMAIL_DETAILS_CACHE_COUNT) * 100, 2)
                }
            }
    
    def cleanup_lru_cache(self) -> Dict[str, int]:
        """
        基于LRU策略清理缓存
        
        当缓存超过阈值时，删除最少访问的20%记录
        保留 access_count 高和 last_accessed_at 新的记录
        
        Returns:
            清理统计信息
        """
        from config import (
            MAX_EMAILS_CACHE_COUNT, 
            MAX_EMAIL_DETAILS_CACHE_COUNT,
            LRU_CLEANUP_THRESHOLD
        )
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                deleted_emails = 0
                deleted_details = 0
                
                # 检查邮件列表缓存是否需要清理
                cursor.execute("SELECT COUNT(*) FROM emails_cache")
                emails_count = cursor.fetchone()[0]
                
                if emails_count > MAX_EMAILS_CACHE_COUNT * LRU_CLEANUP_THRESHOLD:
                    # 删除最少访问的20%
                    delete_count = int(emails_count * 0.2)
                    cursor.execute("""
                        DELETE FROM emails_cache 
                        WHERE id IN (
                            SELECT id FROM emails_cache 
                            ORDER BY 
                                COALESCE(access_count, 0) ASC,
                                COALESCE(last_accessed_at, created_at) ASC
                            LIMIT ?
                        )
                    """, (delete_count,))
                    deleted_emails = cursor.rowcount
                    logger.info(f"LRU cleanup: deleted {deleted_emails} emails from cache")
                
                # 检查邮件详情缓存是否需要清理
                cursor.execute("SELECT COUNT(*) FROM email_details_cache")
                details_count = cursor.fetchone()[0]
                
                if details_count > MAX_EMAIL_DETAILS_CACHE_COUNT * LRU_CLEANUP_THRESHOLD:
                    # 删除最少访问的20%
                    delete_count = int(details_count * 0.2)
                    cursor.execute("""
                        DELETE FROM email_details_cache 
                        WHERE id IN (
                            SELECT id FROM email_details_cache 
                            ORDER BY 
                                COALESCE(access_count, 0) ASC,
                                COALESCE(last_accessed_at, created_at) ASC
                            LIMIT ?
                        )
                    """, (delete_count,))
                    deleted_details = cursor.rowcount
                    logger.info(f"LRU cleanup: deleted {deleted_details} email details from cache")
                
                conn.commit()
                
                return {
                    'deleted_emails': deleted_emails,
                    'deleted_details': deleted_details,
                    'remaining_emails': emails_count - deleted_emails,
                    'remaining_details': details_count - deleted_details
                }
        except Exception as e:
            logger.error(f"Error during LRU cleanup: {e}")
            return {
                'deleted_emails': 0,
                'deleted_details': 0,
                'error': str(e)
            }

