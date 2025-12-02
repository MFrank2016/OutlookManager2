#!/bin/bash

echo "=========================================="
echo "前端容器网络连接测试"
echo "=========================================="

echo -e "\n[1] 检查前端容器网络配置"
echo "----------------------------------------"
docker inspect outlook-email-frontend | grep -A 10 "Networks" || echo "容器未运行"

echo -e "\n[2] 测试前端容器访问后端API"
echo "----------------------------------------"
docker compose exec outlook-email-frontend wget -qO- http://outlook-email-api:8000/api 2>&1 | head -10

echo -e "\n[3] 测试前端容器访问登录接口"
echo "----------------------------------------"
docker compose exec outlook-email-frontend wget -qO- --post-data='{"username":"admin","password":"admin123"}' \
  --header='Content-Type: application/json' \
  http://outlook-email-api:8000/auth/login 2>&1 | head -10

echo -e "\n[4] 查看前端容器日志（最后30行）"
echo "----------------------------------------"
docker compose logs outlook-email-frontend --tail=30

echo -e "\n=========================================="
echo "测试完成"
echo "=========================================="

