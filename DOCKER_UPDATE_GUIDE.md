# Docker 文档桥接说明

这份文档不再维护一整套独立的首启流程。
当前仓库的 Docker / 部署说明已经按“单一事实来源”收敛，请按场景跳转：

## 你只是第一次想跑起来

请看 `README.md`。

那里是唯一主入口，包含：

- `.env.compose.example` → `.env.compose.local`
- `docker compose --env-file .env.compose.local up -d --build`
- `docker compose ps`
- `curl http://127.0.0.1:8000/healthz`

## 你已经跑起来，现在要做 compose 运维

请看 `README_DOCKER.md`。

那里只保留本地 Docker Compose 栈的运维内容，例如：

- 查看日志
- 重启服务
- 重建镜像
- 重新拉起容器
- 进入 API / PostgreSQL 容器

## 你要远程 PostgreSQL 或只跑后端

请看 `docs/LOCAL_DEVELOPMENT.md`。

那里是高级模式文档，使用 `.env.remote-db.example` 作为模板。

## 历史兼容说明

- `docker/docker.env.example` 仍然保留，但仅用于历史兼容说明
- 当前 compose 主路径以 `.env.compose.local` 为准
- 当前远程 PostgreSQL / 只跑后端路径以 `.env.remote-db.example` 为准
