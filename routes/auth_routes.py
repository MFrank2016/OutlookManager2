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
    管理员登录

    返回JWT访问令牌
    """
    admin = auth.authenticate_admin(request.username, request.password)

    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    db.update_admin_login_time(request.username)

    # 创建访问令牌
    access_token = auth.create_access_token(data={"sub": admin["username"]})

    logger.info(f"Admin {request.username} logged in successfully")

    return auth.Token(access_token=access_token)


@router.get("/me", response_model=auth.AdminInfo)
async def get_current_user(admin: dict = Depends(auth.get_current_admin)):
    """
    获取当前登录的管理员信息
    """
    return auth.AdminInfo(
        id=admin["id"],
        username=admin["username"],
        email=admin.get("email"),
        is_active=bool(admin["is_active"]),
        created_at=admin["created_at"],
        last_login=admin.get("last_login"),
    )


@router.post("/change-password")
async def change_password(
    request: auth.ChangePasswordRequest, admin: dict = Depends(auth.get_current_admin)
):
    """
    修改管理员密码
    """
    # 验证旧密码
    if not auth.verify_password(request.old_password, admin["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码
    new_password_hash = auth.hash_password(request.new_password)
    success = db.update_admin_password(admin["username"], new_password_hash)

    if success:
        logger.info(f"Admin {admin['username']} changed password")
        return {"message": "密码修改成功"}
    else:
        raise HTTPException(status_code=500, detail="密码修改失败")

