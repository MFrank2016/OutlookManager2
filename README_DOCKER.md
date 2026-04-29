# Docker 快速部署指南

## 🚀 一键启动

```bash
# 1. 准备本地 compose 配置
cp .env.compose.example .env.compose.local

# 2. 启动服务
docker compose --env-file .env.compose.local up -d --build

# 3. 查看日志
docker compose logs -f
```

> 不要直接复用远程数据库模式的 `.env`。
> 本地 compose 栈只使用 `.env.compose.local`（由 `.env.compose.example` 复制而来）。

## 📝 常用命令

```bash
# 启动服务
docker compose --env-file .env.compose.local up -d

# 停止服务
docker compose stop

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 进入容器
docker compose exec outlook-email-api /bin/sh

# 更新代码（重新构建）
docker compose down
docker compose --env-file .env.compose.local build --no-cache
docker compose --env-file .env.compose.local up -d
```

## 🔧 配置说明

- API 端口：`8000`（由 `.env.compose.local` 中的 `PORT` 控制）
- Frontend 端口：`3000`
- PostgreSQL 主机端口：`55432`
- 日志目录：`./logs`
- 时区：Asia/Shanghai
- PostgreSQL 容器账户默认来自：
  - `POSTGRES_DB`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`

详细配置请参考 [DOCKER_UPDATE_GUIDE.md](./DOCKER_UPDATE_GUIDE.md)
