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
import time
import database as db
from email.utils import parsedate_to_datetime
from fastapi import HTTPException

import database as db
import cache_service
from email_utils import decode_header_value, extract_email_content
from imap_pool import imap_pool
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse
from oauth_service import get_cached_access_token, clear_cached_access_token
from verification_code_detector import detect_verification_code

# 获取日志记录器
logger = logging.getLogger(__name__)


def _format_token_info(token: str, expires_at: Optional[str] = None) -> str:
    """
    格式化 token 信息用于日志（只显示前8位和后8位，中间用...代替）
    
    Args:
        token: access token
        expires_at: token 过期时间（可选）
        
    Returns:
        格式化的 token 信息字符串
    """
    if not token:
        return "None"
    
    if len(token) <= 16:
        masked_token = token[:4] + "..." + token[-4:]
    else:
        masked_token = token[:8] + "..." + token[-8:]
    
    info = f"Token: {masked_token}"
    if expires_at:
        try:
            from datetime import datetime
            expires_dt = datetime.fromisoformat(expires_at)
            now = datetime.now()
            time_until_expiry = (expires_dt - now).total_seconds()
            if time_until_expiry > 0:
                info += f", Expires in: {int(time_until_expiry/60)} minutes"
            else:
                info += f", Expired: {int(abs(time_until_expiry)/60)} minutes ago"
        except:
            info += f", Expires at: {expires_at}"
    
    return info


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
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> EmailListResponse:
    """获取邮件列表 - 优化版本（支持SQLite缓存、搜索、排序）"""
    


    start_time_ms = time.time()
    from_cache = False
    

    # 优先从内存LRU缓存获取
    if not force_refresh:
        cached_data = cache_service.get_cached_email_list(
            email=credentials.email,
            folder=folder,
            page=page,
            page_size=page_size,
            sender_search=sender_search,
            subject_search=subject_search,
            sort_by=sort_by,
            sort_order=sort_order,
            start_time=start_time,
            end_time=end_time,
            force_refresh=force_refresh
        )
        
        if cached_data:
            from_cache = True
            fetch_time_ms = int((time.time() - start_time_ms) * 1000)
            email_count = len(cached_data.get('emails', []))
            logger.info(f"[数据来源: 内存LRU缓存] 账户: {credentials.email}, 返回邮件数: {email_count}, 耗时: {fetch_time_ms}ms")
            # 兼容旧缓存数据，如果缺少 total_pages 则计算
            if 'total_pages' not in cached_data:
                total = cached_data.get('total_emails', 0)
                ps = cached_data.get('page_size', page_size)
                cached_data['total_pages'] = (total + ps - 1) // ps if total > 0 else 0
            return EmailListResponse(**cached_data)
    
    # 从 SQLite 缓存获取
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
                sort_order=sort_order,
                start_time=start_time,
                end_time=end_time
            )
            
            if cached_emails:
                from_cache = True
                fetch_time_ms = int((time.time() - start_time_ms) * 1000)
                logger.info(f"[数据来源: 数据库] 账户: {credentials.email}, 返回邮件数: {len(cached_emails)}, 总数: {total}, 耗时: {fetch_time_ms}ms")
                email_items = [
                    EmailItem(**email) for email in cached_emails
                ]
                total_pages = (total + page_size - 1) // page_size if total > 0 else 0
                response = EmailListResponse(
                    email_id=credentials.email,
                    folder_view=folder,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    total_emails=total,
                    emails=email_items,
                    from_cache=from_cache,
                    fetch_time_ms=fetch_time_ms
                )
                # 缓存到内存LRU缓存
                cache_service.set_cached_email_list(
                    email=credentials.email,
                    folder=folder,
                    page=page,
                    page_size=page_size,
                    data=response.dict(),
                    sender_search=sender_search,
                    subject_search=subject_search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_time=start_time,
                    end_time=end_time
                )
                return response
        except Exception as e:
            logger.warning(f"Failed to load from cache, fetching from IMAP: {e}")
    

    # 自动检测并选择最佳 API（参考 mail-all.js 的实现）
    # 优化策略：
    # 1. 如果 api_method 已明确设置为 graph_api，直接使用（避免重复检测）
    # 2. 如果 api_method 未设置或为 'imap'，尝试检测 Graph API 是否可用
    # 3. 检测成功后，可以更新数据库中的 api_method（可选，避免下次重复检测）
    use_graph_api = False
    
    if credentials.api_method in ["graph", "graph_api"]:
        use_graph_api = True
        logger.info(f"[API选择] 账户: {credentials.email}, 使用预设的 Graph API")
    elif credentials.api_method == "imap":
        # api_method 明确设置为 imap，直接使用（不检测）
        use_graph_api = False
        logger.info(f"[API选择] 账户: {credentials.email}, 使用预设的 IMAP")
    else:
        # api_method 未设置或为空，动态检测 Graph API 是否可用（参考 mail-all.js 的 graph_api 函数）
        try:
            from graph_api_service import check_graph_api_availability
            logger.info(f"[API选择] 账户: {credentials.email}, api_method 未设置，正在检测 Graph API 支持...")
            graph_result = await check_graph_api_availability(credentials)
            if graph_result.get("available", False):
                use_graph_api = True
                logger.info(f"[API选择] 账户: {credentials.email}, Graph API 可用，优先使用 Graph API")
                # 可选：更新数据库中的 api_method，避免下次重复检测
                try:
                    db.update_account(credentials.email, api_method="graph_api")
                    logger.info(f"[API选择] 账户: {credentials.email}, 已更新数据库 api_method 为 graph_api")
                except Exception as update_error:
                    logger.warning(f"[API选择] 账户: {credentials.email}, 更新 api_method 失败: {update_error}")
            else:
                logger.info(f"[API选择] 账户: {credentials.email}, Graph API 不可用，使用 IMAP")
                # 可选：更新数据库中的 api_method
                try:
                    db.update_account(credentials.email, api_method="imap")
                    logger.info(f"[API选择] 账户: {credentials.email}, 已更新数据库 api_method 为 imap")
                except Exception as update_error:
                    logger.warning(f"[API选择] 账户: {credentials.email}, 更新 api_method 失败: {update_error}")
        except Exception as e:
            logger.warning(f"[API选择] 账户: {credentials.email}, Graph API 检测失败: {e}，使用 IMAP")
            use_graph_api = False
    
    if use_graph_api:
        logger.info(f"[邮件列表请求] 账户: {credentials.email}, 访问方式: GRAPH API, 文件夹: {folder}, 页码: {page}, 每页: {page_size}")
        return await list_emails_via_graph_api(
            credentials, folder, page, page_size, force_refresh,
            sender_search, subject_search, sort_by, sort_order, start_time_ms,
            start_time, end_time
        )
    
    logger.info(f"[邮件列表请求] 账户: {credentials.email}, 访问方式: IMAP, 文件夹: {folder}, 页码: {page}, 每页: {page_size}")

    # 如果没有缓存或强制刷新，从 IMAP 获取
    logger.info(f"[数据来源: 微软IMAP服务器] 账户: {credentials.email}, 开始获取邮件列表...")
    access_token = await get_cached_access_token(credentials)
    
    # 获取 token 信息用于日志
    token_info = db.get_account_access_token(credentials.email)
    token_expires_at = token_info.get('token_expires_at') if token_info else None
    logger.info(f"[Token信息] 账户: {credentials.email}, {_format_token_info(access_token, token_expires_at)}")
    
    retry_count = 0
    max_retries = 1

    def _sync_list_emails():
        nonlocal access_token, retry_count
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

            # 获取所有邮件的头部信息（用于过滤）
            email_items = []
            # 按文件夹分组批量获取
            all_emails_data.sort(key=lambda x: x["folder"])

            for folder_name, group in groupby(
                all_emails_data, key=lambda x: x["folder"]
            ):
                try:
                    # 使用 examine 而不是 select，以只读方式打开，可能更稳定
                    imap_client.select(f'"{folder_name}"')

                    msg_ids_to_fetch = [item["message_id_raw"] for item in group]
                    if not msg_ids_to_fetch:
                        continue

                    # 批量获取邮件头 - 优化获取字段
                    msg_id_sequence = b",".join(msg_ids_to_fetch)
                    
                    # 参考 api/mail-all.js，使用 bodies: "" (即 BODY[]) 获取完整内容，然后使用 mailparser 解析
                    # 但为了性能，我们先尝试只获取头部
                    # 注意：api/mail-all.js 使用了 node-imap 的 fetch(results, { bodies: "" })
                    # 并在 message 事件中使用了 mailparser.simpleParser
                    
                    # 在 Python imaplib 中，我们尝试使用 RFC822.HEADER 或 BODY[HEADER]
                    # 如果遇到 SSL EOF 错误，可能是因为请求的数据量过大或连接不稳定
                    # 尝试分批获取，每批 50 封
                    
                    batch_size = 50
                    for i in range(0, len(msg_ids_to_fetch), batch_size):
                        batch_ids = msg_ids_to_fetch[i:i+batch_size]
                        batch_sequence = b",".join(batch_ids)
                        
                        try:
                            # 尝试使用 (BODY.PEEK[HEADER]) 获取头部，这通常比完整的 RFC822 更轻量且不容易出错
                            status, msg_data = imap_client.fetch(
                                batch_sequence,
                                "(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE FROM MESSAGE-ID)])",
                            )

                            if status != "OK":
                                logger.warning(f"Failed to fetch batch from {folder_name}: {status}")
                                continue

                            # 解析批量获取的数据
                            for j in range(0, len(msg_data), 2):
                                if not msg_data[j]: continue
                                
                                # 检查是否是元组 (response, data)
                                if isinstance(msg_data[j], tuple):
                                    header_data = msg_data[j][1]
                                    response_part = msg_data[j][0]
                                else:
                                    continue

                                # 从返回的原始数据中解析出msg_id
                                # e.g., b'1 (BODY[HEADER.FIELDS (SUBJECT DATE FROM)] {..}'
                                match = re.match(rb"(\d+)\s+\(", response_part)
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
                                    body_preview=None,
                                )
                                email_items.append(email_item)
                        except Exception as batch_error:
                            logger.warning(f"Error fetching batch in {folder_name}: {batch_error}")
                            continue

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch bulk emails from {folder_name}: {e}"
                    )
                    continue

            # 应用过滤条件
            filtered_email_items = []
            for email_item in email_items:
                # 检查发件人过滤
                if sender_search:
                    if sender_search.lower() not in email_item.from_email.lower():
                        continue
                
                # 检查主题过滤
                if subject_search:
                    if subject_search.lower() not in email_item.subject.lower():
                        continue
                
                # 检查时间范围过滤
                try:
                    email_date = datetime.fromisoformat(email_item.date)
                    if start_time:
                        start_dt = datetime.fromisoformat(start_time)
                        if email_date < start_dt:
                            continue
                    if end_time:
                        end_dt = datetime.fromisoformat(end_time)
                        if email_date > end_dt:
                            continue
                except Exception as e:
                    logger.warning(f"Failed to parse date for filtering: {e}")
                    # 如果日期解析失败，跳过时间过滤
                    pass
                
                filtered_email_items.append(email_item)
            
            # 按日期重新排序最终结果（使用datetime对象排序以确保准确性）
            def get_sort_key(email_item):
                try:
                    return datetime.fromisoformat(email_item.date)
                except:
                    return datetime.min
            
            filtered_email_items.sort(key=get_sort_key, reverse=(sort_order == "desc"))
            
            # 应用分页
            total_emails = len(filtered_email_items)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_email_items = filtered_email_items[start_index:end_index]
            
            email_items = paginated_email_items

            # 归还连接到池中
            imap_pool.return_connection(credentials.email, imap_client)

            # 缓存到 SQLite
            try:
                emails_to_cache = [email.dict() for email in email_items]
                db.cache_emails(credentials.email, emails_to_cache)
                logger.info(f"Cached {len(emails_to_cache)} emails to database for {credentials.email}")
            except Exception as e:
                logger.warning(f"Failed to cache emails to database: {e}")

            fetch_time_ms = int((time.time() - start_time_ms) * 1000)
            
            total_pages = (total_emails + page_size - 1) // page_size if total_emails > 0 else 0
            
            result = EmailListResponse(
                email_id=credentials.email,
                folder_view=folder,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                total_emails=total_emails,  # 使用过滤后的总数
                emails=email_items,  # 使用分页后的邮件列表
                from_cache=False,
                fetch_time_ms=fetch_time_ms
            )

            # 缓存到内存LRU缓存
            try:
                cache_service.set_cached_email_list(
                    email=credentials.email,
                    folder=folder,
                    page=page,
                    page_size=page_size,
                    data=result.dict(),
                    sender_search=sender_search,
                    subject_search=subject_search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_time=start_time,
                    end_time=end_time
                )
            except Exception as e:
                logger.warning(f"Failed to cache emails to LRU cache: {e}")
            
            logger.info(f"[数据来源: 微软IMAP服务器] 账户: {credentials.email}, 返回邮件数: {len(email_items)}, 总数: {total_emails}, 耗时: {fetch_time_ms}ms")

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
            
            # 检查是否是认证错误或 SSL 错误，如果是且未重试过，则清除缓存的 token 并重试
            error_msg = str(e).lower()
            is_auth_error = any(keyword in error_msg for keyword in ['auth', 'authentication', 'login', 'credential'])
            is_ssl_error = any(keyword in error_msg for keyword in ['ssl', 'unexpected_eof', 'eof', 'protocol'])
            
            if retry_count < max_retries and (is_auth_error or is_ssl_error):
                logger.warning(f"Connection error detected for {credentials.email} (auth: {is_auth_error}, ssl: {is_ssl_error}), clearing cached token and retrying...")
                retry_count += 1
                # 这里需要在异步上下文中清除 token，但我们在同步函数中，所以标记需要重试
                raise Exception("TOKEN_RETRY_NEEDED")
            
            # 其他错误，标记为需要从缓存返回
            raise Exception("FALLBACK_TO_CACHE")

    # 在线程池中运行同步代码，添加重试逻辑
    try:
        return await asyncio.to_thread(_sync_list_emails)
    except Exception as e:
        error_str = str(e)
        if "TOKEN_RETRY_NEEDED" in error_str:
            # 清除缓存的 token
            await clear_cached_access_token(credentials.email)
            # 获取新 token
            access_token = await get_cached_access_token(credentials)
            # 重置重试计数
            retry_count = 0
            # 重试
            logger.info(f"Retrying with fresh token for {credentials.email}")
            try:
                return await asyncio.to_thread(_sync_list_emails)
            except Exception as retry_error:
                logger.error(f"Retry failed for {credentials.email}: {retry_error}")
                # 重试失败，尝试从缓存返回
                pass
        elif "FALLBACK_TO_CACHE" in error_str:
            logger.warning(f"IMAP connection failed for {credentials.email}, attempting to return cached data")
        else:
            logger.error(f"Unexpected error for {credentials.email}: {e}")
        
        # 尝试从缓存返回数据作为降级方案
        try:
            # 先尝试从 SQLite 缓存获取
            cached_emails, total = db.get_cached_emails(
                email_account=credentials.email,
                page=page,
                page_size=page_size,
                folder=folder if folder != 'all' else None,
                sender_search=sender_search,
                subject_search=subject_search,
                sort_by=sort_by,
                sort_order=sort_order,
                start_time=start_time,
                end_time=end_time
            )
            
            if cached_emails:
                logger.info(f"[数据来源: 数据库(降级)] 账户: {credentials.email}, 返回邮件数: {len(cached_emails)}, 总数: {total}, IMAP连接失败，使用缓存数据")
                email_items = [EmailItem(**email) for email in cached_emails]
                total_pages = (total + page_size - 1) // page_size if total > 0 else 0
                return EmailListResponse(
                    email_id=credentials.email,
                    folder_view=folder,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    total_emails=total,
                    emails=email_items,
                    from_cache=True,
                    fetch_time_ms=0
                )
        except Exception as cache_error:
            logger.warning(f"Failed to get cached emails: {cache_error}")
        
        # 如果缓存也没有，返回友好的错误信息
        raise HTTPException(
            status_code=503,
            detail=f"无法连接到邮箱服务器，请稍后重试。如果问题持续，请检查账户凭证是否有效。"
        )


async def get_email_details(
    credentials: AccountCredentials, message_id: str
) -> EmailDetailsResponse:
    """获取邮件详细内容 - 优化版本（支持SQLite缓存）"""
    
    # 检查是否使用 Graph API
    if credentials.api_method in ["graph", "graph_api"]:
        logger.info(f"Using Graph API for email details: {credentials.email}")
        from graph_api_service import get_email_details_graph
        return await get_email_details_graph(credentials, message_id)
    
    # 优先从内存LRU缓存获取
    cached_detail = cache_service.get_cached_email_detail(credentials.email, message_id)
    if cached_detail:
        logger.info(f"Returning cached email detail from LRU cache for {message_id}")
        return EmailDetailsResponse(**cached_detail)
    
    # 从 SQLite 缓存获取
    try:
        cached_detail = db.get_cached_email_detail(credentials.email, message_id)
        if cached_detail:
            logger.info(f"Returning cached email detail from database for {message_id}")
            # 缓存到内存LRU缓存
            cache_service.set_cached_email_detail(credentials.email, message_id, cached_detail)
            return EmailDetailsResponse(**cached_detail)
    except Exception as e:
        logger.warning(f"Failed to load email detail from cache: {e}")
    
    # 解析复合message_id
    try:
        folder_name, msg_id = message_id.split("-", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    access_token = await get_cached_access_token(credentials)
    retry_count = 0
    max_retries = 1

    def _sync_get_email_details():
        nonlocal access_token, retry_count
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
                logger.info(f"Cached email detail to database for {message_id}")
            except Exception as e:
                logger.warning(f"Failed to cache email detail to database: {e}")
            
            # 缓存到内存LRU缓存
            try:
                cache_service.set_cached_email_detail(
                    credentials.email, 
                    message_id, 
                    email_detail_response.dict()
                )
            except Exception as e:
                logger.warning(f"Failed to cache email detail to LRU cache: {e}")
            
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
            
            # 检查是否是认证错误，如果是且未重试过，则清除缓存的 token 并重试
            error_msg = str(e).lower()
            if retry_count < max_retries and any(keyword in error_msg for keyword in ['auth', 'authentication', 'login', 'credential']):
                logger.warning(f"Authentication error detected for {credentials.email}, clearing cached token and retrying...")
                retry_count += 1
                raise Exception("AUTH_RETRY_NEEDED")
            
            raise HTTPException(
                status_code=500, detail="Failed to retrieve email details"
            )

    # 在线程池中运行同步代码，添加重试逻辑
    try:
        return await asyncio.to_thread(_sync_get_email_details)
    except Exception as e:
        if "AUTH_RETRY_NEEDED" in str(e):
            # 清除缓存的 token
            await clear_cached_access_token(credentials.email)
            # 获取新 token
            access_token = await get_cached_access_token(credentials)
            # 重试
            logger.info(f"Retrying email details fetch with fresh token for {credentials.email}")
            return await asyncio.to_thread(_sync_get_email_details)
        raise


async def list_emails_via_graph_api(
    credentials: AccountCredentials,
    folder: str,
    page: int,
    page_size: int,
    force_refresh: bool,
    sender_search: Optional[str],
    subject_search: Optional[str],
    sort_by: str,
    sort_order: str,
    start_time_ms: float,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> EmailListResponse:
    """使用 Graph API 获取邮件列表"""
    from graph_api_service import list_emails_graph
    import time
    
    # 优先从内存LRU缓存获取
    if not force_refresh:
        cached_data = cache_service.get_cached_email_list(
            email=credentials.email,
            folder=folder,
            page=page,
            page_size=page_size,
            sender_search=sender_search,
            subject_search=subject_search,
            sort_by=sort_by,
            sort_order=sort_order,
            start_time=start_time,
            end_time=end_time,
            force_refresh=force_refresh
        )
        
        if cached_data:
            fetch_time_ms = int((time.time() - start_time_ms) * 1000)
            email_count = len(cached_data.get('emails', []))
            logger.info(f"[数据来源: 内存LRU缓存] 账户: {credentials.email}, 访问方式: GRAPH API, 返回邮件数: {email_count}, 耗时: {fetch_time_ms}ms")
            # 兼容旧缓存数据，如果缺少 total_pages 则计算
            if 'total_pages' not in cached_data:
                total = cached_data.get('total_emails', 0)
                ps = cached_data.get('page_size', page_size)
                cached_data['total_pages'] = (total + ps - 1) // ps if total > 0 else 0
            return EmailListResponse(**cached_data)
    
    # 从 SQLite 缓存获取
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
                sort_order=sort_order,
                start_time=start_time,
                end_time=end_time
            )
            
            if cached_emails:
                fetch_time_ms = int((time.time() - start_time_ms) * 1000)
                logger.info(f"[数据来源: 数据库] 账户: {credentials.email}, 访问方式: GRAPH API, 返回邮件数: {len(cached_emails)}, 总数: {total}, 耗时: {fetch_time_ms}ms")
                email_items = [EmailItem(**email) for email in cached_emails]
                total_pages = (total + page_size - 1) // page_size if total > 0 else 0
                response = EmailListResponse(
                    email_id=credentials.email,
                    folder_view=folder,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    total_emails=total,
                    emails=email_items,
                    from_cache=True,
                    fetch_time_ms=fetch_time_ms
                )
                # 缓存到内存LRU缓存
                cache_service.set_cached_email_list(
                    email=credentials.email,
                    folder=folder,
                    page=page,
                    page_size=page_size,
                    data=response.dict(),
                    sender_search=sender_search,
                    subject_search=subject_search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_time=start_time,
                    end_time=end_time
                )
                return response
        except Exception as e:
            logger.warning(f"Failed to load from cache, fetching from Graph API: {e}")
    
    # 从 Graph API 获取
    logger.info(f"[数据来源: 微软Graph API服务器] 账户: {credentials.email}, 开始获取邮件列表...")
    
    # 获取 token 信息用于日志（不重新获取 token，只查询数据库中的信息）
    token_info = db.get_account_access_token(credentials.email)
    if token_info:
        access_token = token_info.get('access_token', '')
        token_expires_at = token_info.get('token_expires_at')
        logger.info(f"[Token信息] 账户: {credentials.email}, {_format_token_info(access_token, token_expires_at)}")
    else:
        logger.info(f"[Token信息] 账户: {credentials.email}, Token信息未找到，将在获取邮件时自动获取")
    
    email_items, total = await list_emails_graph(
        credentials, folder, page, page_size,
        sender_search, subject_search, sort_by, sort_order,
        start_time, end_time
    )
    
    # 缓存到数据库
    try:
        emails_to_cache = [email.dict() for email in email_items]
        db.cache_emails(credentials.email, emails_to_cache)
        logger.info(f"Cached {len(emails_to_cache)} emails to database for {credentials.email}")
    except Exception as e:
        logger.warning(f"Failed to cache emails to database: {e}")
    
    # 缓存到内存LRU缓存
    try:
        cache_service.set_cached_email_list(
            email=credentials.email,
            folder=folder,
            page=page,
            page_size=page_size,
            data=EmailListResponse(
                email_id=credentials.email,
                folder_view=folder,
                page=page,
                page_size=page_size,
                total_emails=total,
                total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
                emails=email_items,
                fetch_time_ms=int((time.time() - start_time_ms) * 1000)
            ).dict()
        )
        logger.debug(f"Cached {len(email_items)} emails to memory LRU cache for {credentials.email}")
    except Exception as e:
        logger.warning(f"Failed to cache emails to memory: {e}")
    
    fetch_time_ms = int((time.time() - start_time_ms) * 1000)
    
    logger.info(f"[数据来源: 微软Graph API服务器] 账户: {credentials.email}, 返回邮件数: {len(email_items)}, 总数: {total}, 耗时: {fetch_time_ms}ms")
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return EmailListResponse(
        email_id=credentials.email,
        folder_view=folder,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_emails=total,
        emails=email_items,
        from_cache=False,
        fetch_time_ms=fetch_time_ms
    )


async def delete_email(
    credentials: AccountCredentials,
    message_id: str
) -> bool:
    """
    删除邮件（支持 Graph API 和 IMAP）
    
    Args:
        credentials: 账户凭证
        message_id: 邮件ID
        
    Returns:
        bool: 是否删除成功
    """
    if credentials.api_method in ["graph", "graph_api"]:
        logger.info(f"Deleting email via Graph API: {message_id}")
        from graph_api_service import delete_email_graph
        return await delete_email_graph(credentials, message_id)
    else:
        logger.info(f"Deleting email via IMAP: {message_id}")
        return await delete_email_via_imap(credentials, message_id)


async def delete_email_via_imap(
    credentials: AccountCredentials,
    message_id: str
) -> bool:
    """使用 IMAP 删除邮件"""
    # 解析复合message_id
    try:
        folder_name, msg_id = message_id.split("-", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")
    
    access_token = await get_cached_access_token(credentials)
    
    def _sync_delete_email():
        imap_client = None
        try:
            # 从连接池获取连接
            imap_client = imap_pool.get_connection(credentials.email, access_token)
            
            # 选择文件夹（可写模式）
            imap_client.select(folder_name, readonly=False)
            
            # 标记为删除
            imap_client.store(msg_id, '+FLAGS', '\\Deleted')
            
            # 永久删除
            imap_client.expunge()
            
            # 归还连接
            imap_pool.return_connection(credentials.email, imap_client)
            
            logger.info(f"Successfully deleted email {message_id} via IMAP for {credentials.email}")
            
            # 删除缓存
            try:
                db.delete_email_from_cache(credentials.email, message_id)
                
                # 清除内存缓存，因为页面内容变了
                cache_service.clear_email_cache(credentials.email)
            except Exception as e:
                logger.warning(f"Failed to delete email from cache: {e}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting email via IMAP: {e}")
            if imap_client:
                try:
                    imap_pool.return_connection(credentials.email, imap_client)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail="Failed to delete email via IMAP")
    
    return await asyncio.to_thread(_sync_delete_email)


async def send_email(
    credentials: AccountCredentials,
    to: str,
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None
) -> str:
    """
    发送邮件（仅支持 Graph API）
    
    Args:
        credentials: 账户凭证
        to: 收件人邮箱
        subject: 邮件主题
        body_text: 纯文本正文
        body_html: HTML正文
        
    Returns:
        str: 邮件ID
    """
    if credentials.api_method in ["graph", "graph_api"]:
        logger.info(f"Sending email via Graph API from {credentials.email} to {to}")
        from graph_api_service import send_email_graph
        return await send_email_graph(credentials, to, subject, body_text, body_html)
    else:
        # IMAP 不支持发送邮件
        raise HTTPException(
            status_code=400,
            detail="Sending email is only supported via Graph API. Please enable Graph API for this account."
        )

