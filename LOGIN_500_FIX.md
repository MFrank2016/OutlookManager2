# 登录500错误修复指南

## 问题现象
- 容器运行正常（healthy状态）
- 登录接口返回500错误
- 服务端容器没有收到日志

## 立即执行的诊断步骤

### 1. 检查容器日志（最重要！）

```bash
# 查看API容器完整日志
docker compose logs outlook-email-api

# 查看最近100行日志
docker compose logs outlook-email-api --tail=100

# 实时查看日志（然后尝试登录）
docker compose logs -f outlook-email-api
```

**如果没有日志输出，说明应用可能没有正常启动**

### 2. 检查应用是否真的在运行

```bash
# 进入容器检查进程
docker compose exec outlook-email-api ps aux

# 应该看到 uvicorn 进程在运行

# 检查端口监听
docker compose exec outlook-email-api netstat -tuln | grep 8000
# 或
docker compose exec outlook-email-api ss -tuln | grep 8000
```

### 3. 测试API端点可访问性

```bash
# 从容器内部测试
docker compose exec outlook-email-api wget -qO- http://localhost:8000/api

# 从主机测试（注意端口映射）
curl http://localhost:8000/api

# 测试登录接口
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 4. 检查数据库状态

```bash
# 检查数据库文件
ls -la data.db

# 检查数据库文件权限
docker compose exec outlook-email-api ls -la /app/data.db

# 检查数据库是否有用户
docker compose exec outlook-email-api python -c "
import sys
sys.path.insert(0, '/app')
import database as db
users = db.get_all_users()
print(f'用户数量: {len(users)}')
for user in users:
    print(f'  - {user.get(\"username\")} (role: {user.get(\"role\")})')
"
```

### 5. 检查环境变量

```bash
# 查看所有环境变量
docker compose exec outlook-email-api env | sort

# 检查关键环境变量
docker compose exec outlook-email-api env | grep -E "DB_|LOG_|PYTHON"
```

### 6. 手动初始化数据库（如果需要）

```bash
# 进入容器
docker compose exec outlook-email-api sh

# 在容器内运行
python -c "
import sys
sys.path.insert(0, '/app')
import database as db
import auth

# 初始化数据库
print('初始化数据库...')
db.init_database()
print('数据库初始化完成')

# 创建默认管理员
print('创建默认管理员...')
auth.init_default_admin()
print('默认管理员创建完成')
"
```

## 常见问题及解决方案

### 问题1: 数据库文件权限错误

**症状**: 日志显示 "Permission denied" 或数据库相关错误

**解决**:
```bash
# 修复文件权限
chmod 666 data.db
chmod 777 logs/

# 或删除后让容器重新创建
rm data.db
docker compose restart outlook-email-api
```

### 问题2: 数据库未初始化

**症状**: 登录时提示用户不存在

**解决**:
```bash
# 手动初始化（见上面的步骤6）
```

### 问题3: PostgreSQL连接失败

**症状**: 日志显示 "could not connect to server"

**解决**:
```bash
# 检查PostgreSQL容器
docker compose ps postgresql

# 检查PostgreSQL日志
docker compose logs postgresql --tail=50

# 检查环境变量
docker compose exec outlook-email-api env | grep DB_
```

### 问题4: 请求没有到达后端

**症状**: 完全没有日志，但前端显示500错误

**可能原因**:
- Next.js代理配置问题
- 网络连接问题

**解决**:
```bash
# 检查前端容器日志
docker compose logs outlook-email-frontend --tail=50

# 检查前端是否能访问后端
docker compose exec outlook-email-frontend wget -qO- http://outlook-email-api:8000/api
```

### 问题5: 应用启动失败但容器显示健康

**症状**: 容器healthy但应用没有运行

**解决**:
```bash
# 检查启动脚本
docker compose exec outlook-email-api cat docker-entrypoint.sh

# 手动运行启动命令测试
docker compose exec outlook-email-api sh -c "cd /app && uvicorn main:app --host 0.0.0.0 --port 8000"
```

## 快速修复命令

```bash
# 完全重启所有服务
docker compose down
docker compose up -d

# 查看启动日志
docker compose logs -f outlook-email-api

# 等待30秒后测试
sleep 30
curl http://localhost:8000/api
```

## 如果仍然无法解决

请提供以下信息：

1. **容器日志**:
   ```bash
   docker compose logs outlook-email-api > api_logs.txt
   ```

2. **测试结果**:
   ```bash
   curl -v http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}' > login_test.txt
   ```

3. **环境信息**:
   ```bash
   docker compose exec outlook-email-api env > env.txt
   ```

4. **数据库状态**:
   ```bash
   ls -la data.db logs/ > files.txt
   ```

