"""
JWT认证模块

提供用户认证、JWT token生成和验证、密码加密等功能
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import database as db

# JWT配置
SECRET_KEY = secrets.token_urlsafe(32)  # 生产环境应从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证（可选，支持API Key）
security = HTTPBearer(auto_error=False)


# ============================================================================
# Pydantic模型
# ============================================================================

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str


class AdminInfo(BaseModel):
    """管理员信息模型（向后兼容）"""
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    email: Optional[str] = None
    role: str  # admin or user
    bound_accounts: list = []
    permissions: list = []
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


# ============================================================================
# 密码处理函数
# ============================================================================

def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    
    Args:
        password: 明文密码
        
    Returns:
        密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希值
        
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token函数
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据（应包含 sub, role, permissions）
        expires_delta: 过期时间增量
        
    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    验证JWT token
    
    Args:
        token: JWT token字符串
        
    Returns:
        TokenData对象
        
    Raises:
        HTTPException: token无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        return TokenData(username=username)
    
    except JWTError:
        raise credentials_exception


# ============================================================================
# 认证函数
# ============================================================================

def verify_api_key(api_key: str) -> bool:
    """
    验证API Key是否正确
    
    Args:
        api_key: API Key值
        
    Returns:
        是否验证通过
    """
    stored_key = db.get_api_key()
    if not stored_key:
        return False
    
    return api_key == stored_key


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    验证用户名和密码
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        用户信息字典或None
    """
    user = db.get_user_by_username(username)
    
    if not user:
        return None
    
    if not verify_password(password, user['password_hash']):
        return None
    
    if not user['is_active']:
        return None
    
    return user


# 向后兼容的别名
def authenticate_admin(username: str, password: str) -> Optional[dict]:
    """
    验证管理员用户名和密码（向后兼容）
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        管理员信息字典或None
    """
    return authenticate_user(username, password)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    获取当前已认证的用户
    
    支持两种认证方式：
    1. JWT Token (Authorization: Bearer <token>)
    2. API Key (X-API-Key: <key> 或 Authorization: ApiKey <key>)
    
    用作FastAPI依赖注入
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭据（可选）
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 未认证或认证失败
    """
    # 方式1: 尝试从 X-API-Key 头获取 API Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if verify_api_key(api_key):
            # API Key认证成功，返回默认管理员（第一个管理员）
            admins = db.get_users_by_role("admin")
            if admins:
                user = admins[0]
                if user.get('is_active'):
                    return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    # 方式2: 尝试从 Authorization 头获取 API Key (格式: ApiKey <key>)
    if credentials and credentials.scheme.lower() == "apikey":
        if verify_api_key(credentials.credentials):
            # API Key认证成功
            admins = db.get_users_by_role("admin")
            if admins:
                user = admins[0]
                if user.get('is_active'):
                    return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    # 方式3: JWT Token认证 (Authorization: Bearer <token>)
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        token_data = verify_token(token)
        
        user = db.get_user_by_username(token_data.username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        return user
    
    # 没有提供任何有效的认证信息
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未提供认证信息或认证信息无效",
        headers={"WWW-Authenticate": "Bearer"}
    )


# 向后兼容的别名
async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    获取当前已认证的管理员（向后兼容）
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭据（可选）
        
    Returns:
        管理员信息字典
        
    Raises:
        HTTPException: 未认证或认证失败
    """
    return await get_current_user(request, credentials)


# ============================================================================
# 权限检查函数
# ============================================================================

def require_admin(user: dict) -> None:
    """
    要求管理员权限
    
    Args:
        user: 用户信息字典
        
    Raises:
        HTTPException: 如果用户不是管理员
    """
    from permissions import Role
    
    if user.get('role') != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )


def require_permission(user: dict, permission: str) -> None:
    """
    要求特定权限
    
    Args:
        user: 用户信息字典
        permission: 权限名称
        
    Raises:
        HTTPException: 如果用户没有该权限
    """
    from permissions import Role
    
    # 管理员拥有所有权限
    if user.get('role') == Role.ADMIN:
        return
    
    user_permissions = user.get('permissions', [])
    if permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要权限: {permission}"
        )


def check_account_access(user: dict, email_id: str) -> bool:
    """
    检查用户是否有权访问指定邮箱账户
    
    Args:
        user: 用户信息字典
        email_id: 邮箱账户
        
    Returns:
        是否有权访问
    """
    from permissions import Role
    
    # 管理员可以访问所有账户
    if user.get('role') == Role.ADMIN:
        return True
    
    # 普通用户只能访问绑定的账户
    bound_accounts = user.get('bound_accounts', [])
    return email_id in bound_accounts


def get_accessible_accounts(user: dict) -> list:
    """
    获取用户可访问的邮箱账户列表
    
    Args:
        user: 用户信息字典
        
    Returns:
        邮箱账户列表（管理员返回None表示所有账户）
    """
    from permissions import Role
    
    # 管理员可以访问所有账户
    if user.get('role') == Role.ADMIN:
        return None  # None 表示所有账户
    
    # 普通用户返回绑定的账户列表
    return user.get('bound_accounts', [])


# ============================================================================
# 初始化默认管理员
# ============================================================================

def init_default_admin(username: str = "admin", password: str = "admin123") -> None:
    """
    初始化默认管理员账户
    
    Args:
        username: 管理员用户名
        password: 管理员密码
    """
    # 检查是否已存在该用户
    existing_user = db.get_user_by_username(username)
    
    if existing_user:
        print(f"用户 '{username}' 已存在，跳过创建")
        return
    
    # 创建默认管理员
    password_hash = hash_password(password)
    db.create_user(username, password_hash, role="admin")
    
    print(f"默认管理员已创建:")
    print(f"  用户名: {username}")
    print(f"  密码: {password}")
    print(f"  请首次登录后立即修改密码！")

