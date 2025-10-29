"""
邮件解析器

解析RFC822格式的邮件消息
"""

import email
import logging
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Optional, Tuple

from src.config.constants import EmailFolder, EmailStatus
from src.domain.entities import EmailMessage
from src.domain.exceptions import EmailParseException
from src.domain.value_objects import EmailAddress

logger = logging.getLogger(__name__)


class EmailParser:
    """邮件解析器"""
    
    @staticmethod
    def parse_email(
        raw_email: bytes,
        folder: EmailFolder = EmailFolder.INBOX
    ) -> EmailMessage:
        """
        解析原始邮件数据为EmailMessage实体
        
        Args:
            raw_email: 原始邮件字节数据
            folder: 邮件所在文件夹
            
        Returns:
            EmailMessage: 邮件实体
            
        Raises:
            EmailParseException: 解析失败
        """
        try:
            # 解析邮件
            msg = email.message_from_bytes(raw_email)
            
            # 提取基本信息
            message_id = EmailParser._get_message_id(msg)
            subject = EmailParser._decode_header(msg.get("Subject", ""))
            sender = EmailParser._parse_email_address(msg.get("From", ""))
            date = EmailParser._parse_date(msg.get("Date"))
            
            # 提取收件人
            recipients = EmailParser._parse_email_addresses(msg.get("To", ""))
            cc = EmailParser._parse_email_addresses(msg.get("Cc", ""))
            bcc = EmailParser._parse_email_addresses(msg.get("Bcc", ""))
            
            # 提取正文
            body_text, body_html = EmailParser._extract_body(msg)
            
            # 提取其他信息
            size = len(raw_email)
            has_attachments = EmailParser._has_attachments(msg)
            flags = EmailParser._extract_flags(msg)
            
            # 确定邮件状态
            status = EmailStatus.READ if "\\Seen" in flags else EmailStatus.UNREAD
            
            # 创建邮件实体
            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                date=date,
                folder=folder,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                body_text=body_text,
                body_html=body_html,
                status=status,
                size=size,
                has_attachments=has_attachments,
                flags=flags
            )
            
        except Exception as e:
            logger.error(f"Failed to parse email: {str(e)}")
            raise EmailParseException("unknown", str(e))
    
    @staticmethod
    def _get_message_id(msg: email.message.Message) -> str:
        """获取消息ID"""
        message_id = msg.get("Message-ID", "")
        if not message_id:
            # 如果没有Message-ID，使用Subject和Date生成
            subject = msg.get("Subject", "no-subject")
            date = msg.get("Date", "no-date")
            message_id = f"<{hash(subject + date)}@generated>"
        return message_id.strip("<>")
    
    @staticmethod
    def _decode_header(header: str) -> str:
        """
        解码邮件头
        
        处理编码的邮件头（如=?UTF-8?B?...?=）
        """
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            result_parts = []
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    # 解码字节
                    if encoding:
                        result_parts.append(part.decode(encoding, errors="replace"))
                    else:
                        result_parts.append(part.decode("utf-8", errors="replace"))
                else:
                    result_parts.append(str(part))
            
            return " ".join(result_parts)
        except Exception as e:
            logger.warning(f"Failed to decode header: {str(e)}")
            return str(header)
    
    @staticmethod
    def _parse_email_address(address_str: str) -> EmailAddress:
        """
        解析单个邮箱地址
        
        Args:
            address_str: 邮箱地址字符串（可能包含名称）
            
        Returns:
            EmailAddress: 邮箱地址值对象
        """
        if not address_str:
            return EmailAddress.create("unknown@example.com")
        
        try:
            # 解码头部
            decoded = EmailParser._decode_header(address_str)
            
            # 提取邮箱地址（格式："Name <email@example.com>" 或 "email@example.com"）
            if "<" in decoded and ">" in decoded:
                # 提取<>中的邮箱
                start = decoded.index("<")
                end = decoded.index(">")
                email_part = decoded[start + 1:end].strip()
            else:
                email_part = decoded.strip()
            
            return EmailAddress.create(email_part)
        except Exception as e:
            logger.warning(f"Failed to parse email address '{address_str}': {str(e)}")
            return EmailAddress.create("unknown@example.com")
    
    @staticmethod
    def _parse_email_addresses(addresses_str: str) -> List[EmailAddress]:
        """
        解析多个邮箱地址
        
        Args:
            addresses_str: 逗号分隔的邮箱地址字符串
            
        Returns:
            List[EmailAddress]: 邮箱地址列表
        """
        if not addresses_str:
            return []
        
        # 简单分割（实际可能需要更复杂的解析）
        addresses = []
        for addr in addresses_str.split(","):
            addr = addr.strip()
            if addr:
                try:
                    addresses.append(EmailParser._parse_email_address(addr))
                except Exception as e:
                    logger.warning(f"Failed to parse address '{addr}': {str(e)}")
        
        return addresses
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> datetime:
        """
        解析邮件日期
        
        Args:
            date_str: 日期字符串
            
        Returns:
            datetime: 日期时间对象
        """
        if not date_str:
            return datetime.utcnow()
        
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {str(e)}")
            return datetime.utcnow()
    
    @staticmethod
    def _extract_body(msg: email.message.Message) -> Tuple[Optional[str], Optional[str]]:
        """
        提取邮件正文
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (纯文本正文, HTML正文)
        """
        body_text = None
        body_html = None
        
        try:
            if msg.is_multipart():
                # 多部分邮件
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # 跳过附件
                    if "attachment" in content_disposition:
                        continue
                    
                    # 提取正文
                    if content_type == "text/plain" and not body_text:
                        body_text = EmailParser._decode_payload(part)
                    elif content_type == "text/html" and not body_html:
                        body_html = EmailParser._decode_payload(part)
            else:
                # 单部分邮件
                content_type = msg.get_content_type()
                payload = EmailParser._decode_payload(msg)
                
                if content_type == "text/plain":
                    body_text = payload
                elif content_type == "text/html":
                    body_html = payload
        except Exception as e:
            logger.warning(f"Failed to extract body: {str(e)}")
        
        return body_text, body_html
    
    @staticmethod
    def _decode_payload(part: email.message.Message) -> str:
        """
        解码邮件部分的载荷
        
        Args:
            part: 邮件部分
            
        Returns:
            str: 解码后的文本
        """
        try:
            payload = part.get_payload(decode=True)
            if payload is None:
                return ""
            
            # 获取字符集
            charset = part.get_content_charset() or "utf-8"
            
            # 解码
            return payload.decode(charset, errors="replace")
        except Exception as e:
            logger.warning(f"Failed to decode payload: {str(e)}")
            return ""
    
    @staticmethod
    def _has_attachments(msg: email.message.Message) -> bool:
        """
        检查邮件是否有附件
        
        Args:
            msg: 邮件消息
            
        Returns:
            bool: 是否有附件
        """
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in content_disposition:
                        return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def _extract_flags(msg: email.message.Message) -> List[str]:
        """
        提取IMAP标志（简化实现）
        
        Args:
            msg: 邮件消息
            
        Returns:
            List[str]: 标志列表
        """
        # 注意：IMAP标志通常不在邮件本身，而是在IMAP服务器返回的元数据中
        # 这里返回空列表，实际需要从IMAP响应中提取
        return []

