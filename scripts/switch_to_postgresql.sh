#!/bin/bash
# 快速切换到PostgreSQL脚本

set -e

ENV_FILE="${ENV_FILE:-.env}"

echo "=========================================="
echo "切换到PostgreSQL数据库"
echo "=========================================="
echo ""

# 检查.env文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env文件不存在，将创建新文件"
    touch "$ENV_FILE"
fi

# 备份原.env文件
if [ -f "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
    BACKUP_ENV="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$ENV_FILE" "$BACKUP_ENV"
    echo "✅ 已备份.env文件到: $BACKUP_ENV"
    echo ""
fi

# 检查PostgreSQL是否运行
echo "🔍 检查PostgreSQL服务状态..."
if docker compose ps postgresql 2>/dev/null | grep -q "Up"; then
    echo "✅ PostgreSQL服务正在运行"
else
    echo "⚠️  PostgreSQL服务未运行，正在启动..."
    docker compose up -d postgresql
    echo "⏳ 等待PostgreSQL就绪（30秒）..."
    sleep 30
fi
echo ""

# 读取或设置PostgreSQL配置
if grep -q "POSTGRES_PASSWORD" "$ENV_FILE" 2>/dev/null; then
    POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
    echo "请输入PostgreSQL密码（留空使用默认值 'changeme'）:"
    read -s POSTGRES_PASSWORD
    if [ -z "$POSTGRES_PASSWORD" ]; then
        POSTGRES_PASSWORD="changeme"
        echo "使用默认密码: changeme"
    fi
    echo ""
fi

# 生成新的配置
echo "📝 更新.env文件..."

# 移除旧的数据库配置（如果存在）
sed -i.bak '/^DB_TYPE=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^DB_HOST=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^DB_PORT=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^DB_NAME=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^DB_USER=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^DB_PASSWORD=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^POSTGRES_DB=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^POSTGRES_USER=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^POSTGRES_PASSWORD=/d' "$ENV_FILE" 2>/dev/null || true
sed -i.bak '/^POSTGRES_PORT=/d' "$ENV_FILE" 2>/dev/null || true

# 添加PostgreSQL配置
cat >> "$ENV_FILE" << EOF

# PostgreSQL数据库配置（自动生成于 $(date +%Y-%m-%d\ %H:%M:%S)）
DB_TYPE=postgresql
DB_HOST=postgresql
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=$POSTGRES_PASSWORD

# PostgreSQL服务配置
POSTGRES_DB=outlook_manager
POSTGRES_USER=outlook_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_PORT=5432
EOF

echo "✅ .env文件已更新"
echo ""

# 初始化PostgreSQL数据库
echo "🔧 初始化PostgreSQL数据库..."
if docker compose exec -T outlook-email-api python3 scripts/init_postgresql.py 2>/dev/null; then
    echo "✅ PostgreSQL数据库初始化成功"
else
    echo "⚠️  应用容器可能未运行，将在启动后自动初始化"
    echo "   或者手动运行: docker compose exec outlook-email-api python3 scripts/init_postgresql.py"
fi
echo ""

# 提示重启应用
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 重启应用服务："
echo "   docker compose restart outlook-email-api"
echo ""
echo "2. 查看应用日志，确认连接成功："
echo "   docker compose logs -f outlook-email-api"
echo ""
echo "3. 验证数据库连接："
echo "   docker compose exec outlook-email-api python3 scripts/verify_postgresql.py"
echo ""
echo "⚠️  注意：SQLite数据库文件(data.db)已不再使用，但不会被删除"
echo "   如需备份，请手动备份: cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)"
echo ""

