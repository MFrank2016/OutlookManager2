"""
认证路由模块

处理用户认证相关的API端点
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

import auth
import database as db

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=auth.Token)
async def login(request: auth.LoginRequest):
    """
    用户登录（支持所有角色）

    返回JWT访问令牌
    """
    user = auth.authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    db.update_user_login_time(request.username)

    # 创建访问令牌，包含角色和权限信息
    access_token = auth.create_access_token(data={
        "sub": user["username"],
        "role": user.get("role", "user"),
        "permissions": user.get("permissions", [])
    })

    logger.info(f"User {request.username} (role: {user.get('role')}) logged in successfully")

    return auth.Token(access_token=access_token)


@router.get("/me", response_model=auth.UserInfo)
async def get_current_user_info(user: dict = Depends(auth.get_current_user)):
    """
    获取当前登录的用户信息（含角色和权限）
    """
    return auth.UserInfo(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user.get("role", "user"),
        bound_accounts=user.get("bound_accounts", []),
        permissions=user.get("permissions", []),
        is_active=bool(user["is_active"]),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
    )


@router.post("/change-password")
async def change_password(
    request: auth.ChangePasswordRequest, user: dict = Depends(auth.get_current_user)
):
    """
    修改用户密码（所有角色均可使用）
    """
    # 验证旧密码
    if not auth.verify_password(request.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码
    new_password_hash = auth.hash_password(request.new_password)
    success = db.update_user_password(user["username"], new_password_hash)

    if success:
        logger.info(f"User {user['username']} changed password")
        return {"message": "密码修改成功"}
    else:
        raise HTTPException(status_code=500, detail="密码修改失败")

