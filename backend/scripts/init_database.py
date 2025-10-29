#!/usr/bin/env python3
"""
数据库初始化脚本

初始化数据库表并可选地创建默认管理员
"""

import asyncio
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


async def init_db():
    """初始化数据库"""
    from src.domain.entities import Admin
    from src.infrastructure.database.repositories import AdminRepositoryImpl
    from src.infrastructure.database.session import get_session, init_database
    from src.infrastructure.external_services.oauth import PasswordServiceImpl
    
    print("=" * 70)
    print("  Outlook邮件管理系统 - 数据库初始化")
    print("=" * 70)
    print()
    
    # 初始化数据库表
    print("正在创建数据库表...")
    await init_database()
    print("✓ 数据库表创建成功")
    print()
    
    # 询问是否创建默认管理员
    create_default = input("是否创建默认管理员账户? (y/n): ").strip().lower()
    
    if create_default == 'y':
        print()
        print("-" * 70)
        print("  创建默认管理员账户")
        print("-" * 70)
        
        # 默认值
        default_username = "admin"
        default_password = "admin123"
        
        print(f"默认用户名: {default_username}")
        print(f"默认密码: {default_password}")
        print()
        
        confirm = input("使用默认值创建? (y/n): ").strip().lower()
        
        if confirm == 'y':
            # 加密密码
            password_service = PasswordServiceImpl()
            password_hash = password_service.hash_password(default_password)
            
            # 创建管理员实体
            admin = Admin(
                username=default_username,
                password_hash=password_hash,
                is_active=True
            )
            
            # 保存到数据库
            async with get_session() as session:
                repository = AdminRepositoryImpl(session)
                
                # 检查是否已存在
                existing = await repository.get_by_username(default_username)
                if existing:
                    print(f"⚠ 管理员 '{default_username}' 已存在，跳过创建")
                else:
                    created_admin = await repository.create(admin)
                    print()
                    print("✓ 默认管理员创建成功！")
                    print(f"  用户名: {created_admin.username}")
                    print(f"  密码: {default_password}")
                    print(f"  ⚠ 请在生产环境中修改默认密码！")
    
    print()
    print("=" * 70)
    print("  ✓ 数据库初始化完成！")
    print("=" * 70)
    print()
    print("下一步:")
    print("  1. 启动应用: python run_dev.py")
    print("  2. 访问API文档: http://localhost:8000/api/docs")
    print("  3. 使用管理员账户登录")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

