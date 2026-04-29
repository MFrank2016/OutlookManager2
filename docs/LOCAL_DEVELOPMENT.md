# 本地开发配置指南（高级模式）

> 这是 **高级模式**。
> 只在以下场景使用：
>
> - 你要连接 **远程 PostgreSQL**
> - 你只想 **只跑后端**，不启动本地 Docker Compose 全栈
>
> 如果你只是想尽快跑起来，请先回到仓库根目录 `README.md`，按本地 Docker Compose 主路径操作。

## 适用前提

1. 你已安装 Python 3.8+
2. 你可以直接访问目标 PostgreSQL
3. 你明确知道这里使用的是 `.env`，而不是 `.env.compose.local`

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 创建远程数据库模式配置

```bash
cp .env.remote-db.example .env
```

> `.env.remote-db.example` 是这条高级模式的权威模板。
> 本文档不适用于本地 compose 栈。

## 3. 填写远程 PostgreSQL 连接信息

```bash
DB_TYPE=postgresql
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_remote_password_here

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30
```

## 4. 启动后端

```bash
python main.py
```

默认访问地址：`http://127.0.0.1:8000`

## 5. 验活

```bash
curl http://127.0.0.1:8000/healthz
```

## 场景边界

### 什么时候用这份文档

- 远程 PostgreSQL 联调
- 只跑后端接口
- 不想启动本地 PostgreSQL 容器

### 什么时候不要用这份文档

- 你要本地一次起 API + Frontend + PostgreSQL
- 你只是第一次使用这个仓库
- 你只想照抄最短命令尽快看到页面

这些情况都应改看 `README.md`。

## 相关文档

- 首次启动：`README.md`
- Compose 运维：`README_DOCKER.md`
- 远程库模板：`.env.remote-db.example`
