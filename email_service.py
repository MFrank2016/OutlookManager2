"""
邮件服务模块

提供邮件列表获取、邮件详情查询等服务
"""

import asyncio
import email
import logging
import re
from datetime import datetime
from itertools import groupby
from typing import Optional

from email.utils import parsedate_to_datetime
from fastapi import HTTPException

import database as db
from cache_service import get_cache_key, get_cached_emails, set_cached_emails
from email_utils import decode_header_value, extract_email_content
from imap_pool import imap_pool
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse
from oauth_service import get_access_token
from verification_code_detector import detect_verification_code

# 获取日志记录器
logger = logging.getLogger(__name__)


async def list_emails(
    credentials: AccountCredentials,
    folder: str,
    page: int,
    page_size: int,
    force_refresh: bool = False,
    sender_search: Optional[str] = None,
    subject_search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
) -> EmailListResponse:
    """获取邮件列表 - 优化版本（支持SQLite缓存、搜索、排序）"""

    # 优先从 SQLite 缓存获取
    if not force_refresh:
        try:
            cached_emails, total = db.get_cached_emails(
                email_account=credentials.email,
                page=page,
                page_size=page_size,
                folder=folder if folder != 'all' else None,
                sender_search=sender_search,
                subject_search=subject_search,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            if cached_emails:
                logger.info(f"Returning {len(cached_emails)} cached emails from SQLite for {credentials.email}")
                email_items = [
                    EmailItem(**email) for email in cached_emails
                ]
                return EmailListResponse(
                    email_id=credentials.email,
                    folder_view=folder,
                    page=page,
                    page_size=page_size,
                    total_emails=total,
                    emails=email_items,
                )
        except Exception as e:
            logger.warning(f"Failed to load from cache, fetching from IMAP: {e}")

    # 如果没有缓存或强制刷新，从 IMAP 获取
    access_token = await get_access_token(credentials)

    def _sync_list_emails():
        imap_client = None
        try:
            # 从连接池获取连接
            imap_client = imap_pool.get_connection(credentials.email, access_token)

            all_emails_data = []

            # 根据folder参数决定要获取的文件夹
            folders_to_check = []
            if folder == "inbox":
                folders_to_check = ["INBOX"]
            elif folder == "junk":
                folders_to_check = ["Junk"]
            else:  # folder == "all"
                folders_to_check = ["INBOX", "Junk"]

            for folder_name in folders_to_check:
                try:
                    # 选择文件夹
                    imap_client.select(f'"{folder_name}"', readonly=True)

                    # 搜索所有邮件
                    status, messages = imap_client.search(None, "ALL")
                    if status != "OK" or not messages or not messages[0]:
                        continue

                    message_ids = messages[0].split()

                    # 按日期排序所需的数据（邮件ID和日期）
                    # 为了避免获取所有邮件的日期，我们假设ID顺序与日期大致相关
                    message_ids.reverse()  # 通常ID越大越新

                    for msg_id in message_ids:
                        all_emails_data.append(
                            {"message_id_raw": msg_id, "folder": folder_name}
                        )

                except Exception as e:
                    logger.warning(f"Failed to access folder {folder_name}: {e}")
                    continue

            # 对所有文件夹的邮件进行统一分页
            total_emails = len(all_emails_data)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_email_meta = all_emails_data[start_index:end_index]

            email_items = []
            # 按文件夹分组批量获取
            paginated_email_meta.sort(key=lambda x: x["folder"])

            for folder_name, group in groupby(
                paginated_email_meta, key=lambda x: x["folder"]
            ):
                try:
                    imap_client.select(f'"{folder_name}"', readonly=True)

                    msg_ids_to_fetch = [item["message_id_raw"] for item in group]
                    if not msg_ids_to_fetch:
                        continue

                    # 批量获取邮件头 - 优化获取字段
                    msg_id_sequence = b",".join(msg_ids_to_fetch)
                    # 只获取必要的头部信息，减少数据传输
                    status, msg_data = imap_client.fetch(
                        msg_id_sequence,
                        "(FLAGS BODY.PEEK[HEADER.FIELDS (SUBJECT DATE FROM MESSAGE-ID)])",
                    )

                    if status != "OK":
                        continue

                    # 解析批量获取的数据
                    for i in range(0, len(msg_data), 2):
                        header_data = msg_data[i][1]

                        # 从返回的原始数据中解析出msg_id
                        # e.g., b'1 (BODY[HEADER.FIELDS (SUBJECT DATE FROM)] {..}'
                        match = re.match(rb"(\d+)\s+\(", msg_data[i][0])
                        if not match:
                            continue
                        fetched_msg_id = match.group(1)

                        msg = email.message_from_bytes(header_data)

                        subject = decode_header_value(
                            msg.get("Subject", "(No Subject)")
                        )
                        from_email = decode_header_value(
                            msg.get("From", "(Unknown Sender)")
                        )
                        date_str = msg.get("Date", "")

                        try:
                            date_obj = (
                                parsedate_to_datetime(date_str)
                                if date_str
                                else datetime.now()
                            )
                            # 转换为UTC时间并去除时区信息，确保统一格式
                            if date_obj.tzinfo is not None:
                                date_obj = date_obj.astimezone(datetime.now().astimezone().tzinfo).replace(tzinfo=None)
                            formatted_date = date_obj.isoformat()
                        except Exception:
                            date_obj = datetime.now().replace(tzinfo=None)
                            formatted_date = date_obj.isoformat()

                        message_id = f"{folder_name}-{fetched_msg_id.decode()}"

                        # 提取发件人首字母
                        sender_initial = "?"
                        if from_email:
                            # 尝试提取邮箱用户名的首字母
                            email_match = re.search(r"([a-zA-Z])", from_email)
                            if email_match:
                                sender_initial = email_match.group(1).upper()

                        # 检测验证码（只从主题检测，避免获取正文）
                        verification_code = None
                        try:
                            code_info = detect_verification_code(subject=subject, body="")
                            if code_info:
                                verification_code = code_info["code"]
                        except Exception as e:
                            logger.warning(f"Failed to detect verification code: {e}")

                        email_item = EmailItem(
                            message_id=message_id,
                            folder=folder_name,
                            subject=subject,
                            from_email=from_email,
                            date=formatted_date,
                            is_read=False,  # 简化处理，实际可通过IMAP flags判断
                            has_attachments=False,  # 简化处理，实际需要检查邮件结构
                            sender_initial=sender_initial,
                            verification_code=verification_code,
                        )
                        email_items.append(email_item)

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch bulk emails from {folder_name}: {e}"
                    )
                    continue

            # 按日期重新排序最终结果（使用datetime对象排序以确保准确性）
            def get_sort_key(email_item):
                try:
                    return datetime.fromisoformat(email_item.date)
                except:
                    return datetime.min
            
            email_items.sort(key=get_sort_key, reverse=True)

            # 归还连接到池中
            imap_pool.return_connection(credentials.email, imap_client)

            # 缓存到 SQLite
            try:
                emails_to_cache = [email.dict() for email in email_items]
                db.cache_emails(credentials.email, emails_to_cache)
                logger.info(f"Cached {len(emails_to_cache)} emails to SQLite for {credentials.email}")
            except Exception as e:
                logger.warning(f"Failed to cache emails to SQLite: {e}")

            result = EmailListResponse(
                email_id=credentials.email,
                folder_view=folder,
                page=page,
                page_size=page_size,
                total_emails=total_emails,
                emails=email_items,
            )

            # 保留内存缓存（用于向后兼容）
            cache_key = get_cache_key(credentials.email, folder, page, page_size)
            set_cached_emails(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            if imap_client:
                try:
                    # 如果出错，尝试归还连接或关闭
                    if hasattr(imap_client, "state") and imap_client.state != "LOGOUT":
                        imap_pool.return_connection(credentials.email, imap_client)
                    else:
                        # 连接已断开，从池中移除
                        pass
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail="Failed to retrieve emails")

    # 在线程池中运行同步代码
    return await asyncio.to_thread(_sync_list_emails)


async def get_email_details(
    credentials: AccountCredentials, message_id: str
) -> EmailDetailsResponse:
    """获取邮件详细内容 - 优化版本（支持SQLite缓存）"""
    
    # 先尝试从 SQLite 缓存获取
    try:
        cached_detail = db.get_cached_email_detail(credentials.email, message_id)
        if cached_detail:
            logger.info(f"Returning cached email detail from SQLite for {message_id}")
            return EmailDetailsResponse(**cached_detail)
    except Exception as e:
        logger.warning(f"Failed to load email detail from cache: {e}")
    
    # 解析复合message_id
    try:
        folder_name, msg_id = message_id.split("-", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    access_token = await get_access_token(credentials)

    def _sync_get_email_details():
        imap_client = None
        try:
            # 从连接池获取连接
            imap_client = imap_pool.get_connection(credentials.email, access_token)

            # 选择正确的文件夹
            imap_client.select(folder_name)

            # 获取完整邮件内容
            status, msg_data = imap_client.fetch(msg_id, "(RFC822)")

            if status != "OK" or not msg_data:
                raise HTTPException(status_code=404, detail="Email not found")

            # 解析邮件
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 提取基本信息
            subject = decode_header_value(msg.get("Subject", "(No Subject)"))
            from_email = decode_header_value(msg.get("From", "(Unknown Sender)"))
            to_email = decode_header_value(msg.get("To", "(Unknown Recipient)"))
            date_str = msg.get("Date", "")

            # 格式化日期
            try:
                if date_str:
                    date_obj = parsedate_to_datetime(date_str)
                    formatted_date = date_obj.isoformat()
                else:
                    formatted_date = datetime.now().isoformat()
            except Exception:
                formatted_date = datetime.now().isoformat()

            # 提取邮件内容
            body_plain, body_html = extract_email_content(msg)

            # 检测验证码
            verification_code = None
            try:
                # 使用主题和正文进行检测
                body_for_detection = body_plain or body_html or ""
                code_info = detect_verification_code(subject=subject, body=body_for_detection)
                if code_info:
                    verification_code = code_info["code"]
                    logger.info(f"Detected verification code in email {message_id}: {verification_code}")
            except Exception as e:
                logger.warning(f"Failed to detect verification code in email details: {e}")

            # 归还连接到池中
            imap_pool.return_connection(credentials.email, imap_client)

            email_detail_response = EmailDetailsResponse(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                date=formatted_date,
                body_plain=body_plain if body_plain else None,
                body_html=body_html if body_html else None,
                verification_code=verification_code,
            )
            
            # 缓存到 SQLite
            try:
                db.cache_email_detail(credentials.email, email_detail_response.dict())
                logger.info(f"Cached email detail to SQLite for {message_id}")
            except Exception as e:
                logger.warning(f"Failed to cache email detail to SQLite: {e}")
            
            return email_detail_response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            if imap_client:
                try:
                    # 如果出错，尝试归还连接
                    if hasattr(imap_client, "state") and imap_client.state != "LOGOUT":
                        imap_pool.return_connection(credentials.email, imap_client)
                except Exception:
                    pass
            raise HTTPException(
                status_code=500, detail="Failed to retrieve email details"
            )

    # 在线程池中运行同步代码
    return await asyncio.to_thread(_sync_get_email_details)

