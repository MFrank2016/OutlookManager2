# 登录500错误排查指南

## 1. 检查容器状态

```bash
# 检查所有容器是否运行
docker compose ps

# 检查容器日志（API服务）
docker compose logs outlook-email-api --tail=100

# 检查容器日志（前端服务）
docker compose logs outlook-email-frontend --tail=100

# 实时查看日志
docker compose logs -f outlook-email-api
```

## 2. 检查容器健康状态

```bash
# 检查API容器健康状态
docker inspect outlook-email-api | grep -A 10 Health

# 检查容器是否正常启动
docker compose ps -a
```

## 3. 检查数据库连接

```bash
# 进入API容器
docker compose exec outlook-email-api sh

# 在容器内检查环境变量
env | grep DB_

# 检查数据库文件（SQLite）
ls -la /app/data.db

# 如果使用PostgreSQL，测试连接
# 需要先安装psql或使用Python测试
python -c "import psycopg2; conn = psycopg2.connect(host='postgresql', dbname='outlook_manager', user='outlook_user', password='changeme'); print('Connected')"
```

## 4. 检查网络连接

```bash
# 检查容器网络
docker network inspect outlook-network

# 测试API容器内部连接
docker compose exec outlook-email-api wget -O- http://localhost:8000/api

# 测试前端到后端的连接
docker compose exec outlook-email-frontend wget -O- http://outlook-email-api:8000/api
```

## 5. 检查环境变量

```bash
# 查看API容器的环境变量
docker compose exec outlook-email-api env

# 检查.env文件（如果使用）
cat .env
```

## 6. 常见问题及解决方案

### 问题1: 数据库未初始化

**症状**: 登录时返回500，日志显示数据库相关错误

**解决**:
```bash
# 检查数据库文件权限
ls -la data.db

# 如果文件不存在或权限错误，重新初始化
docker compose exec outlook-email-api python -c "import database; database.init_db()"
```

### 问题2: PostgreSQL连接失败

**症状**: 日志显示 "could not connect to server"

**解决**:
```bash
# 检查PostgreSQL容器是否运行
docker compose ps postgresql

# 检查PostgreSQL日志
docker compose logs postgresql --tail=50

# 确保环境变量正确
docker compose exec outlook-email-api env | grep DB_
```

### 问题3: 日志没有输出

**症状**: 容器运行但没有日志

**解决**:
```bash
# 检查日志目录权限
ls -la logs/

# 确保日志目录可写
chmod 777 logs/

# 检查Python日志配置
docker compose exec outlook-email-api python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.info('Test')"
```

### 问题4: 端口冲突

**症状**: 容器无法启动或端口被占用

**解决**:
```bash
# 检查端口占用
netstat -tuln | grep 8001
netstat -tuln | grep 3000

# 修改docker-compose.yml中的端口映射
# 或停止占用端口的服务
```

## 7. 手动测试登录接口

```bash
# 在服务器上直接测试API
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# 查看详细响应
curl -v -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

## 8. 检查应用启动日志

```bash
# 查看完整的启动日志
docker compose logs outlook-email-api | grep -i "start\|error\|exception\|traceback"

# 查看最近的错误
docker compose logs outlook-email-api --tail=200 | grep -i error
```

## 9. 重启服务

```bash
# 重启所有服务
docker compose restart

# 完全重建并重启
docker compose down
docker compose up -d --build

# 只重启API服务
docker compose restart outlook-email-api
```

## 10. 检查文件挂载

```bash
# 检查数据文件挂载
ls -la data.db
ls -la logs/

# 检查挂载点权限
docker compose exec outlook-email-api ls -la /app/data.db
docker compose exec outlook-email-api ls -la /app/logs
```

## 快速诊断命令

运行以下命令获取完整诊断信息：

```bash
#!/bin/bash
echo "=== 容器状态 ==="
docker compose ps

echo -e "\n=== API容器日志（最后50行）==="
docker compose logs outlook-email-api --tail=50

echo -e "\n=== 数据库连接测试 ==="
docker compose exec outlook-email-api python -c "
import os
print('DB_TYPE:', os.getenv('DB_TYPE', 'not set'))
print('DB_HOST:', os.getenv('DB_HOST', 'not set'))
print('DB_NAME:', os.getenv('DB_NAME', 'not set'))
"

echo -e "\n=== 网络连接测试 ==="
docker compose exec outlook-email-api wget -qO- http://localhost:8000/api || echo "API endpoint not accessible"

echo -e "\n=== 文件权限检查 ==="
ls -la data.db logs/ 2>/dev/null || echo "Files not found"
```

保存为 `diagnose.sh`，然后运行：
```bash
chmod +x diagnose.sh
./diagnose.sh
```

