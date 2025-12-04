"""
管理面板API模块

提供数据表管理和系统配置管理的API接口
"""

from typing import Any, Dict, List, Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

import auth
import database as db
import cache_service
from logger_config import logger
from datetime import datetime
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


def _convert_datetime_to_str(value):
    """将 datetime 对象转换为 ISO 格式字符串"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _extract_scalar_value(row: Any) -> Any:
    """从数据库查询结果中提取标量值"""
    if row is None:
        return None
    if isinstance(row, (list, tuple)) and len(row) > 0:
        return row[0]
    if isinstance(row, dict) and len(row) > 0:
        return list(row.values())[0]
    return row

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
    try:
        tables = db.get_all_tables()
        
        table_info_list = []
        for table_name in tables:
            try:
                # 获取表记录数
                data, total = db.get_table_data(table_name, page=1, page_size=1)
                table_info_list.append(TableInfo(name=table_name, record_count=total))
            except sqlite3.DatabaseError as e:
                # 如果某个表损坏，记录错误但继续处理其他表
                error_msg = str(e)
                if "malformed" in error_msg.lower() or "corrupt" in error_msg.lower():
                    logger.error(f"Table {table_name} is corrupted, skipping: {e}")
                    # 仍然添加表信息，但标记为错误
                    table_info_list.append(TableInfo(name=table_name, record_count=-1))
                else:
                    raise
            except Exception as e:
                logger.error(f"Error getting data for table {table_name}: {e}")
                # 仍然添加表信息，但标记为错误
                table_info_list.append(TableInfo(name=table_name, record_count=-1))
        
        return TableListResponse(tables=table_info_list)
    except Exception as e:
        logger.error(f"Error getting tables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


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
    search: Optional[str] = Query(None, description="搜索关键词（全字段搜索）"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: str = Query("asc", description="排序方向（asc/desc）"),
    field_search: Optional[str] = Query(None, description="字段搜索（JSON格式：{\"字段名\":\"搜索值\"}）"),
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取表数据（支持分页、搜索、排序和字段筛选）
    """
    # 验证表是否存在
    tables = db.get_all_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    # 解析字段搜索JSON
    field_search_dict = None
    if field_search:
        try:
            import json
            field_search_dict = json.loads(field_search)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="字段搜索参数格式错误，应为JSON格式")
    
    data, total = db.get_table_data(
        table_name, 
        page, 
        page_size, 
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        field_search=field_search_dict
    )
    
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
    
    # 将 datetime 对象转换为字符串
    config_items = []
    for config in configs:
        config_dict = dict(config)
        # 如果 updated_at 是 datetime 对象，转换为 ISO 格式字符串
        if 'updated_at' in config_dict:
            config_dict['updated_at'] = _convert_datetime_to_str(config_dict['updated_at'])
        config_items.append(ConfigItem(**config_dict))
    
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
        # 获取SQLite缓存统计
        stats = db.check_cache_size()
        
        # 获取内存LRU缓存统计
        lru_stats = cache_service.get_cache_stats()
        
        # 合并统计信息
        stats['lru_cache'] = lru_stats
        
        # 计算缓存命中率（基于access_count）
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 计算邮件列表缓存命中率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN access_count > 0 THEN 1 ELSE 0 END), 0) as accessed
                FROM emails_cache
            """)
            row = cursor.fetchone()
            # 处理PostgreSQL字典格式和SQLite元组格式
            # PostgreSQL的RealDictRow支持字典访问，但不一定是dict类型
            try:
                if row is None:
                    emails_total = 0
                    emails_accessed = 0
                elif hasattr(row, 'get'):
                    # PostgreSQL RealDictRow 或 dict（支持字典访问）
                    emails_total = row.get('total', 0) or 0
                    emails_accessed = row.get('accessed', 0) or 0
                else:
                    # 元组或列表格式（SQLite）
                    emails_total = row[0] if row and len(row) > 0 and row[0] is not None else 0
                    emails_accessed = row[1] if row and len(row) > 1 and row[1] is not None else 0
            except (IndexError, TypeError, KeyError, AttributeError) as e:
                logger.error(f"Error extracting emails cache stats: {e}, row type: {type(row)}")
                emails_total = 0
                emails_accessed = 0
            
            # 计算邮件详情缓存命中率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN access_count > 0 THEN 1 ELSE 0 END), 0) as accessed
                FROM email_details_cache
            """)
            row = cursor.fetchone()
            # 处理PostgreSQL字典格式和SQLite元组格式
            try:
                if row is None:
                    details_total = 0
                    details_accessed = 0
                elif hasattr(row, 'get'):
                    # PostgreSQL RealDictRow 或 dict（支持字典访问）
                    details_total = row.get('total', 0) or 0
                    details_accessed = row.get('accessed', 0) or 0
                else:
                    # 元组或列表格式（SQLite）
                    details_total = row[0] if row and len(row) > 0 and row[0] is not None else 0
                    details_accessed = row[1] if row and len(row) > 1 and row[1] is not None else 0
            except (IndexError, TypeError, KeyError, AttributeError) as e:
                logger.error(f"Error extracting details cache stats: {e}, row type: {type(row)}")
                details_total = 0
                details_accessed = 0
            
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
        
        # 清除缓存（包括LRU内存缓存和SQLite缓存）
        cache_service.clear_email_cache(email_id)
        cache_service.clear_cached_access_token(email_id)
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
        
        # 清除所有缓存（包括LRU内存缓存和SQLite缓存）
        cache_service.clear_all_cache()
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emails_cache")
            cursor.execute("DELETE FROM email_details_cache")
            conn.commit()
        
        return CacheManagementResponse(
            message="已清除所有缓存（包括LRU内存缓存和SQLite缓存）",
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
        
        user_infos = []
        for user in users:
            user_infos.append(
                UserInfo(
                    id=user['id'],
                    username=user['username'],
                    email=user.get('email'),
                    role=user.get('role', 'user'),
                    bound_accounts=user.get('bound_accounts', []),
                    permissions=user.get('permissions', []),
                    is_active=bool(user['is_active']),
                    created_at=_convert_datetime_to_str(user['created_at']),
                    last_login=_convert_datetime_to_str(user.get('last_login'))
                )
            )
        
        return UserListResponse(
            total_users=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            users=user_infos
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
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
            created_at=_convert_datetime_to_str(new_user['created_at']),
            last_login=_convert_datetime_to_str(new_user.get('last_login'))
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
        created_at=_convert_datetime_to_str(user['created_at']),
        last_login=_convert_datetime_to_str(user.get('last_login'))
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
            created_at=_convert_datetime_to_str(updated_user['created_at']),
            last_login=_convert_datetime_to_str(updated_user.get('last_login'))
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
            created_at=_convert_datetime_to_str(updated_user['created_at']),
            last_login=_convert_datetime_to_str(updated_user.get('last_login'))
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
            created_at=_convert_datetime_to_str(updated_user['created_at']),
            last_login=_convert_datetime_to_str(updated_user.get('last_login'))
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
            created_at=_convert_datetime_to_str(updated_user['created_at']),
            last_login=_convert_datetime_to_str(updated_user.get('last_login'))
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
        logger.info(f"Updating password for user: {username}")
        new_password_hash = auth.hash_password(request.new_password)
        logger.debug(f"Password hashed successfully for {username}, hash length: {len(new_password_hash)}")
        
        # 更新密码
        success = db.update_user_password(username, new_password_hash)
        
        if success:
            logger.info(f"Password updated successfully for user: {username}")
            # 验证密码是否正确保存（可选，用于调试）
            updated_user = db.get_user_by_username(username)
            if updated_user and updated_user.get('password_hash'):
                # 验证哈希后的密码是否能正确验证
                test_verify = auth.verify_password(request.new_password, updated_user['password_hash'])
                if not test_verify:
                    logger.error(f"WARNING: Password hash verification failed immediately after update for {username}")
                else:
                    logger.debug(f"Password hash verification passed for {username}")
            return MessageResponse(message=f"用户 {username} 密码修改成功")
        else:
            raise HTTPException(status_code=500, detail="修改密码失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")


# ============================================================================
# SQL查询管理API
# ============================================================================

class SqlExecuteRequest(BaseModel):
    """SQL执行请求模型"""
    sql: str
    max_rows: Optional[int] = 10000  # 最大返回行数限制


class SqlExecuteResponse(BaseModel):
    """SQL执行响应模型"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    execution_time_ms: int
    error_message: Optional[str] = None


class SqlQueryHistoryItem(BaseModel):
    """SQL查询历史记录项"""
    id: int
    sql_query: str
    result_count: Optional[int]
    execution_time_ms: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: str
    created_by: Optional[str]


class SqlQueryHistoryResponse(BaseModel):
    """SQL查询历史记录响应"""
    total: int
    page: int
    page_size: int
    total_pages: int
    history: List[SqlQueryHistoryItem]


class SqlQueryFavoriteItem(BaseModel):
    """SQL查询收藏项"""
    id: int
    name: str
    sql_query: str
    description: Optional[str]
    created_at: str
    created_by: Optional[str]
    updated_at: str


class SqlQueryFavoriteListResponse(BaseModel):
    """SQL查询收藏列表响应"""
    favorites: List[SqlQueryFavoriteItem]


class SqlQueryFavoriteCreateRequest(BaseModel):
    """创建SQL收藏请求"""
    name: str
    sql_query: str
    description: Optional[str] = None


@router.post("/sql/execute", response_model=SqlExecuteResponse)
async def execute_sql(
    request: SqlExecuteRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    执行SQL查询（支持所有SQL语句，包括INSERT/UPDATE/DELETE）
    
    注意：此接口允许执行所有SQL语句，请谨慎使用
    """
    import time
    start_time = time.time()
    
    try:
        # 限制最大返回行数
        max_rows = min(request.max_rows or 10000, 10000)
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 执行SQL
            cursor.execute(request.sql)
            
            # 判断是查询还是DML语句
            sql_upper = request.sql.strip().upper()
            is_select = sql_upper.startswith('SELECT')
            
            if is_select:
                # SELECT查询，返回结果
                rows = cursor.fetchall()
                row_count = len(rows)
                
                # 限制返回行数
                if row_count > max_rows:
                    rows = rows[:max_rows]
                    logger.warning(f"SQL query returned {row_count} rows, limited to {max_rows}")
                
                # 转换为字典列表
                if rows:
                    if isinstance(rows[0], dict):
                        data = list(rows)
                    else:
                        # 获取列名
                        if hasattr(cursor, 'description') and cursor.description:
                            columns = [desc[0] for desc in cursor.description]
                            data = [dict(zip(columns, row)) for row in rows]
                        else:
                            data = [{"result": str(row)} for row in rows]
                else:
                    data = []
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # 保存历史记录
                try:
                    _save_sql_history(
                        request.sql,
                        row_count,
                        execution_time_ms,
                        'success',
                        None,
                        admin.get('username')
                    )
                except Exception as e:
                    logger.warning(f"Failed to save SQL history: {e}")
                
                return SqlExecuteResponse(
                    success=True,
                    data=data,
                    row_count=row_count,
                    execution_time_ms=execution_time_ms
                )
            else:
                # DML语句（INSERT/UPDATE/DELETE），返回影响行数
                conn.commit()
                affected_rows = cursor.rowcount
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # 保存历史记录
                try:
                    _save_sql_history(
                        request.sql,
                        affected_rows,
                        execution_time_ms,
                        'success',
                        None,
                        admin.get('username')
                    )
                except Exception as e:
                    logger.warning(f"Failed to save SQL history: {e}")
                
                return SqlExecuteResponse(
                    success=True,
                    data=[{"affected_rows": affected_rows}],
                    row_count=affected_rows,
                    execution_time_ms=execution_time_ms
                )
                
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_message = str(e)
        logger.error(f"SQL execution error: {error_message}")
        
        # 保存错误历史记录
        try:
            _save_sql_history(
                request.sql,
                None,
                execution_time_ms,
                'error',
                error_message,
                admin.get('username')
            )
        except Exception as save_error:
            logger.warning(f"Failed to save SQL error history: {save_error}")
        
        return SqlExecuteResponse(
            success=False,
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )


def _save_sql_history(
    sql_query: str,
    result_count: Optional[int],
    execution_time_ms: int,
    status: str,
    error_message: Optional[str],
    created_by: Optional[str]
):
    """保存SQL查询历史记录"""
    from config import DB_TYPE
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        param_placeholder = "%s" if DB_TYPE == "postgresql" else "?"
        cursor.execute(
            f"""
            INSERT INTO sql_query_history 
            (sql_query, result_count, execution_time_ms, status, error_message, created_by)
            VALUES ({param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder})
            """,
            (sql_query, result_count, execution_time_ms, status, error_message, created_by)
        )
        conn.commit()


@router.get("/sql/history", response_model=SqlQueryHistoryResponse)
async def get_sql_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取SQL查询历史记录（支持分页）
    """
    try:
        from config import DB_TYPE
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            param_placeholder = "%s" if DB_TYPE == "postgresql" else "?"
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM sql_query_history")
            row = cursor.fetchone()
            total = _extract_scalar_value(row)
            
            # 获取分页数据
            offset = (page - 1) * page_size
            if DB_TYPE == "postgresql":
                cursor.execute(
                    f"""
                    SELECT * FROM sql_query_history 
                    ORDER BY created_at DESC 
                    LIMIT {param_placeholder} OFFSET {param_placeholder}
                    """,
                    (page_size, offset)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM sql_query_history 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                    """,
                    (page_size, offset)
                )
            
            rows = cursor.fetchall()
            history_items = []
            for row in rows:
                row_dict = dict(row)
                history_items.append(SqlQueryHistoryItem(
                    id=row_dict['id'],
                    sql_query=row_dict['sql_query'],
                    result_count=row_dict.get('result_count'),
                    execution_time_ms=row_dict.get('execution_time_ms'),
                    status=row_dict.get('status', 'success'),
                    error_message=row_dict.get('error_message'),
                    created_at=_convert_datetime_to_str(row_dict.get('created_at')),
                    created_by=row_dict.get('created_by')
                ))
            
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return SqlQueryHistoryResponse(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                history=history_items
            )
    except Exception as e:
        logger.error(f"Error getting SQL history: {e}")
        raise HTTPException(status_code=500, detail=f"获取SQL历史记录失败: {str(e)}")


@router.get("/sql/favorites", response_model=SqlQueryFavoriteListResponse)
async def get_sql_favorites(
    admin: dict = Depends(auth.get_current_admin)
):
    """
    获取SQL查询收藏列表
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sql_query_favorites ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            
            favorites = []
            for row in rows:
                row_dict = dict(row)
                favorites.append(SqlQueryFavoriteItem(
                    id=row_dict['id'],
                    name=row_dict['name'],
                    sql_query=row_dict['sql_query'],
                    description=row_dict.get('description'),
                    created_at=_convert_datetime_to_str(row_dict.get('created_at')),
                    created_by=row_dict.get('created_by'),
                    updated_at=_convert_datetime_to_str(row_dict.get('updated_at'))
                ))
            
            return SqlQueryFavoriteListResponse(favorites=favorites)
    except Exception as e:
        logger.error(f"Error getting SQL favorites: {e}")
        raise HTTPException(status_code=500, detail=f"获取SQL收藏失败: {str(e)}")


@router.post("/sql/favorites", response_model=MessageResponse)
async def create_sql_favorite(
    request: SqlQueryFavoriteCreateRequest,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    创建SQL查询收藏
    """
    try:
        from config import DB_TYPE
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            param_placeholder = "%s" if DB_TYPE == "postgresql" else "?"
            
            if DB_TYPE == "postgresql":
                cursor.execute(
                    f"""
                    INSERT INTO sql_query_favorites (name, sql_query, description, created_by)
                    VALUES ({param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder})
                    RETURNING id
                    """,
                    (request.name, request.sql_query, request.description, admin.get('username'))
                )
                result = cursor.fetchone()
                favorite_id = result['id'] if result else None
            else:
                cursor.execute(
                    """
                    INSERT INTO sql_query_favorites (name, sql_query, description, created_by)
                    VALUES (?, ?, ?, ?)
                    """,
                    (request.name, request.sql_query, request.description, admin.get('username'))
                )
                favorite_id = cursor.lastrowid
            
            conn.commit()
            return MessageResponse(message=f"SQL收藏创建成功，ID: {favorite_id}")
    except Exception as e:
        logger.error(f"Error creating SQL favorite: {e}")
        raise HTTPException(status_code=400, detail=f"创建SQL收藏失败: {str(e)}")


@router.delete("/sql/favorites/{favorite_id}", response_model=MessageResponse)
async def delete_sql_favorite(
    favorite_id: int,
    admin: dict = Depends(auth.get_current_admin)
):
    """
    删除SQL查询收藏
    """
    try:
        from config import DB_TYPE
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            param_placeholder = "%s" if DB_TYPE == "postgresql" else "?"
            
            cursor.execute(
                f"DELETE FROM sql_query_favorites WHERE id = {param_placeholder}",
                (favorite_id,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                return MessageResponse(message=f"SQL收藏 {favorite_id} 删除成功")
            else:
                raise HTTPException(status_code=404, detail=f"SQL收藏 {favorite_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SQL favorite: {e}")
        raise HTTPException(status_code=500, detail=f"删除SQL收藏失败: {str(e)}")

