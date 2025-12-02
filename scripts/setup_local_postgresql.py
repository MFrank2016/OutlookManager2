#!/usr/bin/env python3
"""
本地开发环境配置脚本
用于快速配置本地 Python 环境连接远程 PostgreSQL
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """创建 .env 文件"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if env_file.exists():
        print("⚠️  .env 文件已存在")
        response = input("是否覆盖现有文件？(y/N): ").strip().lower()
        if response != 'y':
            print("已取消操作")
            return False
    
    # 读取示例文件
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # 如果示例文件不存在，使用默认模板
        content = """# Outlook邮件API服务 - 环境变量配置
# 本地开发连接远程PostgreSQL配置

# 应用配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
TZ=Asia/Shanghai

# 数据库配置
DB_TYPE=postgresql
DB_HOST=192.168.1.100
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_password_here

# 连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30
"""
    
    # 交互式配置
    print("\n" + "="*50)
    print("配置本地开发环境 - 连接远程PostgreSQL")
    print("="*50 + "\n")
    
    # 数据库主机
    db_host = input(f"PostgreSQL 服务器IP地址 [默认: 192.168.1.100]: ").strip()
    if not db_host:
        db_host = "192.168.1.100"
    
    # 数据库端口
    db_port = input(f"PostgreSQL 端口 [默认: 5432]: ").strip()
    if not db_port:
        db_port = "5432"
    
    # 数据库名
    db_name = input(f"数据库名 [默认: outlook_manager]: ").strip()
    if not db_name:
        db_name = "outlook_manager"
    
    # 数据库用户
    db_user = input(f"数据库用户名 [默认: outlook_user]: ").strip()
    if not db_user:
        db_user = "outlook_user"
    
    # 数据库密码
    db_password = input(f"数据库密码 [必填]: ").strip()
    if not db_password:
        print("❌ 密码不能为空")
        return False
    
    # 替换配置
    content = content.replace('DB_HOST=192.168.1.100', f'DB_HOST={db_host}')
    content = content.replace('DB_PORT=5432', f'DB_PORT={db_port}')
    content = content.replace('DB_NAME=outlook_manager', f'DB_NAME={db_name}')
    content = content.replace('DB_USER=outlook_user', f'DB_USER={db_user}')
    content = content.replace('DB_PASSWORD=your_password_here', f'DB_PASSWORD={db_password}')
    
    # 写入文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ .env 文件已创建: {env_file.absolute()}")
    return True

def test_connection():
    """测试数据库连接"""
    print("\n" + "="*50)
    print("测试数据库连接...")
    print("="*50 + "\n")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            connect_timeout=30  # 增加超时时间到30秒，适应远程连接
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"✅ 数据库连接成功！")
        print(f"PostgreSQL 版本: {version}")
        
        # 检查数据库是否已初始化
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 数据库已包含 {len(tables)} 个表:")
            for table in tables[:10]:  # 只显示前10个
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... 还有 {len(tables) - 10} 个表")
        else:
            print("\n⚠️  数据库为空，需要初始化表结构")
            print("   运行: python main.py (会自动初始化)")
        
        conn.close()
        return True
        
    except ImportError:
        print("❌ 缺少依赖: psycopg2-binary")
        print("   请运行: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. 网络连接是否正常")
        print("  2. PostgreSQL 服务是否运行")
        print("  3. 防火墙是否允许访问")
        print("  4. 用户名和密码是否正确")
        return False

def main():
    """主函数"""
    print("="*50)
    print("本地开发环境配置工具")
    print("="*50)
    
    # 检查依赖
    try:
        import psycopg2
    except ImportError:
        print("\n⚠️  缺少依赖: psycopg2-binary")
        print("正在检查 requirements.txt...")
        if 'psycopg2-binary' in Path('requirements.txt').read_text():
            print("请运行: pip install -r requirements.txt")
        else:
            print("请运行: pip install psycopg2-binary")
        sys.exit(1)
    
    # 创建 .env 文件
    # if not create_env_file():
    #     sys.exit(1)
    
    # 测试连接
    test_connection()
    
    print("\n" + "="*50)
    print("配置完成！")
    print("="*50)
    print("\n下一步:")
    print("  1. 启动服务: python main.py")
    print("  2. 访问 API: http://localhost:8000")
    print("  3. 查看文档: http://localhost:8000/docs")
    print()

if __name__ == '__main__':
    main()

