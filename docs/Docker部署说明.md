# Docker部署说明

## 概述

本项目已完全支持Docker容器化部署，提供了完整的Dockerfile和docker-compose.yml配置文件。

## 最新更新（批量Token刷新功能）

### 新增功能
- ✅ 批量刷新Token功能
- ✅ 多维度账户筛选（邮箱、标签、刷新状态、时间范围）
- ✅ API文档界面已更新

### Docker相关文件状态
- ✅ `Dockerfile` - 无需更新（使用现有配置）
- ✅ `docker-compose.yml` - 无需更新（使用现有配置）
- ✅ `docker-entrypoint.sh` - 已创建启动脚本
- ✅ `requirements.txt` - 依赖包完整，无需添加

## 快速部署

### 使用Docker Compose（推荐）

```bash
# 1. 构建并启动容器
docker-compose up -d

# 2. 查看日志
docker-compose logs -f

# 3. 停止容器
docker-compose down
```

### 使用Dockerfile

```bash
# 1. 构建镜像
docker build -t outlook-email-manager .

# 2. 运行容器
docker run -d \
  --name outlook-email-api \
  -p 8000:8000 \
  -v $(pwd)/data.db:/app/data.db \
  -v $(pwd)/logs:/app/logs \
  outlook-email-manager

# 3. 查看日志
docker logs -f outlook-email-api

# 4. 停止容器
docker stop outlook-email-api
docker rm outlook-email-api
```

## 数据持久化

容器使用卷（volumes）持久化以下数据：

- **数据库文件**: `./data.db:/app/data.db`
  - SQLite数据库，存储所有账户和配置
  
- **日志目录**: `./logs:/app/logs`
  - 应用日志，按天轮转，保留30天

- **账户配置**（可选）: `./accounts.json:/app/accounts.json`
  - 旧版JSON配置文件，用于数据迁移

## 环境变量

可通过环境变量配置：

- `HOST`: 监听主机地址（默认: 0.0.0.0）
- `PORT`: 监听端口（默认: 8000）
- `PYTHONUNBUFFERED`: Python输出缓冲（默认: 1）
- `TZ`: 时区设置（默认: Asia/Shanghai）

**docker-compose.yml示例：**

```yaml
environment:
  - HOST=0.0.0.0
  - PORT=8000
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Shanghai
```

## 时区配置

容器已默认配置为**东8区（Asia/Shanghai）**时区，确保显示时间与中国时间一致。

### 配置说明

项目采用**双重时区配置**：

1. **Dockerfile层面**：镜像构建时设置时区
2. **docker-compose层面**：运行时挂载时区文件和环境变量

### 验证时区

```bash
# 快速验证
docker exec outlook-email-api date

# 详细验证
bash scripts/verify_timezone.sh
```

### 修改时区

如需使用其他时区，修改 `docker-compose.yml` 和 `docker/Dockerfile` 中的 `TZ` 环境变量：

- 北京时间（东8区）：`Asia/Shanghai`
- 东京时间（东9区）：`Asia/Tokyo`
- 纽约时间（西5区）：`America/New_York`
- 伦敦时间（0时区）：`Europe/London`

### 时区问题排查

如果显示时间不正确：

```bash
# 方法1: 使用自动修复脚本
bash scripts/fix_timezone.sh

# 方法2: 手动修复
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

详细文档：[时区配置指南](./时区配置指南.md)

## 健康检查

容器包含健康检查配置：

- **检查间隔**: 30秒
- **超时时间**: 10秒
- **重试次数**: 3次
- **启动等待**: 40秒
- **检查方法**: HTTP GET /api

## 网络配置

容器默认使用bridge网络：

```yaml
networks:
  outlook-network:
    driver: bridge
```

## 端口映射

- **容器端口**: 8000
- **主机端口**: 8000（可自定义）

修改主机端口：

```yaml
ports:
  - "9000:8000"  # 映射到主机的9000端口
```

## 访问应用

容器启动后，访问以下地址：

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **OpenAPI规范**: http://localhost:8000/redoc

## 默认管理员账户

首次启动时会自动创建默认管理员：

- **用户名**: admin
- **密码**: admin123

⚠️ **重要**: 首次登录后请立即修改密码！

## 更新部署

### 重新构建镜像

```bash
# 1. 停止并删除旧容器
docker-compose down

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 启动新容器
docker-compose up -d
```

### 更新代码不重新构建

如果只是更新代码，可以：

```bash
# 1. 停止容器
docker-compose stop

# 2. 更新代码（git pull或手动替换）
git pull

# 3. 重启容器
docker-compose start
```

## 故障排查

### 查看日志

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f outlook-email-api
```

### 进入容器

```bash
# Docker Compose
docker-compose exec outlook-email-client sh

# Docker
docker exec -it outlook-email-api sh
```

### 检查容器状态

```bash
# Docker Compose
docker-compose ps

# Docker
docker ps -a | grep outlook
```

### 健康检查状态

```bash
docker inspect --format='{{json .State.Health}}' outlook-email-api | jq
```

## 数据备份

### 备份数据库

```bash
# 方法1: 直接复制数据库文件
cp data.db data.db.backup.$(date +%Y%m%d)

# 方法2: 从容器中导出
docker cp outlook-email-api:/app/data.db ./backup/data.db.$(date +%Y%m%d)
```

### 恢复数据库

```bash
# 1. 停止容器
docker-compose stop

# 2. 恢复数据库文件
cp data.db.backup.20240101 data.db

# 3. 启动容器
docker-compose start
```

## 性能优化

### 资源限制

在docker-compose.yml中添加资源限制：

```yaml
services:
  outlook-email-client:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 日志轮转

日志已配置为按天轮转，保留30天，无需额外配置。

## 生产环境建议

1. **修改默认管理员密码**
2. **配置反向代理**（如Nginx）
3. **启用HTTPS**
4. **定期备份数据库**
5. **监控容器健康状态**
6. **配置日志收集**（如ELK）

## 安全注意事项

- ⚠️ 不要在公网暴露8000端口，使用反向代理
- ⚠️ 定期更新镜像和依赖包
- ⚠️ 保护好数据库文件和日志
- ⚠️ 使用强密码
- ⚠️ 定期检查安全漏洞

## 相关文件

- `Dockerfile`: Docker镜像构建文件
- `docker-compose.yml`: Docker Compose配置
- `docker-entrypoint.sh`: 容器启动脚本
- `requirements.txt`: Python依赖包列表
- `.dockerignore`: Docker构建忽略文件

## 技术支持

如遇问题，请查看：
- 应用日志: `./logs/outlook_manager.log`
- Docker日志: `docker-compose logs`
- API文档: http://localhost:8000/docs

