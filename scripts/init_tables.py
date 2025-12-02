#!/usr/bin/env python3
"""
手动初始化 PostgreSQL 表结构
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def init_tables():
    """初始化数据库表"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            connect_timeout=30
        )
        
        cursor = conn.cursor()
        
        # 读取 schema 文件
        schema_file = Path(__file__).parent.parent / "database" / "postgresql_schema.sql"
        indexes_file = Path(__file__).parent.parent / "database" / "postgresql_indexes.sql"
        
        if not schema_file.exists():
            print(f"❌ Schema 文件不存在: {schema_file}")
            return False
        
        print(f"📄 读取 schema 文件: {schema_file}")
        
        # 执行 schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            # 按分号分割，但保留多行语句
            statements = []
            current_statement = []
            
            for line in schema_sql.split('\n'):
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('--'):
                    continue
                current_statement.append(line)
                # 如果行以分号结尾，说明是一个完整的语句
                if line.endswith(';'):
                    statement = ' '.join(current_statement)
                    if statement and statement != ';':
                        statements.append(statement.rstrip(';'))
                    current_statement = []
            
            # 处理最后一个语句（如果没有以分号结尾）
            if current_statement:
                statement = ' '.join(current_statement)
                if statement:
                    statements.append(statement)
            
            print(f"📝 执行 {len(statements)} 个 SQL 语句...")
            
            for i, statement in enumerate(statements, 1):
                try:
                    cursor.execute(statement)
                    # 获取表名（如果可能）
                    table_name = "未知"
                    if "CREATE TABLE" in statement.upper():
                        import re
                        match = re.search(r'CREATE TABLE.*?(\w+)', statement, re.IGNORECASE)
                        if match:
                            table_name = match.group(1)
                    print(f"  ✅ [{i}/{len(statements)}] {table_name} - 执行成功")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already exists" in error_msg:
                        print(f"  ⚠️  [{i}/{len(statements)}] 已存在，跳过")
                    else:
                        print(f"  ❌ [{i}/{len(statements)}] 执行失败: {e}")
                        print(f"     SQL: {statement[:150]}...")
                        # 回滚当前事务，继续下一个
                        conn.rollback()
                        continue
        
        # 执行索引
        if indexes_file.exists():
            print(f"\n📄 读取索引文件: {indexes_file}")
            with open(indexes_file, 'r', encoding='utf-8') as f:
                indexes_sql = f.read()
                statements = [s.strip() for s in indexes_sql.split(';') if s.strip() and not s.strip().startswith('--') and not s.strip().startswith('=')]
                
                print(f"📝 执行 {len(statements)} 个索引语句...")
                
                for i, statement in enumerate(statements, 1):
                    try:
                        cursor.execute(statement)
                        print(f"  ✅ [{i}/{len(statements)}] 索引创建成功")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "already exists" in error_msg:
                            print(f"  ⚠️  [{i}/{len(statements)}] 索引已存在，跳过")
                        else:
                            print(f"  ❌ [{i}/{len(statements)}] 索引创建失败: {e}")
        
        conn.commit()
        print("\n✅ 数据库表初始化完成！")
        
        # 验证表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\n📊 已创建的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("  PostgreSQL 数据库表初始化")
    print("="*60)
    print()
    
    if init_tables():
        print("\n✅ 初始化成功！")
        sys.exit(0)
    else:
        print("\n❌ 初始化失败！")
        sys.exit(1)

