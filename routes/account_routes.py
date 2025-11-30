"""
账户管理路由模块

处理邮箱账户管理相关的API端点
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

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
    tag_search: Optional[str] = Query(None, description="标签模糊搜索"),
    refresh_status: Optional[str] = Query(None, description="刷新状态筛选 (all, never_refreshed, success, failed, pending, custom)"),
    time_filter: Optional[str] = Query(None, description="时间过滤器 (today, week, month, custom)"),
    after_date: Optional[str] = Query(None, description="自定义日期（ISO格式）"),
    refresh_start_date: Optional[str] = Query(None, description="刷新起始日期（ISO格式，用于自定义日期范围）"),
    refresh_end_date: Optional[str] = Query(None, description="刷新截止日期（ISO格式，用于自定义日期范围）"),
    user: dict = Depends(auth.get_current_user),
):
    """获取已加载的邮箱账户列表，支持分页和多维度搜索（根据用户权限过滤）"""
    try:
        logger.info(f"[API] GET /accounts 收到请求 (user: {user.get('username')}, role: {user.get('role')})")
        logger.info(f"  page={page}, page_size={page_size}")
        logger.info(f"  email_search={email_search}, tag_search={tag_search}")
        logger.info(f"  refresh_status={refresh_status}, time_filter={time_filter}")
        logger.info(f"  after_date={after_date}")
        logger.info(f"  refresh_start_date={refresh_start_date}")
        logger.info(f"  refresh_end_date={refresh_end_date}")
        
        # 使用新的筛选函数
        accounts_data, total_accounts = db.get_accounts_by_filters(
            page=page,
            page_size=page_size,
            email_search=email_search,
            tag_search=tag_search,
            refresh_status=refresh_status,
            time_filter=time_filter,
            after_date=after_date,
            refresh_start_date=refresh_start_date,
            refresh_end_date=refresh_end_date,
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
        # 验证凭证有效性
        await get_access_token(credentials)

        # 保存凭证
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
        
        # 逐个刷新token
        success_count = 0
        failed_count = 0
        details = []
        
        for account_data in accounts_data:
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
                    success_count += 1
                    details.append({
                        "email": email_id,
                        "status": "success",
                        "message": "Token refreshed successfully"
                    })
                    logger.info(f"Successfully refreshed token for {email_id} in batch")
                else:
                    error_msg = result.get("error", "Unknown error")
                    db.update_account(
                        email_id,
                        refresh_status="failed",
                        refresh_error=error_msg,
                    )
                    failed_count += 1
                    details.append({
                        "email": email_id,
                        "status": "failed",
                        "message": error_msg
                    })
                    logger.error(f"Failed to refresh token for {email_id} in batch: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error refreshing token for {email_id} in batch: {e}")
                db.update_account(
                    email_id,
                    refresh_status="failed",
                    refresh_error=error_msg,
                )
                failed_count += 1
                details.append({
                    "email": email_id,
                    "status": "failed",
                    "message": error_msg
                })
        
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

