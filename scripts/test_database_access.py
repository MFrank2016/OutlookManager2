#!/usr/bin/env python3
"""
测试数据库访问脚本

用于验证数据库修复后是否能正常访问
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import database as db

def test_database_access():
    """测试数据库访问"""
    print("=" * 60)
    print("数据库访问测试")
    print("=" * 60)
    print()
    
    try:
        # 测试1: 获取所有表
        print("测试1: 获取所有表...")
        tables = db.get_all_tables()
        print(f"✅ 找到 {len(tables)} 个表: {', '.join(tables)}")
        print()
        
        # 测试2: 获取每个表的结构
        print("测试2: 获取表结构...")
        for table_name in tables:
            try:
                schema = db.get_table_schema(table_name)
                print(f"✅ {table_name}: {len(schema)} 列")
            except Exception as e:
                print(f"❌ {table_name}: 错误 - {e}")
        print()
        
        # 测试3: 获取每个表的数据（仅第一页）
        print("测试3: 获取表数据（第一页，每页1条）...")
        for table_name in tables:
            try:
                data, total = db.get_table_data(table_name, page=1, page_size=1)
                print(f"✅ {table_name}: 总数 {total}, 已获取 {len(data)} 条")
            except Exception as e:
                print(f"❌ {table_name}: 错误 - {e}")
        print()
        
        print("=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_database_access()
    sys.exit(0 if success else 1)

