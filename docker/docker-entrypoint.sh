#!/bin/sh
# Docker启动脚本 - Outlook邮件管理系统

set -e

echo "=========================================="
echo "Outlook邮件管理系统启动中..."
echo "=========================================="

# 显示环境信息
echo "Python版本: $(python --version)"
echo "工作目录: $(pwd)"
echo "时区: ${TZ:-Asia/Shanghai}"

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
LOG_LEVEL=${LOG_LEVEL:-info}

# 检查必要的Python模块
echo "检查Python依赖..."
python -c "import fastapi; import uvicorn; import cachetools; print('所有依赖已安装')" || {
    echo "错误: 缺少必要的Python依赖"
    exit 1
}

echo "启动FastAPI应用..."
echo "监听地址: ${HOST}:${PORT}"
echo "日志级别: ${LOG_LEVEL}"
echo "=========================================="

# 启动应用
exec uvicorn main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL}" \
    --access-log \
    --no-use-colors

