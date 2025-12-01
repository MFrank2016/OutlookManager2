#!/usr/bin/env python3
"""
数据库修复脚本

用于修复SQLite数据库损坏问题
支持：
1. 检查数据库完整性
2. 尝试修复数据库
3. 备份和恢复数据
"""

import sqlite3
import shutil
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_FILE = project_root / "data.db"
BACKUP_DIR = project_root / "backups"

def ensure_backup_dir():
    """确保备份目录存在"""
    BACKUP_DIR.mkdir(exist_ok=True)

def backup_database():
    """备份数据库文件"""
    if not DB_FILE.exists():
        print(f"❌ 数据库文件不存在: {DB_FILE}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"data.db.backup_{timestamp}"
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        print(f"✅ 数据库已备份到: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def check_integrity():
    """检查数据库完整性"""
    if not DB_FILE.exists():
        print(f"❌ 数据库文件不存在: {DB_FILE}")
        return False
    
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        
        # 执行完整性检查
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0] == "ok":
            print("✅ 数据库完整性检查通过")
            return True
        else:
            print(f"❌ 数据库完整性检查失败: {result}")
            return False
    except sqlite3.DatabaseError as e:
        print(f"❌ 数据库损坏: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def repair_database():
    """尝试修复数据库"""
    if not DB_FILE.exists():
        print(f"❌ 数据库文件不存在: {DB_FILE}")
        return False
    
    print("🔧 开始修复数据库...")
    
    # 备份原数据库
    backup_file = backup_database()
    if not backup_file:
        print("❌ 无法创建备份，停止修复")
        return False
    
    try:
        # 方法1: 使用 .recover 命令（SQLite 3.38+）
        print("尝试方法1: 使用 .recover 恢复...")
        recovered_file = BACKUP_DIR / f"data.db.recovered_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 使用 sqlite3 命令行工具进行恢复
        import subprocess
        result = subprocess.run(
            ["sqlite3", str(DB_FILE), ".recover"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0 and result.stdout:
            # 将恢复的数据写入新文件
            with open(recovered_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            print(f"✅ 恢复数据已导出到: {recovered_file}")
            print("⚠️  需要手动导入恢复的数据")
            return True
        else:
            print("⚠️  .recover 方法不可用或失败，尝试方法2...")
    
    except FileNotFoundError:
        print("⚠️  sqlite3 命令行工具未找到，尝试方法2...")
    except subprocess.TimeoutExpired:
        print("⚠️  恢复操作超时，尝试方法2...")
    except Exception as e:
        print(f"⚠️  方法1失败: {e}，尝试方法2...")
    
    # 方法2: 使用 .dump 导出并重新导入
    try:
        print("尝试方法2: 使用 .dump 导出数据...")
        dump_file = BACKUP_DIR / f"data.db.dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        import subprocess
        result = subprocess.run(
            ["sqlite3", str(DB_FILE), ".dump"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            print(f"✅ 数据已导出到: {dump_file}")
            print("⚠️  需要手动导入导出的数据")
            return True
        else:
            print(f"❌ 导出失败: {result.stderr}")
            return False
    
    except FileNotFoundError:
        print("❌ sqlite3 命令行工具未找到，无法使用 .dump 方法")
        return False
    except subprocess.TimeoutExpired:
        print("❌ 导出操作超时")
        return False
    except Exception as e:
        print(f"❌ 方法2失败: {e}")
        return False

def rebuild_database():
    """重建数据库结构（会丢失数据）"""
    print("⚠️  警告: 重建数据库将删除所有数据！")
    response = input("是否继续？(yes/no): ")
    
    if response.lower() != "yes":
        print("❌ 已取消重建")
        return False
    
    # 备份原数据库
    backup_file = backup_database()
    if not backup_file:
        print("❌ 无法创建备份，停止重建")
        return False
    
    try:
        # 删除原数据库
        DB_FILE.unlink()
        print("✅ 已删除损坏的数据库文件")
        
        # 重新初始化数据库
        print("🔧 重新初始化数据库...")
        import database as db
        db.init_database()
        print("✅ 数据库已重新初始化")
        
        print("⚠️  注意: 所有数据已丢失，需要重新导入账户和配置")
        return True
    
    except Exception as e:
        print(f"❌ 重建失败: {e}")
        # 尝试恢复备份
        if backup_file and backup_file.exists():
            print("尝试恢复备份...")
            try:
                shutil.copy2(backup_file, DB_FILE)
                print("✅ 已恢复备份")
            except Exception as restore_error:
                print(f"❌ 恢复备份失败: {restore_error}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("数据库修复工具")
    print("=" * 60)
    print()
    
    ensure_backup_dir()
    
    # 检查数据库文件是否存在
    if not DB_FILE.exists():
        print(f"❌ 数据库文件不存在: {DB_FILE}")
        print("💡 提示: 数据库文件可能在其他位置，或需要先初始化")
        return
    
    print(f"📁 数据库文件: {DB_FILE}")
    print(f"📊 文件大小: {DB_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # 步骤1: 检查完整性
    print("步骤1: 检查数据库完整性...")
    is_ok = check_integrity()
    print()
    
    if is_ok:
        print("✅ 数据库正常，无需修复")
        return
    
    # 步骤2: 尝试修复
    print("步骤2: 尝试修复数据库...")
    repair_success = repair_database()
    print()
    
    if repair_success:
        print("✅ 修复数据已导出，请检查备份目录")
        print("💡 提示: 可以尝试手动导入恢复的数据")
        return
    
    # 步骤3: 重建数据库（最后手段）
    print("步骤3: 所有修复方法都失败了")
    print("⚠️  可以选择重建数据库（会丢失所有数据）")
    print()
    
    rebuild_database()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

