#!/bin/sh
# Docker启动脚本 - Outlook邮件管理系统

set -e

echo "=========================================="
echo "Outlook邮件管理系统启动中..."
echo "=========================================="

# 检查数据库文件
if [ ! -f "/app/data.db" ]; then
    echo "数据库文件不存在，将在首次启动时自动创建"
fi

# 运行数据库迁移（如果需要）
if [ -f "/app/migrate.py" ]; then
    echo "运行数据库迁移..."
    python migrate.py || true
fi

# 设置主机和端口（可通过环境变量覆盖）
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "启动FastAPI应用..."
echo "监听地址: ${HOST}:${PORT}"
echo "=========================================="

# 启动应用
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level info

