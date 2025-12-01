"""
认证路由模块

处理用户认证相关的API端点
"""

import asyncio
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
    logger.info(f"=== LOGIN REQUEST RECEIVED ===")
    logger.info(f"Login attempt for user: {request.username}")
    logger.info(f"Request body: username={request.username}, password={'*' * len(request.password)}")
    try:
        # 验证用户名和密码（使用API请求专用线程池，避免被后台任务阻塞）
        logger.debug(f"Authenticating user: {request.username}")
        try:
            # 导入API请求专用线程池
            from main import api_requests_executor
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(
                api_requests_executor, 
                auth.authenticate_user, 
                request.username, 
                request.password
            )
        except Exception as e:
            logger.error(f"Error in authenticate_user for {request.username}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"认证过程出错: {str(e)}")
        
        logger.debug(f"Authentication result: {user is not None}")

        if not user:
            logger.warning(f"Login failed for user: {request.username} (user not found or password incorrect)")
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 更新最后登录时间（使用API请求专用线程池，避免被后台任务阻塞）
        try:
            from main import api_requests_executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(api_requests_executor, db.update_user_login_time, request.username)
        except Exception as e:
            logger.warning(f"Failed to update login time for {request.username}: {e}")
            # 不影响登录流程，继续执行

        # 创建访问令牌，包含角色和权限信息
        try:
            # 确保 permissions 是列表类型（可能已经是列表，因为 DAO 已经解析了 JSON）
            permissions = user.get("permissions", [])
            if isinstance(permissions, str):
                import json
                try:
                    permissions = json.loads(permissions) if permissions else []
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse permissions JSON for {request.username}: {e}")
                    permissions = []
            
            access_token = auth.create_access_token(data={
                "sub": user["username"],
                "role": user.get("role", "user"),
                "permissions": permissions
            })
        except Exception as e:
            logger.error(f"Failed to create access token for {request.username}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="创建访问令牌失败")

        logger.info(f"User {request.username} (role: {user.get('role')}) logged in successfully")

        return auth.Token(access_token=access_token)
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for {request.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


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
    # 验证旧密码（使用API请求专用线程池，避免被后台任务阻塞）
    from main import api_requests_executor
    loop = asyncio.get_event_loop()
    password_valid = await loop.run_in_executor(
        api_requests_executor,
        auth.verify_password, request.old_password, user["password_hash"]
    )
    if not password_valid:
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码（使用API请求专用线程池，避免被后台任务阻塞）
    new_password_hash = await loop.run_in_executor(api_requests_executor, auth.hash_password, request.new_password)
    success = await loop.run_in_executor(api_requests_executor, db.update_user_password, user["username"], new_password_hash)

    if success:
        logger.info(f"User {user['username']} changed password")
        return {"message": "密码修改成功"}
    else:
        raise HTTPException(status_code=500, detail="密码修改失败")

