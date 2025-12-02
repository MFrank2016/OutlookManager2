#!/usr/bin/env python3
"""
数据库连接诊断工具
用于诊断虚拟环境和非虚拟环境的连接差异
"""

import sys
import os
from pathlib import Path

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_environment():
    """检查环境信息"""
    print_section("环境信息")
    print(f"Python 可执行文件: {sys.executable}")
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.path[:3]}...")  # 只显示前3个
    print(f"工作目录: {os.getcwd()}")
    print(f"是否在虚拟环境: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")

def check_dependencies():
    """检查依赖"""
    print_section("依赖检查")
    
    try:
        import psycopg2
        print(f"✅ psycopg2 版本: {psycopg2.__version__}")
        print(f"   psycopg2 路径: {psycopg2.__file__}")
    except ImportError as e:
        print(f"❌ psycopg2 未安装: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print(f"✅ python-dotenv 已安装")
        print(f"   dotenv 路径: {load_dotenv.__module__}")
    except ImportError as e:
        print(f"❌ python-dotenv 未安装: {e}")
        return False
    
    return True

def check_env_file():
    """检查环境变量文件"""
    print_section("环境变量文件")
    
    env_file = Path('.env')
    if env_file.exists():
        print(f"✅ .env 文件存在: {env_file.absolute()}")
        
        # 读取配置（不显示密码）
        from dotenv import load_dotenv
        load_dotenv()
        
        print(f"\n数据库配置:")
        print(f"  DB_TYPE: {os.getenv('DB_TYPE', '未设置')}")
        print(f"  DB_HOST: {os.getenv('DB_HOST', '未设置')}")
        print(f"  DB_PORT: {os.getenv('DB_PORT', '未设置')}")
        print(f"  DB_NAME: {os.getenv('DB_NAME', '未设置')}")
        print(f"  DB_USER: {os.getenv('DB_USER', '未设置')}")
        print(f"  DB_PASSWORD: {'已设置' if os.getenv('DB_PASSWORD') else '未设置'}")
        print(f"  DB_POOL_TIMEOUT: {os.getenv('DB_POOL_TIMEOUT', '未设置')}")
        
        return True
    else:
        print(f"❌ .env 文件不存在")
        return False

def test_network():
    """测试网络连接"""
    print_section("网络连接测试")
    
    import socket
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv('DB_HOST')
    port = int(os.getenv('DB_PORT', 5432))
    
    if not host:
        print("❌ DB_HOST 未设置")
        return False
    
    print(f"测试连接到 {host}:{port}...")
    
    try:
        # 测试 TCP 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP 连接成功")
            return True
        else:
            print(f"❌ TCP 连接失败 (错误码: {result})")
            return False
    except Exception as e:
        print(f"❌ 网络测试失败: {e}")
        return False

def test_database_connection(timeout=30):
    """测试数据库连接"""
    print_section(f"数据库连接测试 (超时: {timeout}秒)")
    
    from dotenv import load_dotenv
    import psycopg2
    import time
    
    load_dotenv()
    
    host = os.getenv('DB_HOST')
    port = int(os.getenv('DB_PORT', 5432))
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    if not all([host, database, user, password]):
        print("❌ 数据库配置不完整")
        return False
    
    print(f"连接参数:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {database}")
    print(f"  用户: {user}")
    print(f"  超时: {timeout}秒")
    print(f"\n正在连接...")
    
    start_time = time.time()
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=timeout
        )
        
        elapsed = time.time() - start_time
        print(f"✅ 数据库连接成功！(耗时: {elapsed:.2f}秒)")
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL 版本: {version[:50]}...")
        
        # 检查表
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ 数据库表数量: {table_count}")
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        
        if "timeout" in error_msg.lower():
            print(f"❌ 连接超时 (耗时: {elapsed:.2f}秒)")
            print(f"   错误: {error_msg}")
            print(f"\n建议:")
            print(f"   1. 检查网络连接")
            print(f"   2. 检查防火墙设置")
            print(f"   3. 增加超时时间 (当前: {timeout}秒)")
        elif "password" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"❌ 认证失败 (耗时: {elapsed:.2f}秒)")
            print(f"   错误: {error_msg}")
            print(f"\n建议:")
            print(f"   1. 检查 .env 文件中的 DB_PASSWORD")
            print(f"   2. 确认 PostgreSQL 用户密码是否正确")
        else:
            print(f"❌ 连接失败 (耗时: {elapsed:.2f}秒)")
            print(f"   错误: {error_msg}")
        
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 未知错误 (耗时: {elapsed:.2f}秒)")
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("  数据库连接诊断工具")
    print("="*60)
    
    # 检查环境
    check_environment()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装依赖")
        sys.exit(1)
    
    # 检查环境变量文件
    if not check_env_file():
        print("\n❌ 环境变量文件检查失败")
        sys.exit(1)
    
    # 测试网络
    if not test_network():
        print("\n❌ 网络连接测试失败")
        sys.exit(1)
    
    # 测试数据库连接（短超时）
    print("\n" + "="*60)
    print("  第一次连接测试 (超时: 10秒)")
    print("="*60)
    success_short = test_database_connection(timeout=10)
    
    if not success_short:
        # 如果短超时失败，尝试长超时
        print("\n" + "="*60)
        print("  第二次连接测试 (超时: 30秒)")
        print("="*60)
        success_long = test_database_connection(timeout=30)
        
        if success_long:
            print("\n✅ 使用较长超时时间连接成功")
            print("   建议: 在 .env 文件中设置 DB_POOL_TIMEOUT=30")
        else:
            print("\n❌ 即使使用较长超时时间也连接失败")
            sys.exit(1)
    else:
        print("\n✅ 连接测试成功！")
    
    print("\n" + "="*60)
    print("  诊断完成")
    print("="*60)

if __name__ == '__main__':
    main()

