#!/usr/bin/env python3
"""
PostgreSQL连接验证脚本

用于验证PostgreSQL数据库连接是否正常
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DB_TYPE, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_postgresql_connection():
    """验证PostgreSQL连接"""
    if DB_TYPE != "postgresql":
        print(f"当前数据库类型为 {DB_TYPE}，不是 PostgreSQL")
        return False
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        print("=" * 60)
        print("PostgreSQL连接验证")
        print("=" * 60)
        print()
        print(f"连接信息:")
        print(f"  主机: {DB_HOST}")
        print(f"  端口: {DB_PORT}")
        print(f"  数据库: {DB_NAME}")
        print(f"  用户: {DB_USER}")
        print()
        
        # 尝试连接
        print("正在连接PostgreSQL...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )
        
        print("✅ 连接成功！")
        print()
        
        # 获取PostgreSQL版本
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL版本: {version}")
        print()
        
        # 检查数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(%s));", (DB_NAME,))
        size = cursor.fetchone()[0]
        print(f"数据库大小: {size}")
        print()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  数据库中没有表，需要运行初始化脚本")
            print("   运行: python3 scripts/init_postgresql.py")
        
        print()
        
        # 检查连接数
        cursor.execute("SELECT count(*) FROM pg_stat_activity;")
        connections = cursor.fetchone()[0]
        print(f"当前连接数: {connections}")
        
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ PostgreSQL连接验证完成")
        print("=" * 60)
        
        return True
        
    except ImportError:
        print("❌ psycopg2-binary 未安装")
        print("   安装: pip install psycopg2-binary")
        return False
    except psycopg2.OperationalError as e:
        print(f"❌ 连接失败: {e}")
        print()
        print("排查步骤:")
        print("1. 检查PostgreSQL容器是否运行: docker compose ps postgresql")
        print("2. 检查环境变量配置: cat .env | grep DB_")
        print("3. 检查PostgreSQL日志: docker compose logs postgresql")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_postgresql_connection()
    sys.exit(0 if success else 1)

