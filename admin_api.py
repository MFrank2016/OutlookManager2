"""
管理面板API模块

提供数据表管理和系统配置管理的API接口
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

import auth
import database as db
from models import (
    UserCreateRequest,
    UserUpdateRequest,
    UserInfo,
    UserListResponse,
    PermissionsUpdateRequest,
    BindAccountsRequest,
    RoleUpdateRequest,
    UserResponse,
    PasswordUpdateRequest
)

# 创建路由器
router = APIRouter(prefix="/admin", tags=["管理面板"])


# ============================================================================
# Pydantic模型
# ============================================================================

class TableInfo(BaseModel):
    """表信息模型"""
    name: str
    record_count: int


class TableListResponse(BaseModel):
    """表列表响应模型"""
    tables: List[TableInfo]


class ColumnInfo(BaseModel):
    """列信息模型"""
    cid: int
    name: str
    type: str
    notnull: int
    dflt_value: Optional[Any]
    pk: int


class TableSchemaResponse(BaseModel):
    """表结构响应模型"""
    table_name: str
    columns: List[ColumnInfo]


class TableDataResponse(BaseModel):
    """表数据响应模型"""
    table_name: str
    page: int
    page_size: int
    total_records: int
    total_pages: int
    data: List[Dict[str, Any]]


class RecordCreateRequest(BaseModel):
    """记录创建请求模型"""
    data: Dict[str, Any]


class RecordUpdateRequest(BaseModel):
    """记录更新请求模型"""
    data: Dict[str, Any]


class ConfigItem(BaseModel):
    """配置项模型"""
    id: int
    key: str
    value: str
    description: Optional[str]
    updated_at: str


class ConfigListResponse(BaseModel):
    """配置列表响应模型"""
    configs: List[ConfigItem]


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    value: str
    description: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    message: str


# ============================================================================
# 表管理API
# ============================================================================

@router.get("/tables", response_model=TableListResponse)
async def get_tables(admin: dict = Depends(auth.get_current_admin)):
    """
    获取所有数据表列表
    """
    tables = db.get_all_tables()
    
    table_info_list = []
    for table_name in tables:
        # 获取表记录数
        data, total = db.get_table_data(table_name, page=1, page_size=1)
        table_info_list.append(TableInfo(name=table_name, record_count=total))
    
    return TableListResponse(tables=table_info_list)


@router.get("/tables/{table_name}/schema", response_model=TableSchemaResponse)
async def get_table_schema(
    table_name: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取表结构信息
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    schema = db.get_table_schema(table_name)
    
    columns = [ColumnInfo(**col) for col in schema]
    
    return TableSchemaResponse(table_name=table_name, columns=columns)


@router.get("/tables/{table_name}/count")
async def get_table_count(
    table_name: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取表的记录数
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    _, total = db.get_table_data(table_name, page=1, page_size=1)
    
    return {"count": total}


@router.get("/tables/{table_name}")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(1000, ge=1, le=10000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取表数据（支持分页和搜索）
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    data, total = db.get_table_data(table_name, page, page_size, search)
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return {
        "table_name": table_name,
        "page": page,
        "page_size": page_size,
        "total_records": total,
        "total_pages": total_pages,
        "records": data
    }


@router.post("/tables/{table_name}", response_model=MessageResponse)
async def create_table_record(
    table_name: str,
    request: RecordCreateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    在表中插入新记录
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    try:
        record_id = db.insert_table_record(table_name, request.data)
        return MessageResponse(message=f"记录创建成功，ID: {record_id}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建记录失败: {str(e)}")


@router.put("/tables/{table_name}/{record_id}", response_model=MessageResponse)
async def update_table_record(
    table_name: str,
    record_id: int,
    request: RecordUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    更新表中的记录
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    try:
        success = db.update_table_record(table_name, record_id, request.data)
        
        if success:
            return MessageResponse(message=f"记录 {record_id} 更新成功")
        else:
            raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新记录失败: {str(e)}")


@router.delete("/tables/{table_name}/{record_id}", response_model=MessageResponse)
async def delete_table_record(
    table_name: str,
    record_id: int,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    删除表中的记录
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    try:
        success = db.delete_table_record(table_name, record_id)
        
        if success:
            return MessageResponse(message=f"记录 {record_id} 删除成功")
        else:
            raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除记录失败: {str(e)}")


# ============================================================================
# 系统配置API
# ============================================================================

@router.get("/config", response_model=ConfigListResponse)
async def get_all_configs(admin: dict = Depends(auth.get_current_admin)):
    """
    获取所有系统配置
    """
    configs = db.get_all_configs()
    
    config_items = [ConfigItem(**config) for config in configs]
    
    return ConfigListResponse(configs=config_items)


@router.put("/config/{key}", response_model=MessageResponse)
async def update_config(
    key: str,
    request: ConfigUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    更新系统配置
    """
    # 检查配置是否存在
    existing = db.get_config(key)
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"配置 {key} 不存在")
    
    try:
        success = db.set_config(key, request.value, request.description)
        
        if success:
            return MessageResponse(message=f"配置 {key} 更新成功")
        else:
            raise HTTPException(status_code=500, detail="配置更新失败")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")


@router.post("/config", response_model=MessageResponse)
async def create_or_update_config(
    request: Dict[str, Any],
    admin: dict = Depends(auth.get_current_admin)
):
    """
    创建或更新系统配置
    """
    key = request.get("key")
    value = request.get("value")
    description = request.get("description")
    
    if not key or value is None:
        raise HTTPException(status_code=400, detail="缺少必需字段: key 和 value")
    
    try:
        success = db.set_config(key, value, description)
        
        if success:
            return MessageResponse(message=f"配置 {key} 更新成功")
        else:
            raise HTTPException(status_code=500, detail="配置更新失败")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")


@router.delete("/config/{key}", response_model=MessageResponse)
async def delete_config(
    key: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    删除系统配置
    """
    # 检查配置是否存在
    existing = db.get_config(key)
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"配置 {key} 不存在")
    
    try:
        success = db.delete_config(key)
        
        if success:
            return MessageResponse(message=f"配置 {key} 删除成功")
        else:
            raise HTTPException(status_code=500, detail="配置删除失败")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除配置失败: {str(e)}")


# ============================================================================
# 缓存管理API
# ============================================================================


class CacheStatistics(BaseModel):
    """缓存统计信息模型"""
    db_size_mb: float
    max_size_mb: int
    size_usage_percent: float
    emails_cache: Dict[str, Any]
    details_cache: Dict[str, Any]
    hit_rate: Optional[float] = None


class CacheManagementResponse(BaseModel):
    """缓存管理响应模型"""
    message: str
    deleted_count: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@router.get("/cache/statistics", response_model=CacheStatistics)
async def get_cache_statistics(admin: dict = Depends(auth.get_current_admin)):
    """
    获取缓存统计信息
    
    返回缓存大小、记录数、命中率等统计数据
    """
    try:
        stats = db.check_cache_size()
        
        # 计算缓存命中率（基于access_count）
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 计算邮件列表缓存命中率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN access_count > 0 THEN 1 ELSE 0 END) as accessed
                FROM emails_cache
            """)
            row = cursor.fetchone()
            emails_total = row[0] if row else 0
            emails_accessed = row[1] if row else 0
            
            # 计算邮件详情缓存命中率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN access_count > 0 THEN 1 ELSE 0 END) as accessed
                FROM email_details_cache
            """)
            row = cursor.fetchone()
            details_total = row[0] if row else 0
            details_accessed = row[1] if row else 0
            
            # 综合命中率
            total_records = emails_total + details_total
            total_accessed = emails_accessed + details_accessed
            hit_rate = (total_accessed / total_records * 100) if total_records > 0 else 0
        
        stats['hit_rate'] = round(hit_rate, 2)
        
        return CacheStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.delete("/cache/{email_id}", response_model=CacheManagementResponse)
async def clear_account_cache(
    email_id: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    清除指定邮箱的缓存
    
    删除该邮箱的所有邮件列表和详情缓存
    """
    try:
        # 获取删除前的统计
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM emails_cache WHERE email_account = ?", (email_id,))
            emails_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM email_details_cache WHERE email_account = ?", (email_id,))
            details_count = cursor.fetchone()[0]
        
        # 清除缓存
        success = db.clear_email_cache_db(email_id)
        
        if success:
            return CacheManagementResponse(
                message=f"已清除 {email_id} 的缓存",
                deleted_count=emails_count + details_count,
                details={
                    'emails_deleted': emails_count,
                    'details_deleted': details_count
                }
            )
        else:
            raise HTTPException(status_code=500, detail="清除缓存失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.delete("/cache", response_model=CacheManagementResponse)
async def clear_all_cache(admin: dict = Depends(auth.get_current_admin)):
    """
    清除所有缓存
    
    删除所有邮件列表和详情缓存
    """
    try:
        # 获取删除前的统计
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM emails_cache")
            emails_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM email_details_cache")
            details_count = cursor.fetchone()[0]
        
        # 清除所有缓存
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emails_cache")
            cursor.execute("DELETE FROM email_details_cache")
            conn.commit()
        
        return CacheManagementResponse(
            message="已清除所有缓存",
            deleted_count=emails_count + details_count,
            details={
                'emails_deleted': emails_count,
                'details_deleted': details_count
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除所有缓存失败: {str(e)}")


@router.post("/cache/cleanup", response_model=CacheManagementResponse)
async def trigger_lru_cleanup(admin: dict = Depends(auth.get_current_admin)):
    """
    手动触发LRU缓存清理
    
    根据LRU策略清理最少访问的缓存记录
    """
    try:
        result = db.cleanup_lru_cache()
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return CacheManagementResponse(
            message="LRU清理完成",
            deleted_count=result['deleted_emails'] + result['deleted_details'],
            details=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LRU清理失败: {str(e)}")


# ============================================================================
# 用户管理API（仅管理员可访问）
# ============================================================================

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    role_filter: Optional[str] = Query(None, description="角色筛选 (admin/user)"),
    search: Optional[str] = Query(None, description="搜索关键词（用户名或邮箱）"),
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取所有用户列表（支持分页和筛选）
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    try:
        users, total = db.get_all_users(page, page_size, role_filter, search)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        user_infos = [
            UserInfo(
                id=user['id'],
                username=user['username'],
                email=user.get('email'),
                role=user.get('role', 'user'),
                bound_accounts=user.get('bound_accounts', []),
                permissions=user.get('permissions', []),
                is_active=bool(user['is_active']),
                created_at=user['created_at'],
                last_login=user.get('last_login')
            )
            for user in users
        ]
        
        return UserListResponse(
            total_users=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            users=user_infos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    创建新用户
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    try:
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(status_code=400, detail=f"用户名 {request.username} 已存在")
        
        # 创建用户
        password_hash = auth.hash_password(request.password)
        new_user = db.create_user(
            username=request.username,
            password_hash=password_hash,
            email=request.email,
            role=request.role,
            bound_accounts=request.bound_accounts or [],
            permissions=request.permissions or [],
            is_active=request.is_active
        )
        
        user_info = UserInfo(
            id=new_user['id'],
            username=new_user['username'],
            email=new_user.get('email'),
            role=new_user.get('role', 'user'),
            bound_accounts=new_user.get('bound_accounts', []),
            permissions=new_user.get('permissions', []),
            is_active=bool(new_user['is_active']),
            created_at=new_user['created_at'],
            last_login=new_user.get('last_login')
        )
        
        return UserResponse(
            message=f"用户 {request.username} 创建成功",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.get("/users/{username}", response_model=UserInfo)
async def get_user(
    username: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取用户详情
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    user = db.get_user_by_username(username)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    return UserInfo(
        id=user['id'],
        username=user['username'],
        email=user.get('email'),
        role=user.get('role', 'user'),
        bound_accounts=user.get('bound_accounts', []),
        permissions=user.get('permissions', []),
        is_active=bool(user['is_active']),
        created_at=user['created_at'],
        last_login=user.get('last_login')
    )


@router.put("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    request: UserUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    更新用户信息
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        # 构建更新数据
        update_data = {}
        if request.email is not None:
            update_data['email'] = request.email
        if request.role is not None:
            update_data['role'] = request.role
        if request.bound_accounts is not None:
            update_data['bound_accounts'] = request.bound_accounts
        if request.permissions is not None:
            update_data['permissions'] = request.permissions
        if request.is_active is not None:
            update_data['is_active'] = 1 if request.is_active else 0
        
        # 更新用户
        success = db.update_user(username, **update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="更新用户失败")
        
        # 获取更新后的用户信息
        updated_user = db.get_user_by_username(username)
        
        user_info = UserInfo(
            id=updated_user['id'],
            username=updated_user['username'],
            email=updated_user.get('email'),
            role=updated_user.get('role', 'user'),
            bound_accounts=updated_user.get('bound_accounts', []),
            permissions=updated_user.get('permissions', []),
            is_active=bool(updated_user['is_active']),
            created_at=updated_user['created_at'],
            last_login=updated_user.get('last_login')
        )
        
        return UserResponse(
            message=f"用户 {username} 更新成功",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.delete("/users/{username}", response_model=MessageResponse)
async def delete_user(
    username: str,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    删除用户
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 不能删除自己
    if username == admin['username']:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账户")
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        success = db.delete_user(username)
        
        if success:
            return MessageResponse(message=f"用户 {username} 删除成功")
        else:
            raise HTTPException(status_code=500, detail="删除用户失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")


@router.put("/users/{username}/permissions", response_model=UserResponse)
async def update_user_permissions(
    username: str,
    request: PermissionsUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    更新用户权限
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        success = db.update_user_permissions(username, request.permissions)
        
        if not success:
            raise HTTPException(status_code=500, detail="更新权限失败")
        
        # 获取更新后的用户信息
        updated_user = db.get_user_by_username(username)
        
        user_info = UserInfo(
            id=updated_user['id'],
            username=updated_user['username'],
            email=updated_user.get('email'),
            role=updated_user.get('role', 'user'),
            bound_accounts=updated_user.get('bound_accounts', []),
            permissions=updated_user.get('permissions', []),
            is_active=bool(updated_user['is_active']),
            created_at=updated_user['created_at'],
            last_login=updated_user.get('last_login')
        )
        
        return UserResponse(
            message=f"用户 {username} 权限更新成功",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新权限失败: {str(e)}")


@router.put("/users/{username}/bind-accounts", response_model=UserResponse)
async def bind_accounts(
    username: str,
    request: BindAccountsRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    绑定邮箱账户到用户
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        success = db.bind_accounts_to_user(username, request.account_emails)
        
        if not success:
            raise HTTPException(status_code=500, detail="绑定账户失败")
        
        # 获取更新后的用户信息
        updated_user = db.get_user_by_username(username)
        
        user_info = UserInfo(
            id=updated_user['id'],
            username=updated_user['username'],
            email=updated_user.get('email'),
            role=updated_user.get('role', 'user'),
            bound_accounts=updated_user.get('bound_accounts', []),
            permissions=updated_user.get('permissions', []),
            is_active=bool(updated_user['is_active']),
            created_at=updated_user['created_at'],
            last_login=updated_user.get('last_login')
        )
        
        return UserResponse(
            message=f"用户 {username} 账户绑定成功",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"绑定账户失败: {str(e)}")


@router.put("/users/{username}/role", response_model=UserResponse)
async def update_user_role(
    username: str,
    request: RoleUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    修改用户角色
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 不能修改自己的角色
    if username == admin['username']:
        raise HTTPException(status_code=400, detail="不能修改当前登录的管理员角色")
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        success = db.update_user(username, role=request.role)
        
        if not success:
            raise HTTPException(status_code=500, detail="修改角色失败")
        
        # 获取更新后的用户信息
        updated_user = db.get_user_by_username(username)
        
        user_info = UserInfo(
            id=updated_user['id'],
            username=updated_user['username'],
            email=updated_user.get('email'),
            role=updated_user.get('role', 'user'),
            bound_accounts=updated_user.get('bound_accounts', []),
            permissions=updated_user.get('permissions', []),
            is_active=bool(updated_user['is_active']),
            created_at=updated_user['created_at'],
            last_login=updated_user.get('last_login')
        )
        
        return UserResponse(
            message=f"用户 {username} 角色修改成功",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改角色失败: {str(e)}")


@router.put("/users/{username}/password", response_model=MessageResponse)
async def update_user_password(
    username: str,
    request: PasswordUpdateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    修改用户密码
    
    仅管理员可访问
    """
    # 检查管理员权限
    auth.require_admin(admin)
    
    # 检查用户是否存在
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
    
    try:
        # 哈希新密码
        new_password_hash = auth.hash_password(request.new_password)
        
        # 更新密码
        success = db.update_user_password(username, new_password_hash)
        
        if success:
            return MessageResponse(message=f"用户 {username} 密码修改成功")
        else:
            raise HTTPException(status_code=500, detail="修改密码失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")

