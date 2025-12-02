# Docker 部署管理指南

## 📋 概述

本项目使用 Docker 和 Docker Compose 进行容器化部署，支持一键启动、更新和管理服务。

**支持的数据库**：

- SQLite（默认，适合小规模部署）
- PostgreSQL（推荐，适合生产环境和大规模部署）

**服务组件**：

- 后端 API 服务（FastAPI）
- 前端服务（Next.js，可选）
- PostgreSQL 数据库（可选）

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

2. **配置环境变量**

   ```bash
   # 复制环境变量示例文件（如果不存在 .env 文件）
   if [ ! -f .env ]; then
       cp docker/docker.env.example .env
       echo ".env 文件已创建，使用默认配置"
   else
       echo ".env 文件已存在，跳过创建"
   fi
   ```

   **配置数据库类型**：

   #### 方式 1: 使用 SQLite（默认，简单快速）

   无需额外配置，直接使用默认设置即可。

   #### 方式 2: 使用 PostgreSQL（推荐生产环境）

   编辑 `.env` 文件，添加以下配置：

   ```bash
   # 数据库类型
   DB_TYPE=postgresql

   # PostgreSQL连接配置（Docker网络连接）
   DB_HOST=postgresql          # 使用容器名，通过Docker网络连接
   DB_PORT=5432
   DB_NAME=outlook_manager
   DB_USER=outlook_user
   DB_PASSWORD=outlook_manager233

   # PostgreSQL连接池配置
   DB_POOL_SIZE=5
   DB_MAX_OVERFLOW=15
   DB_POOL_TIMEOUT=30

   # PostgreSQL服务配置（用于启动PostgreSQL容器）
   POSTGRES_DB=outlook_manager
   POSTGRES_USER=outlook_user
   POSTGRES_PASSWORD=outlook_manager233
   POSTGRES_PORT=5432

   # 应用配置
   PORT=8001                   # 外部访问端口
   LOG_LEVEL=info              # 日志级别
   TZ=Asia/Shanghai            # 时区
   ```

   **重要提示**：

   - 如果使用 PostgreSQL，确保 `DB_PASSWORD` 和 `POSTGRES_PASSWORD` 相同
   - 使用强密码，不要使用默认的 `changeme`
   - 如果 PostgreSQL 在远程服务器，将 `DB_HOST` 改为服务器 IP 地址

3. **初始化数据库（如果使用 PostgreSQL）**

   如果使用 PostgreSQL，需要先启动 PostgreSQL 服务并初始化数据库：

   ```bash
   # 启动PostgreSQL服务
   docker compose up -d postgresql

   # 等待PostgreSQL就绪（约30秒）
   docker compose ps postgresql

   # 初始化数据库（创建表和索引）
   docker compose exec outlook-email-api python3 scripts/init_postgresql.py
   ```

   **注意**：如果使用 SQLite，数据库会在应用首次启动时自动创建，无需手动初始化。

4. **构建并启动服务**

   ```bash
   # 方式一：使用 docker compose（推荐，Docker 20.10+）
   docker compose up -d --build

   # 方式二：使用 docker-compose（旧版本）
   docker-compose up -d --build
   ```

   **启动所有服务**（包括 PostgreSQL，如果配置了）：

   ```bash
   docker compose up -d --build
   ```

   **仅启动应用服务**（如果 PostgreSQL 在远程服务器）：

   ```bash
   docker compose up -d --build outlook-email-api outlook-email-frontend
   ```

   **注意**：如果前端服务没有启动，请检查：

   - 构建日志：`docker compose build outlook-email-frontend`
   - 容器日志：`docker compose logs outlook-email-frontend`
   - 容器状态：`docker compose ps -a`

5. **查看服务状态**

   ```bash
   docker compose ps
   # 或
   docker-compose ps
   ```

   应该看到以下服务：

   - `outlook-email-api` - 后端 API 服务
   - `outlook-email-frontend` - 前端服务（如果启用）
   - `outlook-postgresql` - PostgreSQL 数据库（如果使用）

6. **查看日志**

   ```bash
   # 查看所有服务日志
   docker compose logs -f

   # 查看特定服务日志
   docker compose logs -f outlook-email-api
   docker compose logs -f postgresql
   ```

7. **验证数据库连接**

   #### 如果使用 PostgreSQL

   ```bash
   # 方式1: 使用验证脚本（推荐）
   docker compose exec outlook-email-api python3 scripts/verify_postgresql.py

   # 方式2: 直接连接PostgreSQL
   docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT version();"

   # 检查表是否创建
   docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "\dt"

   # 检查应用日志，确认数据库连接成功
   docker compose logs outlook-email-api | grep -i "database\|postgresql"
   ```

   **验证脚本功能**：

   - 测试数据库连接
   - 显示 PostgreSQL 版本
   - 显示数据库大小
   - 列出所有表
   - 显示当前连接数

   #### 如果使用 SQLite

   ```bash
   # 检查数据库文件
   ls -lh data.db

   # 检查应用日志
   docker compose logs outlook-email-api | grep -i "database\|sqlite"
   ```

8. **访问服务**
   - 前端界面：http://localhost:3000（推荐）
   - API 文档：http://localhost:8001/docs
   - 后端 API：http://localhost:8001
   - 健康检查：http://localhost:8001/api
   - 管理面板：http://localhost:8001（登录后访问）

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

**SQLite 模式**：

- `./data.db` → `/app/data.db` - SQLite 数据库文件

**PostgreSQL 模式**：

- `postgres_data` - PostgreSQL 数据卷（Docker 管理）
- 数据存储在 Docker 卷中，可通过 `docker volume inspect outlook_postgres_data` 查看位置

**通用**：

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

#### 基础配置

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

#### 数据库配置

**SQLite 配置（默认）**：

```bash
DB_TYPE=sqlite
# 无需其他配置，数据库文件自动创建在 ./data.db
```

**PostgreSQL 配置（Docker 网络连接）**：

```bash
# 数据库类型
DB_TYPE=postgresql

# 连接配置（使用Docker网络，容器名连接）
DB_HOST=postgresql          # 容器名，通过Docker网络连接
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password_here

# 连接池配置
DB_POOL_SIZE=5             # 最小连接数
DB_MAX_OVERFLOW=15         # 最大连接数 = POOL_SIZE + MAX_OVERFLOW
DB_POOL_TIMEOUT=30         # 连接超时（秒）

# PostgreSQL服务配置（用于启动PostgreSQL容器）
POSTGRES_DB=outlook_manager
POSTGRES_USER=outlook_user
POSTGRES_PASSWORD=your_strong_password_here  # 必须与DB_PASSWORD相同
POSTGRES_PORT=5432
```

**PostgreSQL 配置（远程连接）**：

```bash
# 如果PostgreSQL在远程服务器
DB_TYPE=postgresql
DB_HOST=192.168.1.100      # 远程服务器IP
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password_here
# 其他配置同上
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

项目使用自定义网络 `outlook-network`，所有服务（API、前端、PostgreSQL）都在同一网络中。

**连接方式**：

- **Docker 网络连接**：同一网络内的容器可以通过容器名互相访问
  - 应用连接 PostgreSQL：`DB_HOST=postgresql`（容器名）
  - 前端连接后端：`BACKEND_URL=http://outlook-email-api:8000`（容器名）
- **远程连接**：通过端口映射访问
  - 访问 API：`http://localhost:8001`
  - 访问 PostgreSQL：`localhost:5432`（用于数据库管理工具）

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

## 💾 数据库管理

### SQLite 数据库

#### 查看数据库

```bash
# 进入容器
docker compose exec outlook-email-api /bin/sh

# 使用sqlite3查看数据库
sqlite3 /app/data.db ".tables"
sqlite3 /app/data.db "SELECT COUNT(*) FROM accounts;"

# 退出容器
exit
```

#### 备份数据库

```bash
# 备份SQLite数据库
cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)
```

#### 修复数据库

```bash
# 如果数据库损坏，运行修复脚本
docker compose exec outlook-email-api python3 scripts/repair_database.py
```

### PostgreSQL 数据库

#### 连接 PostgreSQL

**方式 1: 通过 Docker 容器连接**

```bash
# 进入PostgreSQL容器
docker compose exec postgresql psql -U outlook_user -d outlook_manager

# 执行SQL命令
\dt                    # 查看所有表
SELECT COUNT(*) FROM accounts;  # 查询数据
\q                     # 退出
```

**方式 2: 使用数据库管理工具（远程连接）**

使用以下连接信息：

- **主机**: `localhost` 或服务器 IP
- **端口**: `5432`（或你在.env 中设置的 POSTGRES_PORT）
- **数据库**: `outlook_manager`
- **用户名**: `outlook_user`
- **密码**: 你在.env 中设置的 POSTGRES_PASSWORD

**推荐工具**：

- DBeaver（免费，跨平台）
- pgAdmin（PostgreSQL 官方工具）
- DataGrip（JetBrains，付费）
- Navicat（付费）

#### 初始化数据库

```bash
# 如果数据库未初始化，运行初始化脚本
docker compose exec outlook-email-api python3 scripts/init_postgresql.py
```

#### 备份 PostgreSQL 数据库

```bash
# 备份数据库
docker compose exec postgresql pg_dump -U outlook_user outlook_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用压缩备份
docker compose exec postgresql pg_dump -U outlook_user -Fc outlook_manager > backup_$(date +%Y%m%d_%H%M%S).dump
```

#### 恢复 PostgreSQL 数据库

```bash
# 恢复数据库
docker compose exec -T postgresql psql -U outlook_user outlook_manager < backup_20250101.sql

# 或从压缩备份恢复
docker compose exec -T postgresql pg_restore -U outlook_user -d outlook_manager < backup_20250101.dump
```

#### 查看 PostgreSQL 状态

```bash
# 查看数据库大小
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT pg_size_pretty(pg_database_size('outlook_manager'));"

# 查看连接数
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT count(*) FROM pg_stat_activity;"

# 查看表统计信息
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables;"
```

#### PostgreSQL 性能优化

```bash
# 执行VACUUM和ANALYZE（优化数据库）
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "VACUUM ANALYZE;"

# 重建索引（如果需要）
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "REINDEX DATABASE outlook_manager;"
```

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

### 问题 5：数据库文件权限问题（SQLite）

```bash
# 检查数据库文件权限
ls -lh data.db

# 修复权限（Linux/Mac）
chmod 666 data.db

# 检查容器内权限
docker compose exec outlook-email-api ls -lh /app/data.db
```

### 问题 6：PostgreSQL 连接失败

**症状**：应用日志中出现 "Failed to connect to PostgreSQL" 或 "database connection error"

**检查步骤**：

```bash
# 1. 检查PostgreSQL容器是否运行
docker compose ps postgresql

# 2. 检查PostgreSQL日志
docker compose logs postgresql

# 3. 测试PostgreSQL连接
docker compose exec postgresql pg_isready -U outlook_user -d outlook_manager

# 4. 检查环境变量配置
docker compose exec outlook-email-api env | grep DB_

# 5. 测试从应用容器连接PostgreSQL
docker compose exec outlook-email-api ping postgresql
```

**解决方案**：

1. **确保 PostgreSQL 已启动**：

   ```bash
   docker compose up -d postgresql
   ```

2. **检查密码配置**：

   - 确保 `.env` 文件中的 `DB_PASSWORD` 和 `POSTGRES_PASSWORD` 相同
   - 检查是否有特殊字符需要转义

3. **检查网络连接**：

   ```bash
   # 确认应用和PostgreSQL在同一网络
   docker network inspect outlook-network

   # 从应用容器测试连接
   docker compose exec outlook-email-api python3 -c "
   import psycopg2
   from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
   conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
   print('连接成功！')
   conn.close()
   "
   ```

4. **重新初始化数据库**：
   ```bash
   docker compose exec outlook-email-api python3 scripts/init_postgresql.py
   ```

### 问题 7：PostgreSQL 远程连接失败

**症状**：无法使用数据库管理工具连接到 PostgreSQL

**检查步骤**：

```bash
# 1. 检查端口映射
docker compose ps postgresql
# 应该显示端口映射，如 0.0.0.0:5432->5432/tcp

# 2. 检查PostgreSQL是否监听所有接口
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SHOW listen_addresses;"
# 应该显示: *

# 3. 测试端口是否开放
telnet localhost 5432
# 或
nc -zv localhost 5432
```

**解决方案**：

1. **检查防火墙设置**：

   ```bash
   # Linux (ufw)
   sudo ufw status
   sudo ufw allow 5432/tcp

   # Linux (firewalld)
   sudo firewall-cmd --list-ports
   sudo firewall-cmd --permanent --add-port=5432/tcp
   sudo firewall-cmd --reload
   ```

2. **检查 PostgreSQL 配置**：

   - 确保 `docker-compose.yml` 中 PostgreSQL 的 `command` 包含 `-c listen_addresses='*'`
   - 重启 PostgreSQL 容器：`docker compose restart postgresql`

3. **检查 pg_hba.conf**（如果需要）：
   ```bash
   docker compose exec postgresql cat /var/lib/postgresql/data/pg_hba.conf
   ```

### 问题 8：时区不正确

```bash
# 检查容器时区
docker compose exec outlook-email-api date
docker compose exec postgresql date

# 检查环境变量
docker compose exec outlook-email-api env | grep TZ
docker compose exec postgresql env | grep TZ

# 确保 .env 文件中设置了 TZ=Asia/Shanghai
```

### 问题 9：SQLite 数据库损坏

**症状**：应用启动失败，日志中出现：

```
Tree 147 page 96790 cell 3: Rowid 978297 out of order
sqlite3.ProgrammingError: Cannot operate on a closed database.
ERROR: Application startup failed. Exiting.
```

**快速解决方案**：

#### 方案 1: 切换到 PostgreSQL（推荐，如果已配置）

```bash
# 1. 停止应用
docker compose stop outlook-email-api

# 2. 编辑.env文件，设置PostgreSQL
# DB_TYPE=postgresql
# DB_HOST=postgresql
# DB_PORT=5432
# DB_NAME=outlook_manager
# DB_USER=outlook_user
# DB_PASSWORD=your_password
# POSTGRES_PASSWORD=your_password

# 3. 初始化PostgreSQL数据库
docker compose exec outlook-email-api python3 scripts/init_postgresql.py

# 4. 启动应用
docker compose start outlook-email-api
```

#### 方案 2: 修复 SQLite 数据库

```bash
# 方法A: 使用修复脚本
docker compose exec outlook-email-api bash scripts/fix_corrupted_db.sh

# 方法B: 使用Python修复脚本
docker compose exec outlook-email-api python3 scripts/repair_database.py

# 方法C: 重建数据库（会丢失数据）
cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)
rm data.db
docker compose restart outlook-email-api
```

**详细说明**：参见 [SQLite 数据库损坏修复指南](docs/SQLITE_CORRUPTION_FIX.md)

### 问题 10：数据库表不存在

**症状**：应用启动后提示表不存在或初始化失败

**解决方案**：

**SQLite**：

```bash
# 删除旧数据库文件，让应用重新创建
rm data.db
docker compose restart outlook-email-api
```

**PostgreSQL**：

```bash
# 运行初始化脚本
docker compose exec outlook-email-api python3 scripts/init_postgresql.py

# 或手动执行SQL
docker compose exec -T postgresql psql -U outlook_user -d outlook_manager < database/postgresql_schema.sql
docker compose exec -T postgresql psql -U outlook_user -d outlook_manager < database/postgresql_indexes.sql
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

#### SQLite 备份

```bash
# 备份SQLite数据库
cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)

# 或使用SQLite备份命令
docker compose exec outlook-email-api sqlite3 /app/data.db ".backup '/app/data.db.backup'"
```

#### PostgreSQL 备份

```bash
# 备份PostgreSQL数据库（SQL格式）
docker compose exec postgresql pg_dump -U outlook_user outlook_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份PostgreSQL数据库（压缩格式，推荐）
docker compose exec postgresql pg_dump -U outlook_user -Fc outlook_manager > backup_$(date +%Y%m%d_%H%M%S).dump

# 备份PostgreSQL数据库（仅数据，不含结构）
docker compose exec postgresql pg_dump -U outlook_user -a outlook_manager > backup_data_$(date +%Y%m%d_%H%M%S).sql

# 备份PostgreSQL数据库（仅结构，不含数据）
docker compose exec postgresql pg_dump -U outlook_user -s outlook_manager > backup_schema_$(date +%Y%m%d_%H%M%S).sql
```

#### 通用备份

```bash
# 备份日志
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/

# 备份配置文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
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

   - **SQLite**: 定期备份 `data.db` 文件
   - **PostgreSQL**: 使用 `pg_dump` 定期备份
   - 考虑使用自动化备份脚本
   - 建议保留至少 7 天的备份

5. **PostgreSQL 安全**
   - 使用强密码，不要使用默认密码
   - 限制远程访问 IP（使用防火墙）
   - 生产环境建议启用 SSL 连接
   - 定期更新 PostgreSQL 镜像以获取安全补丁

## 📞 需要帮助？

如果问题仍未解决，请提供以下信息：

1. Docker 版本：`docker --version`
2. Docker Compose 版本：`docker compose version` 或 `docker-compose --version`
3. 容器状态：`docker compose ps`
4. 容器日志：`docker compose logs --tail=100`
5. 镜像信息：`docker images | grep outlook`
6. 系统信息：`uname -a`（Linux/Mac）或 `systeminfo`（Windows）
7. 错误截图或详细错误信息

## 📚 完整使用流程示例

### 场景 1: 本地开发（使用 SQLite）

```bash
# 1. 克隆项目
git clone <repository-url>
cd OutlookManager2

# 2. 启动服务（使用默认SQLite）
docker compose up -d --build

# 3. 查看日志
docker compose logs -f

# 4. 访问服务
# 浏览器打开: http://localhost:8001
```

### 场景 2: 本地开发（使用 PostgreSQL）

```bash
# 1. 克隆项目
git clone <repository-url>
cd OutlookManager2

# 2. 创建.env文件
cat > .env << EOF
DB_TYPE=postgresql
DB_HOST=postgresql
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=mypassword123
POSTGRES_DB=outlook_manager
POSTGRES_USER=outlook_user
POSTGRES_PASSWORD=mypassword123
POSTGRES_PORT=5432
EOF

# 3. 启动PostgreSQL
docker compose up -d postgresql

# 4. 等待PostgreSQL就绪
sleep 10

# 5. 初始化数据库
docker compose exec outlook-email-api python3 scripts/init_postgresql.py

# 6. 启动所有服务
docker compose up -d --build

# 7. 访问服务
# 浏览器打开: http://localhost:8001
# 使用数据库管理工具连接: localhost:5432
```

### 场景 3: 生产环境（PostgreSQL 在远程服务器）

**A 服务器（PostgreSQL）**：

```bash
# 1. 在A服务器上部署PostgreSQL
cd /opt/outlook-postgresql
# 复制 docker/postgresql/docker-compose.yml 到A服务器
docker compose up -d

# 2. 配置防火墙
sudo ufw allow from B_SERVER_IP to any port 5432
```

**B 服务器（应用）**：

```bash
# 1. 克隆项目
git clone <repository-url>
cd OutlookManager2

# 2. 创建.env文件
cat > .env << EOF
DB_TYPE=postgresql
DB_HOST=A_SERVER_IP
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password
EOF

# 3. 启动应用
docker compose up -d --build outlook-email-api outlook-email-frontend

# 4. 初始化数据库
docker compose exec outlook-email-api python3 scripts/init_postgresql.py
```

## ⚡ 快速参考

### 常用命令速查

#### 服务管理

```bash
# 启动所有服务
docker compose up -d

# 启动特定服务
docker compose up -d outlook-email-api postgresql

# 停止服务
docker compose stop

# 重启服务
docker compose restart

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

#### 数据库操作

**SQLite**:

```bash
# 备份
cp data.db data.db.backup.$(date +%Y%m%d)

# 修复
docker compose exec outlook-email-api python3 scripts/repair_database.py
```

**PostgreSQL**:

```bash
# 连接数据库
docker compose exec postgresql psql -U outlook_user -d outlook_manager

# 备份数据库
docker compose exec postgresql pg_dump -U outlook_user outlook_manager > backup.sql

# 初始化数据库
docker compose exec outlook-email-api python3 scripts/init_postgresql.py

# 优化数据库
docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "VACUUM ANALYZE;"
```

#### 环境变量配置

**SQLite（默认）**:

```bash
# .env文件（可选，使用默认值）
DB_TYPE=sqlite
```

**PostgreSQL（Docker 网络）**:

```bash
# .env文件
DB_TYPE=postgresql
DB_HOST=postgresql
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_password
POSTGRES_PASSWORD=your_password
```

**PostgreSQL（远程）**:

```bash
# .env文件
DB_TYPE=postgresql
DB_HOST=192.168.1.100
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_password
```

### 连接信息速查

| 服务                      | 连接方式   | 地址                       | 端口 |
| ------------------------- | ---------- | -------------------------- | ---- |
| 前端界面                  | 浏览器     | http://localhost:3000      | 3000 |
| API 服务                  | 浏览器/API | http://localhost:8001      | 8001 |
| API 文档                  | 浏览器     | http://localhost:8001/docs | 8001 |
| PostgreSQL（Docker 网络） | 应用连接   | postgresql                 | 5432 |
| PostgreSQL（远程工具）    | 数据库工具 | localhost                  | 5432 |

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [PostgreSQL 部署指南](docs/POSTGRESQL_DEPLOYMENT.md) - 详细的 PostgreSQL 部署说明
- 项目 README.md
