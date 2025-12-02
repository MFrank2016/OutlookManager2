#!/bin/bash

echo "=========================================="
echo "登录接口测试"
echo "=========================================="

echo -e "\n[1] 测试API健康检查"
echo "----------------------------------------"
curl -s http://localhost:8000/api | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api

echo -e "\n[2] 测试登录接口"
echo "----------------------------------------"
echo "请输入用户名（默认: admin）:"
read -r USERNAME
USERNAME=${USERNAME:-admin}

echo "请输入密码（默认: admin123）:"
read -r PASSWORD
PASSWORD=${PASSWORD:-admin123}

echo -e "\n发送登录请求到 http://localhost:8000/auth/login ..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo ""
echo "HTTP状态码: $HTTP_CODE"
echo "响应内容:"
if [ "$HTTP_CODE" = "200" ]; then
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "✓ 登录成功！"
else
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "✗ 登录失败"
fi

echo -e "\n[3] 查看API容器日志（最后20行）"
echo "----------------------------------------"
docker compose logs outlook-email-api --tail=20

