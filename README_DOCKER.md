# Docker 运维手册

> 首次启动请先看 README.md。
> 这份文档只负责 **本地 Docker Compose 栈** 的日常运维，不再重复首启流程。

## 适用范围

- 你已经按 `README.md` 完成过首次启动
- 当前栈使用 `.env.compose.local`
- 你要做的是查看状态、看日志、重建、重启、清理或进入容器

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看所有服务日志
docker compose logs -f

# 查看 API 日志
docker compose logs -f outlook-email-api

# 查看 Frontend 日志
docker compose logs -f outlook-email-frontend

# 查看 PostgreSQL 日志
docker compose logs -f postgresql

# 停止服务
docker compose stop

# 启动已存在容器
docker compose --env-file .env.compose.local up -d

# 重启所有服务
docker compose restart

# 重新构建并启动
docker compose --env-file .env.compose.local up -d --build

# 强制重新构建后启动
docker compose --env-file .env.compose.local build --no-cache
docker compose --env-file .env.compose.local up -d

# 停止并移除容器
docker compose down
```

## 验活命令

```bash
# 容器状态
docker compose ps

# API 健康检查
curl http://127.0.0.1:8000/healthz

# Frontend 首页
curl -I http://127.0.0.1:3000
```

## 常见运维场景

### 仅重启 API

```bash
docker compose restart outlook-email-api
```

### 进入 API 容器

```bash
docker compose exec outlook-email-api /bin/sh
```

### 进入 PostgreSQL 容器

```bash
docker compose exec postgresql /bin/sh
```

### 清理并重新拉起本地栈

```bash
docker compose down
docker compose --env-file .env.compose.local up -d --build
```

## 排障入口

- 首次启动不会用：回到 `README.md`
- 需要远程 PostgreSQL / 只跑后端：看 `docs/LOCAL_DEVELOPMENT.md`
- 需要理解旧 `.env` / 旧 Docker 模板：看 `docker/docker.env.example` 顶部说明
