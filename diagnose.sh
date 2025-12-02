#!/bin/bash

echo "=========================================="
echo "Outlook Manager 诊断脚本"
echo "=========================================="

echo -e "\n[1] 检查容器状态"
echo "----------------------------------------"
docker compose ps

echo -e "\n[2] 检查API容器日志（最后30行）"
echo "----------------------------------------"
docker compose logs outlook-email-api --tail=30 2>&1

echo -e "\n[3] 检查API容器是否正在运行"
echo "----------------------------------------"
if docker compose ps | grep -q "outlook-email-api.*Up"; then
    echo "✓ API容器正在运行"
else
    echo "✗ API容器未运行或已停止"
    echo "查看完整日志："
    docker compose logs outlook-email-api --tail=100
fi

echo -e "\n[4] 测试API端点可访问性"
echo "----------------------------------------"
if docker compose exec -T outlook-email-api wget -qO- http://localhost:8000/api 2>&1 | head -5; then
    echo "✓ API端点可访问"
else
    echo "✗ API端点不可访问"
fi

echo -e "\n[5] 检查环境变量"
echo "----------------------------------------"
docker compose exec -T outlook-email-api env | grep -E "DB_|PYTHON|LOG" | sort

echo -e "\n[6] 检查数据库文件"
echo "----------------------------------------"
if [ -f "data.db" ]; then
    echo "✓ data.db 存在"
    ls -lh data.db
else
    echo "✗ data.db 不存在"
fi

echo -e "\n[7] 检查日志目录"
echo "----------------------------------------"
if [ -d "logs" ]; then
    echo "✓ logs 目录存在"
    ls -lh logs/ | head -5
    echo "最新的日志文件："
    ls -t logs/*.log 2>/dev/null | head -1 | xargs tail -20 2>/dev/null || echo "无日志文件"
else
    echo "✗ logs 目录不存在"
fi

echo -e "\n[8] 测试登录接口（需要有效的用户名密码）"
echo "----------------------------------------"
echo "请在服务器上手动运行："
echo "curl -X POST http://localhost:8001/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"admin\",\"password\":\"your_password\"}'"

echo -e "\n[9] 检查网络连接"
echo "----------------------------------------"
docker network inspect outlook-network 2>/dev/null | grep -A 5 "Containers" || echo "网络检查失败"

echo -e "\n[10] 检查端口占用"
echo "----------------------------------------"
netstat -tuln 2>/dev/null | grep -E ":(8001|3000|5432)" || ss -tuln 2>/dev/null | grep -E ":(8001|3000|5432)" || echo "无法检查端口（需要root权限）"

echo -e "\n=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果API容器未运行，请查看完整日志："
echo "  docker compose logs outlook-email-api"
echo ""
echo "如果容器运行但无法访问，请检查："
echo "  1. 端口是否正确映射"
echo "  2. 防火墙设置"
echo "  3. 反向代理配置（如果使用）"
echo ""

