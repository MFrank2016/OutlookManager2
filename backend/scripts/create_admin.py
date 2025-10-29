#!/usr/bin/env python3
"""
创建管理员脚本

用于创建初始管理员账户
"""

import asyncio
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


async def create_admin():
    """创建管理员"""
    from src.domain.entities import Admin
    from src.domain.value_objects import EmailAddress
    from src.infrastructure.database.repositories import AdminRepositoryImpl
    from src.infrastructure.database.session import get_session, init_database
    from src.infrastructure.external_services.oauth import PasswordServiceImpl
    
    print("=" * 70)
    print("  创建管理员账户")
    print("=" * 70)
    print()
    
    # 初始化数据库
    await init_database()
    print("✓ 数据库已初始化")
    
    # 获取输入
    username = input("请输入用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        return
    
    password = input("请输入密码 (至少8个字符): ").strip()
    if len(password) < 8:
        print("❌ 密码长度至少为8个字符")
        return
    
    email_str = input("请输入邮箱地址 (可选，直接回车跳过): ").strip()
    email = EmailAddress.create(email_str) if email_str else None
    
    # 加密密码
    password_service = PasswordServiceImpl()
    password_hash = password_service.hash_password(password)
    
    # 创建管理员实体
    admin = Admin(
        username=username,
        password_hash=password_hash,
        email=email,
        is_active=True
    )
    
    # 保存到数据库
    async with get_session() as session:
        repository = AdminRepositoryImpl(session)
        
        # 检查用户名是否已存在
        existing = await repository.get_by_username(username)
        if existing:
            print(f"❌ 用户名 '{username}' 已存在")
            return
        
        # 创建管理员
        created_admin = await repository.create(admin)
        print()
        print("=" * 70)
        print("  ✓ 管理员创建成功！")
        print("=" * 70)
        print(f"  用户名: {created_admin.username}")
        print(f"  邮箱: {created_admin.email_str or '未设置'}")
        print(f"  状态: {'激活' if created_admin.is_active else '未激活'}")
        print(f"  创建时间: {created_admin.created_at}")
        print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(create_admin())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

