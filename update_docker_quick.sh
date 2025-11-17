#!/bin/bash
# Docker 快速更新脚本（使用缓存加速构建）

echo "=========================================="
echo "  OutlookManager2 Docker 快速更新"
echo "=========================================="
echo ""

# 停止旧容器
echo "📦 停止旧容器..."
docker compose down

# 重新构建（使用缓存）
echo "🔨 重新构建镜像..."
docker compose build

# 启动新容器
echo "🚀 启动新容器..."
docker compose up -d

# 查看状态
echo ""
echo "✅ 更新完成！"
echo ""
echo "📊 容器状态："
docker compose ps

echo ""
echo "📋 查看日志："
echo "  docker compose logs -f"
echo ""
echo "🔍 验证修复："
echo "  浏览器访问并测试批量刷新Token功能"

