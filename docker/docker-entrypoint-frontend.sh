#!/bin/sh
# Next.js 前端 Docker 启动脚本

# 设置环境变量
export PORT=${PORT:-3000}
export HOSTNAME=${HOSTNAME:-0.0.0.0}
export NODE_ENV=${NODE_ENV:-production}

# 查找 server.js 文件（可能在多个位置）
if [ -f "server.js" ]; then
    echo "✓ Found server.js in root directory"
    echo "Starting Next.js server on ${HOSTNAME}:${PORT}..."
    exec node server.js
elif [ -f "frontend/server.js" ]; then
    echo "✓ Found server.js in frontend directory"
    echo "Starting Next.js server on ${HOSTNAME}:${PORT}..."
    exec node frontend/server.js
else
    echo "❌ Error: server.js not found!"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Available files in /app:"
    ls -la /app | head -20
    echo ""
    if [ -d "frontend" ]; then
        echo "Available files in /app/frontend:"
        ls -la /app/frontend | head -20
    else
        echo "frontend directory does not exist"
    fi
    echo ""
    echo "Searching for server.js..."
    find /app -name "server.js" -type f 2>/dev/null || echo "No server.js found"
    exit 1
fi
