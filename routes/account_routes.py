"""
账户管理路由模块

处理邮箱账户管理相关的API端点
"""

import logging
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks

import auth
import database as db
from account_service import get_account_credentials, save_account_credentials
from models import (
    AccountCredentials,
    AccountInfo,
    AccountListResponse,
    AccountResponse,
    AddTagRequest,
    BatchRefreshRequest,
    BatchRefreshResult,
    BatchDeleteRequest,
    BatchDeleteResult,
    UpdateTagsRequest,
    BatchImportRequest,
    BatchImportTaskResponse,
    BatchImportTaskProgress,
)
from oauth_service import get_access_token, refresh_account_token

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/accounts", tags=["账户管理"])


@router.get("/random", response_model=AccountListResponse)
async def get_random_accounts(
    include_tags: Optional[str] = Query(None, description="必须包含的标签，多个用逗号分隔"),
    exclude_tags: Optional[str] = Query(None, description="必须不包含的标签，多个用逗号分隔"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，范围1-100"),
    admin: dict = Depends(auth.get_current_admin),
):
    """随机获取邮箱账户列表（支持标签筛选和分页）"""
    try:
        # 解析标签列表
        include_tag_list = [tag.strip() for tag in include_tags.split(",")] if include_tags else None
        exclude_tag_list = [tag.strip() for tag in exclude_tags.split(",")] if exclude_tags else None
        
        # 从数据库获取随机账户
        accounts_data, total_accounts = db.get_random_accounts(
            include_tags=include_tag_list,
            exclude_tags=exclude_tag_list,
            page=page,
            page_size=page_size
        )
        
        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get("client_id"):
                    status = "invalid"
            except Exception:
                status = "error"
            
            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
            )
            all_accounts.append(account)
        
        # 计算分页信息
        total_pages = (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        
        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )
    except Exception as e:
        logger.error(f"Error getting random accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=AccountListResponse)
async def get_accounts(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，范围1-100"),
    email_search: Optional[str] = Query(None, description="邮箱账号模糊搜索"),
    tag_search: Optional[str] = Query(None, description="标签模糊搜索（已废弃，使用include_tags代替）"),
    include_tags: Optional[str] = Query(None, description="必须包含的标签，多个用逗号分隔"),
    exclude_tags: Optional[str] = Query(None, description="必须不包含的标签，多个用逗号分隔"),
    refresh_status: Optional[str] = Query(None, description="刷新状态筛选 (all, never_refreshed, success, failed, pending, custom)"),
    time_filter: Optional[str] = Query(None, description="时间过滤器 (today, week, month, custom)"),
    after_date: Optional[str] = Query(None, description="自定义日期（ISO格式）"),
    refresh_start_date: Optional[str] = Query(None, description="刷新起始日期（ISO格式，用于自定义日期范围）"),
    refresh_end_date: Optional[str] = Query(None, description="刷新截止日期（ISO格式，用于自定义日期范围）"),
    user: dict = Depends(auth.get_current_user),
):
    """获取已加载的邮箱账户列表，支持分页和多维度搜索（根据用户权限过滤）"""
    try:
        # 解析标签列表
        include_tag_list = [tag.strip() for tag in include_tags.split(",")] if include_tags else None
        exclude_tag_list = [tag.strip() for tag in exclude_tags.split(",")] if exclude_tags else None
        
        logger.info(f"[API] GET /accounts 收到请求 (user: {user.get('username')}, role: {user.get('role')})")
        logger.info(f"  page={page}, page_size={page_size}")
        logger.info(f"  email_search={email_search}, tag_search={tag_search}")
        logger.info(f"  include_tags={include_tag_list}, exclude_tags={exclude_tag_list}")
        logger.info(f"  refresh_status={refresh_status}, time_filter={time_filter}")
        logger.info(f"  after_date={after_date}")
        logger.info(f"  refresh_start_date={refresh_start_date}")
        logger.info(f"  refresh_end_date={refresh_end_date}")
        
        # 使用新的筛选函数（使用API请求专用线程池，避免被后台任务阻塞）
        import asyncio
        from main import api_requests_executor
        loop = asyncio.get_event_loop()
        accounts_data, total_accounts = await loop.run_in_executor(
            api_requests_executor,
            db.get_accounts_by_filters,
            page,
            page_size,
            email_search,
            tag_search,
            include_tag_list,
            exclude_tag_list,
            refresh_status,
            time_filter,
            after_date,
            refresh_start_date,
            refresh_end_date,
        )
        
        # 根据用户权限过滤账户
        accessible_accounts = auth.get_accessible_accounts(user)
        if accessible_accounts is not None:  # 普通用户，只能看到绑定的账户
            accounts_data = [
                acc for acc in accounts_data 
                if acc['email'] in accessible_accounts
            ]
            total_accounts = len(accounts_data)
            logger.info(f"[API] 普通用户过滤后: 返回={len(accounts_data)}条")
        else:  # 管理员，可以看到所有账户
            logger.info(f"[API] 管理员查询: 总数={total_accounts}, 返回={len(accounts_data)}条")
        
        # 转换为AccountInfo对象
        all_accounts = []
        for account_data in accounts_data:
            # 验证账户状态
            status = "active"
            try:
                if not account_data.get("refresh_token") or not account_data.get("client_id"):
                    status = "invalid"
            except Exception:
                status = "error"
            
            account = AccountInfo(
                email_id=account_data["email"],
                client_id=account_data.get("client_id", ""),
                status=status,
                tags=account_data.get("tags", []),
                last_refresh_time=account_data.get("last_refresh_time"),
                next_refresh_time=account_data.get("next_refresh_time"),
                refresh_status=account_data.get("refresh_status", "pending"),
            )
            all_accounts.append(account)
        
        # 计算分页信息
        total_pages = (total_accounts + page_size - 1) // page_size if total_accounts > 0 else 0
        
        return AccountListResponse(
            total_accounts=total_accounts,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            accounts=all_accounts,
        )
        
    except Exception as e:
        logger.error(f"Error getting accounts list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=AccountResponse)
async def register_account(
    credentials: AccountCredentials, admin: dict = Depends(auth.get_current_admin)
):
    """注册或更新邮箱账户"""
    try:
        # 验证凭证有效性并获取access token
        await get_access_token(credentials)

        # 更新凭证的刷新时间和状态
        current_time = datetime.now().isoformat()
        next_refresh = datetime.now() + timedelta(days=3)
        
        credentials.last_refresh_time = current_time
        credentials.next_refresh_time = next_refresh.isoformat()
        credentials.refresh_status = "success"
        credentials.refresh_error = None

        # 保存凭证（包含access token和刷新时间）
        await save_account_credentials(credentials.email, credentials)

        return AccountResponse(
            email_id=credentials.email,
            message="Account verified and saved successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering account: {e}")
        raise HTTPException(status_code=500, detail="Account registration failed")


@router.put("/{email_id}/tags", response_model=AccountResponse)
async def update_account_tags(
    email_id: str,
    request: UpdateTagsRequest,
    admin: dict = Depends(auth.get_current_admin),
):
    """更新账户标签"""
    try:
        # 检查账户是否存在
        credentials = await get_account_credentials(email_id)

        # 更新标签
        credentials.tags = request.tags

        # 保存更新后的凭证
        await save_account_credentials(email_id, credentials)

        return AccountResponse(
            email_id=email_id, message="Account tags updated successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to update account tags")


@router.post("/{email_id}/tags/add", response_model=AccountResponse)
async def add_account_tag(
    email_id: str,
    request: AddTagRequest,
    admin: dict = Depends(auth.get_current_admin),
):
    """为账户添加标签（如果标签已存在则不处理）"""
    try:
        # 使用数据库函数添加标签
        success = db.add_tag_to_account(email_id, request.tag)
        
        if not success:
            # 账户不存在
            raise HTTPException(status_code=404, detail=f"Account {email_id} not found")
        
        # 检查标签是否已存在
        account = db.get_account_by_email(email_id)
        if request.tag in account.get('tags', []):
            return AccountResponse(
                email_id=email_id, 
                message=f"Tag '{request.tag}' already exists for account."
            )
        else:
            return AccountResponse(
                email_id=email_id, 
                message=f"Tag '{request.tag}' added successfully."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tag to account: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tag to account")


@router.delete("/{email_id}", response_model=AccountResponse)
async def delete_account(email_id: str, admin: dict = Depends(auth.get_current_admin)):
    """删除邮箱账户"""
    try:
        # 检查账户是否存在
        await get_account_credentials(email_id)

        # 从数据库删除账户
        success = db.delete_account(email_id)

        if success:
            return AccountResponse(
                email_id=email_id, message="Account deleted successfully."
            )
        else:
            raise HTTPException(status_code=404, detail="Account not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.post("/batch-delete", response_model=BatchDeleteResult)
async def batch_delete_accounts(
    request: BatchDeleteRequest,
    admin: dict = Depends(auth.get_current_admin),
):
    """批量删除邮箱账户"""
    try:
        logger.info(f"Admin {admin['username']} initiated batch delete for {len(request.email_ids)} accounts")
        
        if not request.email_ids:
            return BatchDeleteResult(
                total_processed=0,
                success_count=0,
                failed_count=0,
                details=[]
            )
        
        success_count = 0
        failed_count = 0
        details = []
        
        for email_id in request.email_ids:
            try:
                # 从数据库删除账户
                success = db.delete_account(email_id)
                
                if success:
                    success_count += 1
                    details.append({
                        "email": email_id,
                        "status": "success",
                        "message": "Account deleted successfully"
                    })
                    logger.info(f"Successfully deleted account {email_id} in batch")
                else:
                    failed_count += 1
                    details.append({
                        "email": email_id,
                        "status": "failed",
                        "message": "Account not found"
                    })
                    logger.warning(f"Account {email_id} not found during batch delete")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error deleting account {email_id} in batch: {e}")
                failed_count += 1
                details.append({
                    "email": email_id,
                    "status": "failed",
                    "message": error_msg
                })
        
        logger.info(f"Batch delete completed by {admin['username']}: "
                   f"{success_count} succeeded, {failed_count} failed out of {len(request.email_ids)}")
        
        return BatchDeleteResult(
            total_processed=len(request.email_ids),
            success_count=success_count,
            failed_count=failed_count,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Error in batch delete: {e}")
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.post("/{email_id}/refresh-token", response_model=AccountResponse)
async def manual_refresh_token(
    email_id: str, admin: dict = Depends(auth.get_current_admin)
):
    """手动刷新指定账户的token"""
    try:
        # 获取账户凭证
        credentials = await get_account_credentials(email_id)

        # 调用刷新函数
        result = await refresh_account_token(credentials)

        if result["success"]:
            # 更新凭证对象
            current_time = datetime.now().isoformat()
            next_refresh = datetime.now() + timedelta(days=3)

            credentials.refresh_token = result["new_refresh_token"]
            credentials.last_refresh_time = current_time
            credentials.next_refresh_time = next_refresh.isoformat()
            credentials.refresh_status = "success"
            credentials.refresh_error = None

            # 保存更新后的凭证
            await save_account_credentials(email_id, credentials)

            logger.info(f"Token refreshed for {email_id} by {admin['username']}")

            return AccountResponse(
                email_id=email_id,
                message=f"Token refreshed successfully at {current_time}",
            )
        else:
            # 更新失败状态
            credentials.refresh_status = "failed"
            credentials.refresh_error = result.get("error", "Unknown error")
            await save_account_credentials(email_id, credentials)

            raise HTTPException(
                status_code=500,
                detail=f"Token refresh failed: {result.get('error', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error manually refreshing token for {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@router.post("/batch-refresh-tokens", response_model=BatchRefreshResult)
async def batch_refresh_tokens(
    request: Optional[BatchRefreshRequest] = Body(None, description="批量刷新请求，包含email_ids列表"),
    email_search: Optional[str] = Query(None, description="邮箱账号模糊搜索"),
    tag_search: Optional[str] = Query(None, description="标签模糊搜索"),
    refresh_status: Optional[str] = Query(None, description="刷新状态筛选 (all, never_refreshed, success, failed, pending, custom)"),
    time_filter: Optional[str] = Query(None, description="时间过滤器 (today, week, month, custom)"),
    after_date: Optional[str] = Query(None, description="自定义日期（ISO格式）"),
    refresh_start_date: Optional[str] = Query(None, description="刷新起始日期（ISO格式，用于自定义日期范围）"),
    refresh_end_date: Optional[str] = Query(None, description="刷新截止日期（ISO格式，用于自定义日期范围）"),
    admin: dict = Depends(auth.get_current_admin),
):
    """批量刷新符合条件的账户Token（支持指定email_ids或筛选条件）"""
    try:
        # 如果提供了email_ids，直接使用这些账户
        if request and request.email_ids and len(request.email_ids) > 0:
            logger.info(f"Admin {admin['username']} initiated batch token refresh for {len(request.email_ids)} selected accounts")
            accounts_data = []
            for email_id in request.email_ids:
                account_data = db.get_account_by_email(email_id)
                if account_data:
                    accounts_data.append(account_data)
            total_accounts = len(accounts_data)
        else:
            # 否则使用筛选条件
            logger.info(f"Admin {admin['username']} initiated batch token refresh with filters: "
                       f"email_search={email_search}, tag_search={tag_search}, "
                       f"refresh_status={refresh_status}, time_filter={time_filter}, "
                       f"refresh_start_date={refresh_start_date}, refresh_end_date={refresh_end_date}")
            
            # 获取符合筛选条件的所有账户
            accounts_data, total_accounts = db.get_accounts_by_filters(
                page=1,
                page_size=10000,  # 获取所有符合条件的账户
                email_search=email_search,
                tag_search=tag_search,
                refresh_status=refresh_status,
                time_filter=time_filter,
                after_date=after_date,
                refresh_start_date=refresh_start_date,
                refresh_end_date=refresh_end_date,
            )
        
        if not accounts_data:
            logger.info("No accounts match the criteria")
            return BatchRefreshResult(
                total_processed=0,
                success_count=0,
                failed_count=0,
                details=[]
            )
        
        # 使用信号量限制并发数为5
        semaphore = asyncio.Semaphore(5)
        
        async def refresh_single_token(account_data: dict) -> dict:
            """刷新单个账户的token（使用信号量限制并发）"""
            async with semaphore:
                email_id = account_data["email"]
                try:
                    # 构建凭证对象
                    credentials = AccountCredentials(
                        email=email_id,
                        refresh_token=account_data["refresh_token"],
                        client_id=account_data["client_id"],
                        tags=account_data.get("tags", []),
                        last_refresh_time=account_data.get("last_refresh_time"),
                        next_refresh_time=account_data.get("next_refresh_time"),
                        refresh_status=account_data.get("refresh_status", "pending"),
                        refresh_error=account_data.get("refresh_error"),
                        api_method=account_data.get("api_method", "imap"),
                    )
                    
                    # 刷新token
                    result = await refresh_account_token(credentials)
                    
                    # 更新账户信息
                    current_time = datetime.now().isoformat()
                    next_refresh = datetime.now() + timedelta(days=3)
                    
                    if result["success"]:
                        db.update_account(
                            email_id,
                            refresh_token=result["new_refresh_token"],
                            last_refresh_time=current_time,
                            next_refresh_time=next_refresh.isoformat(),
                            refresh_status="success",
                            refresh_error=None,
                        )
                        logger.info(f"Successfully refreshed token for {email_id} in batch")
                        return {
                            "email": email_id,
                            "status": "success",
                            "message": "Token refreshed successfully"
                        }
                    else:
                        error_msg = result.get("error", "Unknown error")
                        db.update_account(
                            email_id,
                            refresh_status="failed",
                            refresh_error=error_msg,
                        )
                        logger.error(f"Failed to refresh token for {email_id} in batch: {error_msg}")
                        return {
                            "email": email_id,
                            "status": "failed",
                            "message": error_msg
                        }
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error refreshing token for {email_id} in batch: {e}")
                    db.update_account(
                        email_id,
                        refresh_status="failed",
                        refresh_error=error_msg,
                    )
                    return {
                        "email": email_id,
                        "status": "failed",
                        "message": error_msg
                    }
        
        # 并发执行所有token刷新任务
        logger.info(f"Starting concurrent token refresh for {total_accounts} accounts (max 5 concurrent)")
        tasks = [refresh_single_token(account_data) for account_data in accounts_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = 0
        failed_count = 0
        details = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                logger.error(f"Exception in token refresh: {result}")
                details.append({
                    "email": "unknown",
                    "status": "failed",
                    "message": str(result)
                })
            else:
                details.append(result)
                if result["status"] == "success":
                    success_count += 1
                else:
                    failed_count += 1
        
        logger.info(f"Batch token refresh completed by {admin['username']}: "
                   f"{success_count} succeeded, {failed_count} failed out of {total_accounts}")
        
        return BatchRefreshResult(
            total_processed=total_accounts,
            success_count=success_count,
            failed_count=failed_count,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Error in batch token refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Batch refresh failed: {str(e)}")


@router.post("/{email_id}/detect-api-method", response_model=AccountResponse)
async def detect_api_method_route(
    email_id: str, admin: dict = Depends(auth.get_current_admin)
):
    """检测并更新账户的API方法（Graph API 或 IMAP）"""
    from oauth_service import detect_and_update_api_method
    
    try:
        # 获取账户凭证
        credentials = await get_account_credentials(email_id)
        
        # 检测API方法
        api_method = await detect_and_update_api_method(credentials)
        
        logger.info(f"Detected API method for {email_id}: {api_method} by {admin['username']}")
        
        return AccountResponse(
            email_id=email_id,
            message=f"API method detected and updated to: {api_method}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting API method for {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect API method")


# 线程池执行器（用于批量导入任务，限制并发数为5）
executor = ThreadPoolExecutor(max_workers=5)


def _process_single_import_item_sync(
    task_id: str,
    item: dict,
    task_tags: list,
    api_method: str
) -> tuple:
    """
    处理单个导入项（同步包装函数，在线程池中运行）
    
    Args:
        task_id: 任务ID
        item: 任务项数据
        task_tags: 任务标签
        api_method: API方法
        
    Returns:
        (email, success, error_msg) 元组
    """
    try:
        # 在新的事件循环中运行异步操作
        import asyncio
        
        # 创建新的事件循环（因为在线程中运行）
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 构建凭证对象
        credentials = AccountCredentials(
            email=item['email'],
            refresh_token=item['refresh_token'],
            client_id=item['client_id'],
            tags=task_tags,
            api_method=api_method
        )
        
        # 运行异步操作
        async def _async_import():
            # 验证凭证有效性并获取access token
            await get_access_token(credentials)
            
            # 更新凭证的刷新时间和状态
            current_time = datetime.now().isoformat()
            next_refresh = datetime.now() + timedelta(days=3)
            
            credentials.last_refresh_time = current_time
            credentials.next_refresh_time = next_refresh.isoformat()
            credentials.refresh_status = "success"
            credentials.refresh_error = None
            
            # 保存凭证（包含access token和刷新时间）
            await save_account_credentials(credentials.email, credentials)
            
            # 更新任务项状态
            from dao.batch_import_task_dao import BatchImportTaskItemDAO
            item_dao = BatchImportTaskItemDAO()
            item_dao.update_item(task_id, item['email'], "success")
        
        # 执行异步操作
        loop.run_until_complete(_async_import())
        
        return (item['email'], True, None)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to import {item['email']}: {error_msg}")
        try:
            from dao.batch_import_task_dao import BatchImportTaskItemDAO
            item_dao = BatchImportTaskItemDAO()
            item_dao.update_item(task_id, item['email'], "failed", error_msg)
        except:
            pass
        return (item['email'], False, error_msg)


async def process_batch_import_task(task_id: str):
    """
    后台处理批量导入任务（使用信号量限制并发数为5）
    
    Args:
        task_id: 任务ID
    """
    try:
        from dao.batch_import_task_dao import BatchImportTaskDAO, BatchImportTaskItemDAO
        
        task_dao = BatchImportTaskDAO()
        item_dao = BatchImportTaskItemDAO()
        
        logger.info(f"Starting batch import task: {task_id}")
        
        # 更新任务状态为处理中
        task_dao.update_progress(task_id, status="processing")
        
        # 获取任务信息
        task = task_dao.get_by_task_id(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # 获取任务项
        items = item_dao.get_by_task_id(task_id, status="pending")
        total = len(items)
        
        logger.info(f"Processing {total} items for task {task_id} using thread pool (5 workers)")
        
        # 准备任务参数
        # task['tags'] 在 DAO 中已经被解析为列表，不需要再次解析
        task_tags = task.get('tags', [])
        if isinstance(task_tags, str):
            # 如果仍然是字符串，则解析（兼容旧数据）
            task_tags = json.loads(task_tags) if task_tags else []
        api_method = task.get('api_method', 'imap')
        
        # 使用线程池并发处理
        loop = asyncio.get_event_loop()
        futures = []
        
        for item in items:
            # 将任务提交到线程池
            future = loop.run_in_executor(
                executor,
                _process_single_import_item_sync,
                task_id,
                item,
                task_tags,
                api_method
            )
            futures.append(future)
        
        # 等待所有任务完成，并定期更新进度
        success_count = 0
        failed_count = 0
        completed_count = 0
        
        # 分批处理，每完成一批就更新进度
        batch_size = 10  # 每处理10个就更新一次进度
        
        for i in range(0, len(futures), batch_size):
            batch_futures = futures[i:i + batch_size]
            results = await asyncio.gather(*batch_futures, return_exceptions=True)
            
            # 统计这一批的结果
            for result in results:
                completed_count += 1
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"Exception in import task: {result}")
                else:
                    email, success, error_msg = result
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
            
            # 更新任务进度
            task_dao.update_progress(
                task_id,
                success_count=success_count,
                failed_count=failed_count,
                processed_count=completed_count
            )
            
            logger.debug(f"Progress: {completed_count}/{total} items processed")
        
        # 更新任务状态为完成
        task_dao.update_progress(
            task_id,
            status="completed",
            success_count=success_count,
            failed_count=failed_count,
            processed_count=total
        )
        
        logger.info(f"Batch import task {task_id} completed: {success_count} success, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error processing batch import task {task_id}: {e}")
        from dao.batch_import_task_dao import BatchImportTaskDAO
        task_dao = BatchImportTaskDAO()
        task_dao.update_progress(task_id, status="failed")


@router.post("/batch-import", response_model=BatchImportTaskResponse)
async def create_batch_import_task(
    request: BatchImportRequest,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(auth.get_current_admin),
):
    """创建批量导入任务"""
    try:
        if not request.items:
            raise HTTPException(status_code=400, detail="Items list cannot be empty")
        
        from dao.batch_import_task_dao import BatchImportTaskDAO, BatchImportTaskItemDAO
        
        task_dao = BatchImportTaskDAO()
        item_dao = BatchImportTaskItemDAO()
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务
        success = task_dao.create(
            task_id=task_id,
            total_count=len(request.items),
            api_method=request.api_method,
            tags=request.tags,
            created_by=admin.get('username')
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create batch import task")
        
        # 添加任务项
        task_items = [
            {
                'email': item.email,
                'refresh_token': item.refresh_token,
                'client_id': item.client_id
            }
            for item in request.items
        ]
        
        success = item_dao.add_items(task_id, task_items)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add batch import task items")
        
        # 启动后台任务
        background_tasks.add_task(process_batch_import_task, task_id)
        
        logger.info(f"Created batch import task {task_id} with {len(request.items)} items by {admin['username']}")
        
        return BatchImportTaskResponse(
            task_id=task_id,
            total_count=len(request.items),
            status="pending",
            message="Batch import task created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch import task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create batch import task: {str(e)}")


@router.get("/batch-import/{task_id}", response_model=BatchImportTaskProgress)
async def get_batch_import_task_progress(
    task_id: str,
    admin: dict = Depends(auth.get_current_admin),
):
    """获取批量导入任务进度"""
    try:
        from dao.batch_import_task_dao import BatchImportTaskDAO
        
        task_dao = BatchImportTaskDAO()
        task = task_dao.get_by_task_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        total = task['total_count']
        processed = task['processed_count']
        success = task['success_count']
        failed = task['failed_count']
        status = task['status']
        
        progress_percent = (processed / total * 100) if total > 0 else 0
        
        return BatchImportTaskProgress(
            task_id=task_id,
            total_count=total,
            success_count=success,
            failed_count=failed,
            processed_count=processed,
            status=status,
            progress_percent=round(progress_percent, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch import task progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task progress")

