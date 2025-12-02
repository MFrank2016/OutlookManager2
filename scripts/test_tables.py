#!/usr/bin/env python3
"""
测试 PostgreSQL 表是否已创建
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        connect_timeout=10
    )
    
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    
    print(f"✅ 数据库连接成功")
    print(f"\n📊 已创建的表 ({len(tables)} 个):")
    
    required_tables = ['accounts', 'users', 'system_config', 'emails_cache', 'email_details_cache']
    
    for table in tables:
        table_name = table[0]
        status = "✅" if table_name in required_tables else "ℹ️"
        print(f"  {status} {table_name}")
    
    print(f"\n必需的表检查:")
    for table_name in required_tables:
        exists = any(t[0] == table_name for t in tables)
        status = "✅" if exists else "❌"
        print(f"  {status} {table_name}")
    
    if len(tables) == 0:
        print("\n⚠️  数据库为空，需要初始化表结构")
        print("   运行: python main.py (会自动初始化)")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)

