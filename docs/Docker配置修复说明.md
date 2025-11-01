# Docker 配置修复说明

## 🐛 修复的问题

### 1. docker-compose.yml 问题

#### 问题 1：Build Context 路径错误
**错误配置**：
```yaml
build:
  context: ..
  dockerfile: docker/Dockerfile
```

**问题**：
- `context: ..` 指向父目录，但项目根目录就是当前目录
- 会导致找不到文件或路径混乱

**修复**：
```yaml
build:
  context: .
  dockerfile: docker/Dockerfile
```

#### 问题 2：数据库文件名错误
**错误配置**：
```yaml
volumes:
  - ../data.db:/app/data.db
```

**问题**：
- 项目使用的数据库文件名是 `outlook_manager.db`，不是 `data.db`
- 路径使用 `..` 不正确

**修复**：
```yaml
volumes:
  - ./outlook_manager.db:/app/outlook_manager.db
```

#### 问题 3：端口配置不一致
**错误配置**：
```yaml
ports:
  - "8001:8000"
environment:
  - PORT=8001
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/api')"]
```

**问题**：
- 容器内端口应该是 8000（Dockerfile 中 EXPOSE 8000）
- 环境变量 PORT=8001 会导致应用监听 8001，但容器映射的是 8000
- healthcheck 检查的端口应该是容器内的端口（8000）

**修复**：
```yaml
ports:
  - "8001:8000"  # 主机端口:容器端口
environment:
  - PORT=8000    # 容器内端口
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api')"]
```

#### 问题 4：未使用的 volumes 定义
**错误配置**：
```yaml
volumes:
  outlook-data:
    driver: local
```

**问题**：
- 定义了 `outlook-data` volume 但没有在服务中使用
- 造成配置混乱

**修复**：
- 移除未使用的 volumes 定义

#### 问题 5：路径前缀错误
**错误配置**：
```yaml
volumes:
  - ../logs:/app/logs
  - ../accounts.json:/app/accounts.json
```

**问题**：
- 使用 `..` 指向父目录，但应该是当前目录

**修复**：
```yaml
volumes:
  - ./logs:/app/logs
  - ./accounts.json:/app/accounts.json
```

### 2. Dockerfile 问题

#### 问题：缺少 verification_code_detector.py 文件

**问题**：
- 项目中添加了 `verification_code_detector.py` 模块
- Dockerfile 中没有复制这个文件
- 会导致运行时 ImportError

**修复**：
```dockerfile
COPY verification_code_detector.py .
```

## ✅ 修复后的完整配置

### docker-compose.yml

```yaml
version: "3.8"

services:
  outlook-email-client:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: outlook-email-api
    ports:
      - "8001:8000"
    volumes:
      # 数据持久化 - SQLite数据库文件
      - ./outlook_manager.db:/app/outlook_manager.db
      # 日志持久化 - 保留30天日志
      - ./logs:/app/logs
      # 可选：旧版JSON文件（用于迁移）
      - ./accounts.json:/app/accounts.json
    environment:
      # 可以通过环境变量覆盖默认配置
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import requests; requests.get('http://localhost:8000/api')",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - outlook-network

networks:
  outlook-network:
    driver: bridge
```

### Dockerfile 关键部分

```dockerfile
# 复制应用代码
COPY main.py .
COPY config.py .
COPY models.py .
COPY logger_config.py .
COPY database.py .
COPY auth.py .
COPY admin_api.py .
COPY account_service.py .
COPY oauth_service.py .
COPY email_service.py .
COPY email_utils.py .
COPY imap_pool.py .
COPY cache_service.py .
COPY verification_code_detector.py .  # ← 新增
COPY routes/ ./routes/
COPY static/ ./static/
COPY docker/docker-entrypoint.sh .
```

## 🚀 部署步骤

### 1. 构建镜像

```bash
cd /Users/mfrank/Documents/programming/github/OutlookManager2
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
# 查看实时日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

### 4. 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看健康检查状态
docker inspect outlook-email-api | grep -A 10 Health
```

### 5. 访问服务

- **Web 界面**：http://localhost:8001
- **API 文档**：http://localhost:8001/api
- **健康检查**：http://localhost:8001/api

## 🔍 验证修复

### 1. 检查容器是否正常启动

```bash
docker-compose ps
```

预期输出：
```
NAME                 STATUS              PORTS
outlook-email-api    Up (healthy)        0.0.0.0:8001->8000/tcp
```

### 2. 检查日志是否有错误

```bash
docker-compose logs | grep -i error
```

应该没有 ImportError 或文件找不到的错误。

### 3. 测试 API 访问

```bash
curl http://localhost:8001/api
```

应该返回 API 信息。

### 4. 检查数据库文件

```bash
# 在主机上检查
ls -lh outlook_manager.db

# 在容器内检查
docker exec outlook-email-api ls -lh /app/outlook_manager.db
```

### 5. 检查日志文件

```bash
# 在主机上检查
ls -lh logs/

# 在容器内检查
docker exec outlook-email-api ls -lh /app/logs/
```

## 📝 配置说明

### 端口映射

- **主机端口**：8001
- **容器端口**：8000
- **映射**：`8001:8000` 表示主机的 8001 端口映射到容器的 8000 端口

### 数据持久化

1. **数据库文件**：`./outlook_manager.db` → `/app/outlook_manager.db`
   - 存储账户信息、邮件缓存、系统配置等

2. **日志文件**：`./logs` → `/app/logs`
   - 存储应用日志，保留 30 天

3. **旧版配置**（可选）：`./accounts.json` → `/app/accounts.json`
   - 用于从旧版本迁移数据

### 环境变量

- `PYTHONUNBUFFERED=1`：禁用 Python 输出缓冲，实时显示日志
- `HOST=0.0.0.0`：监听所有网络接口
- `PORT=8000`：容器内应用监听的端口

### 健康检查

- **检查间隔**：30 秒
- **超时时间**：10 秒
- **重试次数**：3 次
- **启动等待**：40 秒
- **检查方法**：访问 `/api` 端点

### 重启策略

- `restart: unless-stopped`：除非手动停止，否则总是重启

## 🐛 常见问题

### 问题 1：容器启动失败

**症状**：
```bash
docker-compose ps
# 显示 Exit 或 Restarting
```

**排查**：
```bash
# 查看详细日志
docker-compose logs

# 检查配置文件语法
docker-compose config
```

### 问题 2：无法访问服务

**症状**：
```bash
curl http://localhost:8001/api
# Connection refused
```

**排查**：
1. 检查容器是否运行：`docker-compose ps`
2. 检查端口映射：`docker port outlook-email-api`
3. 检查防火墙设置
4. 查看容器日志：`docker-compose logs`

### 问题 3：数据库文件权限问题

**症状**：
```
Database error: unable to open database file
```

**解决**：
```bash
# 设置正确的文件权限
chmod 666 outlook_manager.db

# 或者使用容器内的用户权限
docker exec outlook-email-api chown -R $(id -u):$(id -g) /app/outlook_manager.db
```

### 问题 4：日志目录权限问题

**症状**：
```
Permission denied: '/app/logs/outlook_manager.log'
```

**解决**：
```bash
# 创建日志目录并设置权限
mkdir -p logs
chmod 777 logs
```

## 🔄 更新和维护

### 更新应用

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 备份数据

```bash
# 备份数据库
cp outlook_manager.db outlook_manager.db.backup.$(date +%Y%m%d)

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### 清理旧镜像

```bash
# 删除未使用的镜像
docker image prune -a

# 删除所有停止的容器
docker container prune
```

## 📚 相关文档

- [Docker部署说明.md](./Docker部署说明.md) - 详细的 Docker 部署指南
- [QUICK_START.md](./QUICK_START.md) - 快速开始指南
- [README.md](../README.md) - 项目总体说明

---

**修复时间**：2025-11-01  
**修复状态**：✅ 已完成  
**测试状态**：待验证

