# Docker 部署管理指南

## 📋 概述

本项目使用 Docker 和 Docker Compose 进行容器化部署，支持一键启动、更新和管理服务。

## 🚀 快速开始

### 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+（或 docker-compose 1.29+）
- 至少 2GB 可用磁盘空间

### 首次部署

1. **克隆项目并进入目录**

   ```bash
   git clone <repository-url>
   cd OutlookManager2
   ```

2. **配置环境变量（可选）**

   ```bash
   # 复制环境变量示例文件（如果不存在 .env 文件）
   if [ ! -f .env ]; then
       cp docker/docker.env.example .env
       echo ".env 文件已创建，使用默认配置"
   else
       echo ".env 文件已存在，跳过创建"
   fi

   # 根据需要编辑 .env 文件
   # 主要配置项：
   # - PORT: 外部访问端口（默认 8001）
   # - LOG_LEVEL: 日志级别（默认 info）
   # - TZ: 时区（默认 Asia/Shanghai）
   ```

   **注意**：如果 `.env` 文件不存在，Docker Compose 会使用 `environment` 部分定义的默认值，服务仍可正常启动。

3. **构建并启动服务**

   ```bash
   # 方式一：使用 docker compose（推荐，Docker 20.10+）
   docker compose up -d --build

   # 方式二：使用 docker-compose（旧版本）
   docker-compose up -d --build
   ```

4. **查看服务状态**

   ```bash
   docker compose ps
   # 或
   docker-compose ps
   ```

5. **查看日志**

   ```bash
   docker compose logs -f
   # 或
   docker-compose logs -f
   ```

6. **访问服务**
   - 前端界面：http://localhost:3000（推荐）
   - API 文档：http://localhost:8001/docs
   - 后端 API：http://localhost:8001
   - 健康检查：http://localhost:8001/api

## 🔄 更新代码

### 方案一：完整更新（推荐，确保完全使用新代码）

```bash
# 1. 停止并删除旧容器
docker compose down
# 或
docker-compose down

# 2. 重新构建镜像（不使用缓存）
docker compose build --no-cache
# 或
docker-compose build --no-cache

# 3. 启动新容器
docker compose up -d
# 或
docker-compose up -d

# 4. 查看日志验证
docker compose logs -f
# 或
docker-compose logs -f
```

**或使用提供的脚本：**

```bash
# Linux/Mac
chmod +x update_docker.sh
./update_docker.sh

# Windows
update_docker.bat
```

### 方案二：快速更新（使用缓存，速度更快）

```bash
# 停止旧容器
docker compose down
# 或
docker-compose down

# 重新构建（使用缓存）
docker compose build
# 或
docker-compose build

# 启动新容器
docker compose up -d
# 或
docker-compose up -d
```

**或使用快速脚本：**

```bash
chmod +x update_docker_quick.sh
./update_docker_quick.sh
```

### 方案三：仅重启容器（代码已通过 volume 挂载时）

如果使用 volume 挂载代码目录（仅开发环境），修改代码后只需：

```bash
docker compose restart
# 或
docker-compose restart
```

## 🔍 验证更新

### 1. 检查容器状态

```bash
docker compose ps
# 或
docker-compose ps
```

应该看到容器状态为 `Up` 或 `running`，健康状态为 `healthy`。

### 2. 查看容器日志

```bash
# 查看实时日志
docker compose logs -f
# 或
docker-compose logs -f

# 查看最近50行日志
docker compose logs --tail=50
# 或
docker-compose logs --tail=50
```

在日志中应该能看到应用启动信息：

```
==========================================
Outlook邮件管理系统启动中...
==========================================
Python版本: Python 3.11.x
工作目录: /app
时区: Asia/Shanghai
检查Python依赖...
所有依赖已安装
启动FastAPI应用...
监听地址: 0.0.0.0:8000
日志级别: info
==========================================
```

### 3. 进入容器验证代码

```bash
# 进入容器
docker compose exec outlook-email-api /bin/sh
# 或
docker-compose exec outlook-email-api /bin/sh

# 查看文件列表
ls -lh

# 检查代码内容
grep -A 5 "Outlook邮件管理系统" main.py

# 检查依赖
pip list | grep cachetools

# 退出容器
exit
```

### 4. 测试功能

1. 浏览器访问：`http://localhost:8001`
2. 登录后台管理系统
3. 进入账户管理页面
4. 测试邮件列表和详情功能
5. 检查浏览器开发者工具 Network 标签，确认 API 请求正常

## 🛠️ 常用 Docker Compose 命令

### 服务管理

```bash
# 启动服务（后台运行）
docker compose up -d
docker-compose up -d

# 启动服务（前台运行，查看日志）
docker compose up
docker-compose up

# 停止服务
docker compose stop
docker-compose stop

# 停止并删除容器
docker compose down
docker-compose down

# 停止并删除容器、网络、卷
docker compose down -v
docker-compose down -v

# 重启服务
docker compose restart
docker-compose restart
```

### 构建管理

```bash
# 构建镜像（不使用缓存）
docker compose build --no-cache
docker-compose build --no-cache

# 构建镜像（使用缓存）
docker compose build
docker-compose build

# 强制重新创建容器
docker compose up -d --force-recreate
docker-compose up -d --force-recreate
```

### 日志管理

```bash
# 查看所有服务日志
docker compose logs
docker-compose logs

# 实时跟踪日志
docker compose logs -f
docker-compose logs -f

# 查看最近100行日志
docker compose logs --tail=100
docker-compose logs --tail=100

# 查看特定服务的日志
docker compose logs outlook-email-api
docker-compose logs outlook-email-api
```

### 容器管理

```bash
# 查看容器状态
docker compose ps
docker-compose ps

# 进入容器
docker compose exec outlook-email-api /bin/sh
docker-compose exec outlook-email-api /bin/sh

# 执行命令
docker compose exec outlook-email-api python -c "import cachetools; print(cachetools.__version__)"
docker-compose exec outlook-email-api python -c "import cachetools; print(cachetools.__version__)"

# 查看容器资源使用
docker stats outlook-email-api
```

## 📝 项目结构说明

### Docker 相关文件

```
OutlookManager2/
├── docker/
│   ├── Dockerfile              # Docker 镜像构建文件
│   ├── docker-entrypoint.sh    # 容器启动脚本
│   └── docker.env.example      # 环境变量配置示例
├── docker-compose.yml          # Docker Compose 配置文件
├── .dockerignore               # Docker 构建忽略文件
├── .env                        # 环境变量配置文件（需创建）
└── requirements.txt            # Python 依赖列表
```

### 数据持久化

以下文件/目录通过 volume 挂载，数据会持久化到宿主机：

- `./data.db` → `/app/data.db` - SQLite 数据库文件
- `./logs` → `/app/logs` - 应用日志目录
- `./accounts.json` → `/app/accounts.json` - 账户配置文件（可选，用于迁移）

### 代码结构

项目代码在构建时复制到镜像中，包括：

- Python 应用代码（main.py, config.py, models.py 等）
- 路由模块（routes/）
- DAO 层（dao/）
- 静态文件（static/）
- 其他服务模块（email_service.py, oauth_service.py 等）

## ⚙️ 配置说明

### 环境变量配置

通过 `.env` 文件配置环境变量（从 `docker/docker.env.example` 复制）：

```bash
# 服务配置
HOST=0.0.0.0          # 监听地址
PORT=8000             # 容器内部端口（外部端口在 docker-compose.yml 中配置）

# Python 配置
PYTHONUNBUFFERED=1    # 实时输出日志
PYTHONDONTWRITEBYTECODE=1  # 不生成 .pyc 文件

# 应用配置
LOG_LEVEL=info        # 日志级别：debug, info, warning, error
TZ=Asia/Shanghai      # 时区设置
```

### 端口配置

在 `docker-compose.yml` 中配置端口映射：

```yaml
ports:
  - "${PORT:-8001}:8000" # 外部端口:容器内部端口
```

- 外部端口（8001）：通过浏览器访问的端口
- 容器内部端口（8000）：应用在容器内监听的端口

### 网络配置

项目使用自定义网络 `outlook-network`，便于后续扩展（如添加数据库、Redis 等）。

## 🔄 更新流程详解

### 为什么需要重新构建？

查看 `docker/Dockerfile`：

```dockerfile
# 复制应用代码
COPY main.py .
COPY config.py .
COPY routes/ ./routes/
COPY dao/ ./dao/
...
```

这些 COPY 指令在**构建镜像时**执行一次，将代码复制到镜像内部。之后即使本地代码修改了，容器内的代码仍然是构建时的版本。

### `docker compose up -d` 为什么不更新代码？

- `docker compose up -d`：只启动容器，如果镜像已存在，直接使用现有镜像
- 不会自动检测代码变化
- 不会重新构建镜像

### `docker compose build` 做了什么？

- 重新执行 Dockerfile 中的所有指令
- 重新 COPY 代码文件到镜像
- 重新安装 Python 依赖（如果 requirements.txt 变化）
- 创建新的镜像层

### `--no-cache` 参数的作用

- 不使用 Docker 构建缓存
- 强制重新执行所有步骤
- 确保使用最新的代码和依赖
- 构建时间更长，但结果更可靠

## 🎯 最佳实践

### 开发环境

如果经常需要修改代码，可以考虑使用 volume 挂载代码：

修改 `docker-compose.yml`，添加代码 volume：

```yaml
volumes:
  - ./data.db:/app/data.db
  - ./logs:/app/logs
  # 挂载代码目录（开发环境）
  - ./main.py:/app/main.py
  - ./routes:/app/routes
  - ./dao:/app/dao
  # ... 其他代码文件
```

**优点：** 修改代码后只需重启容器 `docker compose restart`  
**缺点：** 与容器化理念不符，不适合生产环境

### 生产环境（当前方式）

使用 COPY 方式固化代码到镜像：

**优点：**

- ✅ 代码与镜像打包在一起，部署一致性高
- ✅ 不依赖外部文件系统
- ✅ 可以方便地版本管理和回滚
- ✅ 支持多环境部署（开发、测试、生产）

**缺点：**

- ❌ 更新代码需要重新构建镜像

## 🚨 故障排查

### 问题 1：构建失败

```bash
# 查看详细构建日志
docker compose build --no-cache --progress=plain
docker-compose build --no-cache --progress=plain

# 检查磁盘空间
df -h  # Linux/Mac
# 或
wmic logicaldisk get size,freespace,caption  # Windows

# 清理Docker缓存
docker system prune -a
```

### 问题 2：容器无法启动

```bash
# 查看容器日志
docker compose logs outlook-email-api
docker-compose logs outlook-email-api

# 检查端口占用
netstat -tulpn | grep 8001  # Linux
lsof -i :8001  # Mac
netstat -ano | findstr :8001  # Windows

# 检查容器状态
docker compose ps
docker-compose ps
```

### 问题 3：代码仍然是旧的

```bash
# 确认是否重新构建了镜像
docker images | grep outlook-email-api

# 查看镜像创建时间，应该是最近的时间
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"

# 删除旧镜像强制重建
docker compose down
docker rmi outlook-email-api:latest
docker compose build --no-cache
docker compose up -d
```

### 问题 4：依赖缺失错误

如果遇到 `ModuleNotFoundError`，检查：

1. **requirements.txt 是否包含所有依赖**

   ```bash
   cat requirements.txt
   ```

2. **重新构建镜像**

   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

3. **进入容器检查依赖**
   ```bash
   docker compose exec outlook-email-api pip list
   ```

### 问题 5：数据库文件权限问题

```bash
# 检查数据库文件权限
ls -lh data.db

# 修复权限（Linux/Mac）
chmod 666 data.db

# 检查容器内权限
docker compose exec outlook-email-api ls -lh /app/data.db
```

### 问题 6：时区不正确

```bash
# 检查容器时区
docker compose exec outlook-email-api date

# 检查环境变量
docker compose exec outlook-email-api env | grep TZ

# 确保 .env 文件中设置了 TZ=Asia/Shanghai
```

## 📊 监控和维护

### 查看资源使用

```bash
# 实时监控容器资源
docker stats outlook-email-api

# 查看容器详细信息
docker inspect outlook-email-api
```

### 备份数据

```bash
# 备份数据库
cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

### 清理旧日志

```bash
# 进入容器清理日志
docker compose exec outlook-email-api find /app/logs -name "*.log.*" -mtime +30 -delete
```

## 🔐 安全建议

1. **不要将 `.env` 文件提交到 Git**

   - `.env` 文件可能包含敏感信息
   - 使用 `.env.example` 作为模板

2. **定期更新基础镜像**

   - 检查 `docker/Dockerfile` 中的基础镜像版本
   - 定期更新以获取安全补丁

3. **限制端口访问**

   - 在生产环境中，使用防火墙限制端口访问
   - 考虑使用反向代理（Nginx）进行访问控制

4. **数据备份**
   - 定期备份 `data.db` 文件
   - 考虑使用数据库备份工具

## 📞 需要帮助？

如果问题仍未解决，请提供以下信息：

1. Docker 版本：`docker --version`
2. Docker Compose 版本：`docker compose version` 或 `docker-compose --version`
3. 容器状态：`docker compose ps`
4. 容器日志：`docker compose logs --tail=100`
5. 镜像信息：`docker images | grep outlook`
6. 系统信息：`uname -a`（Linux/Mac）或 `systeminfo`（Windows）
7. 错误截图或详细错误信息

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- 项目 README.md
