#!/bin/bash

echo "=========================================="
echo "登录接口测试脚本"
echo "=========================================="

echo -e "\n[1] 测试API容器内部端点"
echo "----------------------------------------"
docker compose exec -T outlook-email-api wget -qO- http://localhost:8000/api 2>&1 | head -10

echo -e "\n[2] 测试从主机访问API"
echo "----------------------------------------"
curl -v http://localhost:8000/api 2>&1 | head -20

echo -e "\n[3] 测试登录接口（需要有效的用户名密码）"
echo "----------------------------------------"
echo "请输入用户名（默认: admin）:"
read -r USERNAME
USERNAME=${USERNAME:-admin}

echo "请输入密码:"
read -s PASSWORD

echo -e "\n发送登录请求..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo -e "\n[4] 查看实时日志（按Ctrl+C退出）"
echo "----------------------------------------"
echo "正在查看API容器日志..."
docker compose logs -f outlook-email-api

