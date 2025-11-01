#!/usr/bin/env python3
"""
数据表管理功能测试脚本
测试新增的 emails_cache 和 email_details_cache 表管理
"""

import database as db

def test_table_management():
    """测试数据表管理功能"""
    print("=" * 60)
    print("数据表管理功能测试")
    print("=" * 60)
    
    # 初始化数据库
    print("\n1. 初始化数据库...")
    db.init_database()
    print("✅ 数据库初始化成功")
    
    # 获取所有表
    print("\n2. 获取所有数据表...")
    tables = db.get_all_tables()
    print(f"✅ 找到 {len(tables)} 个表")
    
    # 显示表详情
    print("\n3. 表详情统计:")
    print("-" * 60)
    print(f"{'序号':<6} {'表名':<25} {'记录数':<10} {'状态'}")
    print("-" * 60)
    
    expected_tables = [
        'accounts',
        'admins', 
        'system_config',
        'emails_cache',
        'email_details_cache'
    ]
    
    for i, table_name in enumerate(expected_tables, 1):
        if table_name in tables:
            _, count = db.get_table_data(table_name, page=1, page_size=1)
            status = "✅ 已管理"
        else:
            count = 0
            status = "❌ 未找到"
        
        print(f"{i:<6} {table_name:<25} {count:<10} {status}")
    
    print("-" * 60)
    
    # 验证新增的表
    print("\n4. 验证新增的缓存表...")
    new_tables = ['emails_cache', 'email_details_cache']
    
    for table_name in new_tables:
        if table_name in tables:
            # 获取表结构
            schema = db.get_table_schema(table_name)
            print(f"\n✅ {table_name} 表结构:")
            print(f"   - 字段数: {len(schema)}")
            print(f"   - 主要字段: {', '.join([col['name'] for col in schema[:5]])}")
            
            # 获取记录数
            _, count = db.get_table_data(table_name, page=1, page_size=1)
            print(f"   - 记录数: {count}")
            
            # 获取示例数据
            if count > 0:
                data, _ = db.get_table_data(table_name, page=1, page_size=1)
                if data:
                    print(f"   - 示例记录: {list(data[0].keys())[:5]}")
        else:
            print(f"❌ {table_name} 表不存在")
    
    # 测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_found = all(table in tables for table in expected_tables)
    
    if all_found:
        print("✅ 所有预期的表都已找到并可管理")
        print(f"✅ 表总数: {len(tables)}")
        print(f"✅ 管理的表: {', '.join(expected_tables)}")
        
        # 计算总记录数
        total_records = 0
        for table_name in expected_tables:
            _, count = db.get_table_data(table_name, page=1, page_size=1)
            total_records += count
        print(f"✅ 总记录数: {total_records}")
        
        print("\n🎉 数据表管理功能测试通过！")
        return True
    else:
        missing = [t for t in expected_tables if t not in tables]
        print(f"❌ 缺少以下表: {', '.join(missing)}")
        print("\n❌ 测试失败！")
        return False

if __name__ == "__main__":
    success = test_table_management()
    exit(0 if success else 1)
