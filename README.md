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

最快启动方式：

```bash
./scripts/compose-up.sh
```

这个脚本会执行 `docker compose --env-file .env.compose.local up -d --build`，并自动检查容器状态、API `/healthz` 和 Frontend 首页。

如果你想手动执行，再用下面这组备用命令：

```bash
docker compose --env-file .env.compose.local up -d --build
docker compose ps
curl http://127.0.0.1:8000/healthz
```

### 3. 默认入口


- Frontend: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8000`
- PostgreSQL(host): `127.0.0.1:55432`

### 4. 遇到问题先看这里

```bash
docker compose ps
docker compose logs -f outlook-email-api
docker compose logs -f outlook-email-frontend
docker compose logs -f postgresql
```

### 5. 常用运维命令

```bash
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

## Microsoft Access Layer / API v2 快速入口

`OutlookManager2` 现在已经提供一套面向 Microsoft Access Layer 的 `/api/v2` 契约。

推荐优先使用这些入口：

- `POST /api/v2/accounts/probe`
- `GET /api/v2/accounts/{email}/health`
- `GET /api/v2/accounts/{email}/delivery-strategy`
- `GET /api/v2/accounts/{email}/messages`
- `POST /api/v2/accounts/import?mode=dry_run`

### 快速示例

预检单个账户：

```bash
curl -X POST http://127.0.0.1:8000/api/v2/accounts/probe \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "refresh_token": "refresh-token",
    "client_id": "client-id",
    "strategy_mode": "auto"
  }'
```

查看健康状态：

```bash
curl http://127.0.0.1:8000/api/v2/accounts/user%40example.com/health
```

解释当前投递策略：

```bash
curl "http://127.0.0.1:8000/api/v2/accounts/user%40example.com/delivery-strategy?override_provider=graph&skip_cache=true"
```

批量导入先 dry run：

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/accounts/import?mode=dry_run" \
  -H 'Content-Type: application/json' \
  -d '{
    "api_method": "imap",
    "tags": ["seed"],
    "items": [
      {
        "email": "user@example.com",
        "refresh_token": "refresh-token",
        "client_id": "client-id"
      }
    ]
  }'
```

## v1 兼容期说明

当前 `/accounts`、`/emails` 等 v1 路由仍可继续使用，但它们已经进入兼容层。

- 响应头会返回 `Deprecation: true`
- 响应头会返回 `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`

新接入调用方、自动化脚本、前端新功能，默认都应优先走 `/api/v2`。

更详细的迁移说明见：

- `docs/runbooks/2026-04-30-microsoft-access-v2-migration.md`
