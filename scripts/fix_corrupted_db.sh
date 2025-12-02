#!/bin/bash
# SQLite数据库修复脚本

set -e

DB_FILE="${DB_FILE:-data.db}"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "SQLite数据库修复工具"
echo "=========================================="
echo ""

# 检查数据库文件是否存在
if [ ! -f "$DB_FILE" ]; then
    echo "❌ 数据库文件不存在: $DB_FILE"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份原数据库
echo "📦 备份原数据库..."
BACKUP_FILE="$BACKUP_DIR/data.db.backup_$TIMESTAMP"
cp "$DB_FILE" "$BACKUP_FILE"
echo "✅ 备份已创建: $BACKUP_FILE"
echo ""

# 检查数据库完整性
echo "🔍 检查数据库完整性..."
if sqlite3 "$DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ 数据库完整性检查通过"
    exit 0
else
    echo "⚠️  数据库损坏，开始修复..."
    echo ""
fi

# 方法1: 尝试使用.recover恢复（SQLite 3.38+）
echo "🔧 方法1: 尝试使用.recover恢复..."
RECOVERED_FILE="$BACKUP_DIR/data.db.recovered_$TIMESTAMP.sql"
if sqlite3 "$DB_FILE" ".recover" > "$RECOVERED_FILE" 2>/dev/null && [ -s "$RECOVERED_FILE" ]; then
    echo "✅ 恢复数据已导出到: $RECOVERED_FILE"
    echo "📝 正在重建数据库..."
    
    # 创建新的数据库文件
    NEW_DB_FILE="$BACKUP_DIR/data.db.new_$TIMESTAMP"
    sqlite3 "$NEW_DB_FILE" < "$RECOVERED_FILE"
    
    if sqlite3 "$NEW_DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "✅ 数据库修复成功！"
        echo "📦 原数据库已备份到: $BACKUP_FILE"
        echo "📦 修复后的数据库: $NEW_DB_FILE"
        echo ""
        echo "⚠️  请手动检查修复后的数据库，然后替换原文件："
        echo "   mv $NEW_DB_FILE $DB_FILE"
        exit 0
    else
        echo "⚠️  修复后的数据库仍然有问题"
    fi
else
    echo "⚠️  .recover方法不可用或失败"
fi

echo ""

# 方法2: 使用.dump导出并重新导入
echo "🔧 方法2: 尝试使用.dump导出..."
DUMP_FILE="$BACKUP_DIR/data.db.dump_$TIMESTAMP.sql"
if sqlite3 "$DB_FILE" ".dump" > "$DUMP_FILE" 2>/dev/null && [ -s "$DUMP_FILE" ]; then
    echo "✅ 数据已导出到: $DUMP_FILE"
    echo "📝 正在重建数据库..."
    
    # 创建新的数据库文件
    NEW_DB_FILE="$BACKUP_DIR/data.db.new_$TIMESTAMP"
    sqlite3 "$NEW_DB_FILE" < "$DUMP_FILE"
    
    if sqlite3 "$NEW_DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "✅ 数据库修复成功！"
        echo "📦 原数据库已备份到: $BACKUP_FILE"
        echo "📦 修复后的数据库: $NEW_DB_FILE"
        echo ""
        echo "⚠️  请手动检查修复后的数据库，然后替换原文件："
        echo "   mv $NEW_DB_FILE $DB_FILE"
        exit 0
    else
        echo "⚠️  修复后的数据库仍然有问题"
    fi
else
    echo "❌ .dump方法也失败"
fi

echo ""
echo "=========================================="
echo "❌ 自动修复失败"
echo "=========================================="
echo ""
echo "建议方案："
echo "1. 切换到PostgreSQL（推荐）："
echo "   在.env文件中设置: DB_TYPE=postgresql"
echo "   然后运行: docker compose exec outlook-email-api python3 scripts/init_postgresql.py"
echo ""
echo "2. 手动修复："
echo "   检查备份文件: $BACKUP_FILE"
echo "   尝试使用SQLite工具手动修复"
echo ""
echo "3. 重建数据库（会丢失数据）："
echo "   rm $DB_FILE"
echo "   # 然后重启应用，会自动创建新数据库"
echo ""

exit 1

