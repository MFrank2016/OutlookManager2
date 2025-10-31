"""
数据迁移脚本

将accounts.json数据迁移到SQLite数据库
并初始化系统配置和默认管理员
"""

import json
import sys
from pathlib import Path

import auth
import database as db


def migrate_accounts_from_json(json_file: str = "accounts.json") -> int:
    """
    从JSON文件迁移账户数据到SQLite
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        迁移的账户数量
    """
    json_path = Path(json_file)
    
    if not json_path.exists():
        print(f"未找到 {json_file}，跳过账户迁移")
        return 0
    
    print(f"正在从 {json_file} 迁移账户数据...")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
        
        migrated_count = 0
        skipped_count = 0
        
        for email, account_info in accounts_data.items():
            # 检查账户是否已存在
            existing = db.get_account_by_email(email)
            
            if existing:
                print(f"  - 账户 {email} 已存在，跳过")
                skipped_count += 1
                continue
            
            # 创建账户
            try:
                db.create_account(
                    email=email,
                    refresh_token=account_info.get('refresh_token', ''),
                    client_id=account_info.get('client_id', ''),
                    tags=account_info.get('tags', [])
                )
                
                # 更新额外字段
                update_fields = {}
                if account_info.get('last_refresh_time'):
                    update_fields['last_refresh_time'] = account_info['last_refresh_time']
                if account_info.get('next_refresh_time'):
                    update_fields['next_refresh_time'] = account_info['next_refresh_time']
                if account_info.get('refresh_status'):
                    update_fields['refresh_status'] = account_info['refresh_status']
                if account_info.get('refresh_error'):
                    update_fields['refresh_error'] = account_info['refresh_error']
                
                if update_fields:
                    db.update_account(email, **update_fields)
                
                print(f"  ✓ 成功迁移账户: {email}")
                migrated_count += 1
                
            except Exception as e:
                print(f"  ✗ 迁移账户 {email} 失败: {e}")
        
        print(f"\n账户迁移完成:")
        print(f"  成功迁移: {migrated_count} 个")
        print(f"  跳过: {skipped_count} 个")
        
        return migrated_count
    
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析 {json_file}: {e}")
        return 0
    except Exception as e:
        print(f"错误: 迁移过程中出现异常: {e}")
        return 0


def init_system_configs() -> None:
    """
    初始化系统配置
    """
    print("\n正在初始化系统配置...")
    
    default_configs = [
        ("IMAP_SERVER", "outlook.office365.com", "IMAP服务器地址"),
        ("IMAP_PORT", "993", "IMAP服务器端口"),
        ("MAX_CONNECTIONS", "5", "每个邮箱的最大IMAP连接数"),
        ("CONNECTION_TIMEOUT", "30", "连接超时时间（秒）"),
        ("SOCKET_TIMEOUT", "15", "Socket超时时间（秒）"),
        ("CACHE_EXPIRE_TIME", "60", "缓存过期时间（秒）"),
        ("TOKEN_REFRESH_INTERVAL", "3", "Token刷新间隔（天）"),
        ("LOG_RETENTION_DAYS", "30", "日志保留天数"),
    ]
    
    for key, value, description in default_configs:
        # 检查配置是否已存在
        existing = db.get_config(key)
        
        if existing:
            print(f"  - 配置 {key} 已存在，跳过")
            continue
        
        db.set_config(key, value, description)
        print(f"  ✓ 已设置配置: {key} = {value}")
    
    print("系统配置初始化完成")


def main():
    """
    主迁移流程
    """
    print("=" * 60)
    print("Outlook邮件管理系统 - 数据迁移工具")
    print("=" * 60)
    print()
    
    # 1. 初始化数据库
    print("步骤 1: 初始化数据库表结构...")
    db.init_database()
    print("✓ 数据库初始化完成\n")
    
    # 2. 迁移账户数据
    print("步骤 2: 迁移账户数据...")
    migrated_count = migrate_accounts_from_json()
    
    # 3. 初始化系统配置
    print("\n步骤 3: 初始化系统配置...")
    init_system_configs()
    
    # 4. 创建默认管理员
    print("\n步骤 4: 创建默认管理员...")
    auth.init_default_admin()
    
    print("\n" + "=" * 60)
    print("数据迁移完成！")
    print("=" * 60)
    print()
    print("重要提示:")
    print("  1. 默认管理员用户名: admin")
    print("  2. 默认管理员密码: admin123")
    print("  3. 请首次登录后立即修改密码！")
    print("  4. 数据库文件: data.db")
    print()
    
    # 提示是否备份旧文件
    if Path("accounts.json").exists():
        print("建议:")
        print("  - 迁移成功后，可以备份或删除 accounts.json 文件")
        print("  - 备份命令: cp accounts.json accounts.json.backup")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n迁移已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误: {e}")
        sys.exit(1)

