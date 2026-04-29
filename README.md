# Outlook 邮件管理系统

基于 **FastAPI + Next.js** 的 Outlook 邮件管理系统，当前仓库有两种常用启动方式：

1. **本地 Docker Compose 栈**
   API、Frontend、PostgreSQL 一起起，适合本地联调和日常使用。
2. **直接运行 Python + 远程 PostgreSQL**
   适合你已经有现成远程数据库，只想单独启动后端服务。

> **最重要的一点：不要混用两套配置。**
> 本地 compose 模式用 `.env.compose.example`；远程数据库模式用 `.env.remote-db.example`。

## 方式一：本地 Docker Compose 栈

推荐日常优先使用这套。

### 1. 准备配置文件

```bash
cp .env.compose.example .env.compose.local
```

### 2. 启动服务

```bash
docker compose --env-file .env.compose.local up -d --build
```

### 3. 验证服务

```bash
docker compose ps
curl http://127.0.0.1:8000/healthz
```

默认入口：

- Frontend: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8000`
- PostgreSQL(host): `127.0.0.1:55432`

### 4. 常用运维命令

```bash
# 查看日志
docker compose logs -f outlook-email-api
docker compose logs -f outlook-email-frontend

# 重建并重启
docker compose --env-file .env.compose.local up -d --build

# 停止
docker compose down
```

## 方式二：直接运行 Python + 远程 PostgreSQL

这套只启动后端，不起本地 PostgreSQL 容器。

### 1. 准备配置文件

```bash
cp .env.remote-db.example .env
```

然后把下面这些值改成你的远程库：

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### 2. 安装依赖并启动

```bash
pip install -r requirements.txt
python main.py
```

### 3. 验证服务

```bash
curl http://127.0.0.1:8000/healthz
```

## 为什么之前会出现数据库密码串用

因为仓库里曾经只有一套 `.env` 语义，很容易出现：

- **主机走本地 compose**：`DB_HOST=postgresql`
- **密码却还是远程库那套**

现在已经拆成两套示例文件：

- `.env.compose.example`
- `.env.remote-db.example`

按对应模式使用即可，不要交叉复制。

## 相关文档

- `README_DOCKER.md`：本地 compose 栈常用命令
- `docs/LOCAL_DEVELOPMENT.md`：远程 PostgreSQL 模式详细说明
