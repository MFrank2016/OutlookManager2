"""
权限管理模块

定义系统权限常量和默认权限配置
"""

from typing import Dict, List

# ============================================================================
# 权限常量定义
# ============================================================================

class Permission:
    """权限常量类"""
    
    # 邮件相关权限
    VIEW_EMAILS = "view_emails"           # 查看邮件
    SEND_EMAILS = "send_emails"           # 发送邮件
    DELETE_EMAILS = "delete_emails"       # 删除邮件
    
    # 账户相关权限
    MANAGE_ACCOUNTS = "manage_accounts"   # 管理账户（修改标签等）
    
    # 系统管理权限
    VIEW_ADMIN_PANEL = "view_admin_panel" # 访问管理面板
    MANAGE_USERS = "manage_users"         # 管理用户
    MANAGE_CACHE = "manage_cache"         # 管理缓存
    MANAGE_CONFIG = "manage_config"       # 管理系统配置
    
    # 所有权限列表
    ALL_PERMISSIONS = [
        VIEW_EMAILS,
        SEND_EMAILS,
        DELETE_EMAILS,
        MANAGE_ACCOUNTS,
        VIEW_ADMIN_PANEL,
        MANAGE_USERS,
        MANAGE_CACHE,
        MANAGE_CONFIG,
    ]


# ============================================================================
# 角色常量定义
# ============================================================================

class Role:
    """角色常量类"""
    
    ADMIN = "admin"  # 管理员
    USER = "user"    # 普通用户


# ============================================================================
# 默认权限配置
# ============================================================================

# 管理员默认权限（拥有所有权限）
ADMIN_DEFAULT_PERMISSIONS = Permission.ALL_PERMISSIONS.copy()

# 普通用户默认权限（仅查看邮件）
USER_DEFAULT_PERMISSIONS = [
    Permission.VIEW_EMAILS,
]

# 根据角色获取默认权限
def get_default_permissions(role: str) -> List[str]:
    """
    根据角色获取默认权限列表
    
    Args:
        role: 用户角色 (admin/user)
        
    Returns:
        权限列表
    """
    if role == Role.ADMIN:
        return ADMIN_DEFAULT_PERMISSIONS.copy()
    elif role == Role.USER:
        return USER_DEFAULT_PERMISSIONS.copy()
    else:
        return []


# ============================================================================
# 权限描述映射
# ============================================================================

PERMISSION_DESCRIPTIONS: Dict[str, str] = {
    Permission.VIEW_EMAILS: "查看邮件",
    Permission.SEND_EMAILS: "发送邮件",
    Permission.DELETE_EMAILS: "删除邮件",
    Permission.MANAGE_ACCOUNTS: "管理账户（修改标签等）",
    Permission.VIEW_ADMIN_PANEL: "访问管理面板",
    Permission.MANAGE_USERS: "管理用户",
    Permission.MANAGE_CACHE: "管理缓存",
    Permission.MANAGE_CONFIG: "管理系统配置",
}


def get_permission_description(permission: str) -> str:
    """
    获取权限描述
    
    Args:
        permission: 权限名称
        
    Returns:
        权限描述
    """
    return PERMISSION_DESCRIPTIONS.get(permission, permission)

