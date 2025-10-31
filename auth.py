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
    """管理员信息模型"""
    id: int
    username: str
    email: Optional[str] = None
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
        data: 要编码的数据
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


def authenticate_admin(username: str, password: str) -> Optional[dict]:
    """
    验证管理员用户名和密码
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        管理员信息字典或None
    """
    admin = db.get_admin_by_username(username)
    
    if not admin:
        return None
    
    if not verify_password(password, admin['password_hash']):
        return None
    
    if not admin['is_active']:
        return None
    
    return admin


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    获取当前已认证的管理员
    
    支持两种认证方式：
    1. JWT Token (Authorization: Bearer <token>)
    2. API Key (X-API-Key: <key> 或 Authorization: ApiKey <key>)
    
    用作FastAPI依赖注入
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭据（可选）
        
    Returns:
        管理员信息字典
        
    Raises:
        HTTPException: 未认证或认证失败
    """
    # 方式1: 尝试从 X-API-Key 头获取 API Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if verify_api_key(api_key):
            # API Key认证成功，返回默认管理员（第一个管理员）
            admins = db.get_all_admins()
            if admins:
                admin = admins[0]
                if admin.get('is_active'):
                    return admin
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    # 方式2: 尝试从 Authorization 头获取 API Key (格式: ApiKey <key>)
    if credentials and credentials.scheme.lower() == "apikey":
        if verify_api_key(credentials.credentials):
            # API Key认证成功
            admins = db.get_all_admins()
            if admins:
                admin = admins[0]
                if admin.get('is_active'):
                    return admin
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    # 方式3: JWT Token认证 (Authorization: Bearer <token>)
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        token_data = verify_token(token)
        
        admin = db.get_admin_by_username(token_data.username)
        
        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理员不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not admin['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员账户已被禁用"
            )
        
        return admin
    
    # 没有提供任何有效的认证信息
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未提供认证信息或认证信息无效",
        headers={"WWW-Authenticate": "Bearer"}
    )


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
    # 检查是否已存在管理员
    existing_admin = db.get_admin_by_username(username)
    
    if existing_admin:
        print(f"管理员 '{username}' 已存在，跳过创建")
        return
    
    # 创建默认管理员
    password_hash = hash_password(password)
    db.create_admin(username, password_hash)
    
    print(f"默认管理员已创建:")
    print(f"  用户名: {username}")
    print(f"  密码: {password}")
    print(f"  请首次登录后立即修改密码！")

