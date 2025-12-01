# Docker 快速部署指南

## 🚀 一键启动

```bash
# 1. 配置环境变量（可选）
cp docker/docker.env.example .env

# 2. 启动服务
docker compose up -d --build

# 3. 查看日志
docker compose logs -f
```

## 📝 常用命令

```bash
# 启动服务
docker compose up -d

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
docker compose build --no-cache
docker compose up -d
```

## 🔧 配置说明

- 默认端口：8001（可在 `.env` 文件中修改）
- 数据库文件：`./data.db`（自动创建）
- 日志目录：`./logs`
- 时区：Asia/Shanghai

详细配置请参考 [DOCKER_UPDATE_GUIDE.md](./DOCKER_UPDATE_GUIDE.md)

