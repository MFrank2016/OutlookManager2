#!/bin/bash
# Docker 代码更新脚本

echo "=========================================="
echo "  OutlookManager2 Docker 代码更新"
echo "=========================================="
echo ""

# 1. 停止并删除旧容器
echo "📦 [1/4] 停止并删除旧容器..."
docker compose down
echo "✅ 容器已停止"
echo ""

# 2. 删除旧镜像（可选，但推荐）
echo "🗑️  [2/4] 删除旧镜像..."
docker compose rm -f
docker rmi outlook-email-client 2>/dev/null || echo "⚠️  旧镜像不存在，跳过删除"
echo "✅ 旧镜像已清理"
echo ""

# 3. 重新构建镜像（使用 --no-cache 确保使用最新代码）
echo "🔨 [3/4] 重新构建镜像（不使用缓存）..."
docker compose build --no-cache
if [ $? -ne 0 ]; then
    echo "❌ 构建失败！请检查错误信息"
    exit 1
fi
echo "✅ 镜像构建完成"
echo ""

# 4. 启动新容器
echo "🚀 [4/4] 启动新容器..."
docker compose up -d
if [ $? -ne 0 ]; then
    echo "❌ 启动失败！请检查错误信息"
    exit 1
fi
echo "✅ 容器已启动"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（10秒）..."
sleep 10
echo ""

# 检查容器状态
echo "📊 容器状态："
docker compose ps
echo ""

# 查看最新日志
echo "📋 最新日志（Ctrl+C 退出）："
echo "----------------------------------------"
docker compose logs -f --tail=50

