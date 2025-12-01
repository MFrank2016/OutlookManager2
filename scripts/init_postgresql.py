#!/usr/bin/env python3
"""
PostgreSQL数据库初始化脚本

用于在PostgreSQL数据库中创建所有必要的表和索引
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import database as db
import auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("PostgreSQL数据库初始化")
    print("=" * 60)
    print()
    
    try:
        # 检查数据库类型
        from config import DB_TYPE
        if DB_TYPE != "postgresql":
            print(f"❌ 当前数据库类型为 {DB_TYPE}，不是 PostgreSQL")
            print("💡 提示: 设置环境变量 DB_TYPE=postgresql 以使用PostgreSQL")
            return False
        
        # 初始化数据库（创建表和索引）
        print("步骤1: 创建数据库表和索引...")
        db.init_database()
        print("✅ 数据库表和索引创建成功")
        print()
        
        # 初始化默认管理员
        print("步骤2: 初始化默认管理员账户...")
        auth.init_default_admin()
        print("✅ 默认管理员账户初始化成功")
        print()
        
        # 初始化API Key
        print("步骤3: 初始化API Key...")
        api_key = db.init_default_api_key()
        print(f"✅ API Key初始化成功: {api_key}")
        print()
        
        print("=" * 60)
        print("✅ PostgreSQL数据库初始化完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

