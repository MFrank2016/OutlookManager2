"""
邮件工具模块

提供邮件处理相关的辅助函数，如邮件头解码、内容提取等
"""

import email
import logging
from email.header import decode_header

# 获取日志记录器
logger = logging.getLogger(__name__)


def decode_header_value(header_value: str) -> str:
    """
    解码邮件头字段

    处理各种编码格式的邮件头部信息，如Subject、From等

    Args:
        header_value: 原始头部值

    Returns:
        str: 解码后的字符串
    """
    if not header_value:
        return ""

    try:
        decoded_parts = decode_header(str(header_value))
        decoded_string = ""

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    # 使用指定编码或默认UTF-8解码
                    encoding = charset if charset else "utf-8"
                    decoded_string += part.decode(encoding, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    # 编码失败时使用UTF-8强制解码
                    decoded_string += part.decode("utf-8", errors="replace")
            else:
                decoded_string += str(part)

        return decoded_string.strip()
    except Exception as e:
        logger.warning(f"Failed to decode header value '{header_value}': {e}")
        return str(header_value) if header_value else ""


def extract_email_content(email_message: email.message.EmailMessage) -> tuple[str, str]:
    """
    提取邮件的纯文本和HTML内容

    Args:
        email_message: 邮件消息对象

    Returns:
        tuple[str, str]: (纯文本内容, HTML内容)
    """
    body_plain = ""
    body_html = ""

    try:
        if email_message.is_multipart():
            # 处理多部分邮件
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 跳过附件
                if "attachment" not in content_disposition.lower():
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)

                        if payload:
                            decoded_content = payload.decode(charset, errors="replace")

                            if content_type == "text/plain" and not body_plain:
                                body_plain = decoded_content
                            elif content_type == "text/html" and not body_html:
                                body_html = decoded_content

                    except Exception as e:
                        logger.warning(
                            f"Failed to decode email part ({content_type}): {e}"
                        )
        else:
            # 处理单部分邮件
            try:
                charset = email_message.get_content_charset() or "utf-8"
                payload = email_message.get_payload(decode=True)

                if payload:
                    content = payload.decode(charset, errors="replace")
                    content_type = email_message.get_content_type()

                    if content_type == "text/plain":
                        body_plain = content
                    elif content_type == "text/html":
                        body_html = content
                    else:
                        # 默认当作纯文本处理
                        body_plain = content

            except Exception as e:
                logger.warning(f"Failed to decode single-part email body: {e}")

    except Exception as e:
        logger.error(f"Error extracting email content: {e}")

    return body_plain.strip(), body_html.strip()

