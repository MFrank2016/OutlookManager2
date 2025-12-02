#!/bin/bash

echo "=========================================="
echo "修复端口配置并重启服务"
echo "=========================================="

echo -e "\n[1] 停止所有容器"
docker compose down

echo -e "\n[2] 重新构建并启动（应用新的端口配置）"
docker compose up -d --build

echo -e "\n[3] 等待服务启动（10秒）"
sleep 10

echo -e "\n[4] 检查容器状态"
docker compose ps

echo -e "\n[5] 测试API端点"
echo "----------------------------------------"
curl -s http://localhost:8001/api | head -5 || echo "API不可访问"

echo -e "\n[6) 查看API容器日志（最后20行）"
echo "----------------------------------------"
docker compose logs outlook-email-api --tail=20

echo -e "\n=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在应该可以通过以下地址访问："
echo "  - API: http://localhost:8001/api"
echo "  - 前端: http://localhost:3000"
echo ""
echo "测试登录："
echo "  curl -X POST http://localhost:8001/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
echo ""

