# Outlook 邮件管理系统

基于 **FastAPI + Next.js** 的 Outlook 邮件管理系统。

如果你只是想先把仓库跑起来，**先走本地 Docker Compose 栈**。
远程 PostgreSQL / 只跑后端属于高级模式，放到后面单独说明。

## 推荐路径：先用本地 Docker Compose 栈跑起来

这是默认主路径。
适合本地联调、日常使用、以及第一次接手仓库时快速确认服务面。

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

## 高级模式：远程 PostgreSQL / 只跑后端

只有在下面这些场景再走这条路：

- 你已经有现成远程 PostgreSQL
- 你只想单独启动 Python 后端
- 你明确知道自己不需要本地 PostgreSQL 容器

高级模式入口文档：

- `docs/LOCAL_DEVELOPMENT.md`

高级模式使用的配置模板是：

- `.env.remote-db.example`

## 两种模式不要混用

- 本地 compose 模式：`.env.compose.example` → `.env.compose.local`
- 远程 PostgreSQL 模式：`.env.remote-db.example` → `.env`

最常见问题不是服务本身坏了，而是把两套配置交叉复制了。

## FAQ

### 为什么之前会出现数据库密码串用

因为仓库早期只有一套 `.env` 语义，容易出现：

- 主机走本地 compose：`DB_HOST=postgresql`
- 密码却还是远程库那套

现在已经拆成两套示例文件：

- `.env.compose.example`
- `.env.remote-db.example`

按对应模式使用即可，不要交叉复制。

## 相关文档

- `README_DOCKER.md`：本地 compose 栈运维命令
- `docs/LOCAL_DEVELOPMENT.md`：远程 PostgreSQL / 只跑后端高级模式
