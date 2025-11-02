# Docker 部署更新说明

## 更新时间
2025-11-01

## 更新内容

### 1. Dockerfile 更新

#### 新增文件
在 Dockerfile 中添加了新创建的 Graph API 服务模块：

```dockerfile
COPY graph_api_service.py .
```

**位置**: 在 `oauth_service.py` 之后，`email_service.py` 之前

#### 完整的文件复制列表
```dockerfile
COPY main.py .
COPY config.py .
COPY models.py .
COPY logger_config.py .
COPY database.py .
COPY auth.py .
COPY admin_api.py .
COPY account_service.py .
COPY oauth_service.py .
COPY graph_api_service.py .          # ← 新增
COPY email_service.py .
COPY email_utils.py .
COPY imap_pool.py .
COPY cache_service.py .
COPY verification_code_detector.py .
COPY routes/ ./routes/
COPY static/ ./static/
COPY docker/docker-entrypoint.sh .
```

### 2. docker-compose.yml 检查

#### 当前配置 ✅ 无需修改
```yaml
version: "3.8"

services:
  outlook-email-client:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: outlook-email-api
    ports:
      - "8001:8000"
    volumes:
      - ./data.db:/app/data.db          # SQLite数据库持久化
      - ./logs:/app/logs                # 日志持久化
      - ./accounts.json:/app/accounts.json  # 可选：旧版JSON文件
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TZ=Asia/Shanghai
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - outlook-network
```

#### 为什么不需要修改？

1. **无需额外依赖**
   - Graph API 使用 `httpx` 库，已在 `requirements.txt` 中
   - 无需安装新的系统包或Python包

2. **无需新的环境变量**
   - Graph API 配置在 `config.py` 中硬编码
   - 使用相同的 OAuth2 认证流程
   - 无需额外的API密钥或配置

3. **数据持久化已配置**
   - `data.db` 已挂载，包含新的 `api_method` 字段
   - 日志目录已挂载
   - 无需额外的存储卷

4. **网络配置无变化**
   - Graph API 通过 HTTPS 访问微软服务器
   - 使用标准的 443 端口
   - 无需修改防火墙或网络配置

### 3. 依赖检查

#### requirements.txt ✅ 无需修改
```txt
fastapi[all]==0.115.0
httpx==0.27.0              # ← Graph API 使用此库
aioimaplib==2.0.1
pydantic[email]==2.9.0
requests==2.32.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.3
python-multipart==0.0.9
```

**说明**:
- `httpx` 已存在，用于异步HTTP请求
- Graph API 服务使用 `httpx` 调用微软 Graph API
- 无需添加新的依赖

## 部署步骤

### 首次部署或更新部署

#### 1. 停止现有容器（如果存在）
```bash
docker-compose down
```

#### 2. 重新构建镜像
```bash
docker-compose build --no-cache
```

**重要**: 使用 `--no-cache` 确保包含新文件 `graph_api_service.py`

#### 3. 启动服务
```bash
docker-compose up -d
```

#### 4. 查看日志
```bash
docker-compose logs -f
```

#### 5. 验证服务
```bash
# 检查健康状态
docker-compose ps

# 测试API
curl http://localhost:8001/api

# 检查Graph API模块
docker-compose exec outlook-email-client python -c "import graph_api_service; print('✓ Graph API module loaded')"
```

### 数据库迁移

#### 自动迁移
容器启动时会自动执行数据库迁移：
```python
# database.py 中的 init_database() 会自动添加 api_method 字段
ALTER TABLE accounts ADD COLUMN api_method TEXT DEFAULT 'imap'
```

#### 验证迁移
```bash
# 进入容器
docker-compose exec outlook-email-client sh

# 检查数据库
python -c "
import sqlite3
conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(accounts)')
columns = [col[1] for col in cursor.fetchall()]
print('api_method' in columns and '✓ Migration successful' or '✗ Migration failed')
conn.close()
"
```

## 配置说明

### Graph API 相关配置

所有 Graph API 配置在 `config.py` 中：

```python
# OAuth2配置
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
OAUTH_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
```

**无需在 docker-compose.yml 中配置环境变量**

### 可选的环境变量（未来扩展）

如果需要自定义配置，可以添加：

```yaml
environment:
  # 现有配置
  - PYTHONUNBUFFERED=1
  - HOST=0.0.0.0
  - PORT=8000
  - TZ=Asia/Shanghai
  
  # 可选：Graph API配置（当前不需要）
  # - GRAPH_API_TIMEOUT=30
  # - GRAPH_API_RETRY=3
```

## 网络要求

### 出站连接
容器需要访问以下微软服务：

1. **OAuth2 认证**
   - `login.microsoftonline.com` (443)
   
2. **Graph API**
   - `graph.microsoft.com` (443)
   
3. **IMAP（备用）**
   - `outlook.office365.com` (993)

### 防火墙配置
确保容器可以访问以上域名和端口。大多数环境默认允许出站 HTTPS 连接。

## 故障排查

### 问题1: graph_api_service 模块未找到

**症状**:
```
ModuleNotFoundError: No module named 'graph_api_service'
```

**解决方案**:
```bash
# 重新构建镜像（不使用缓存）
docker-compose build --no-cache
docker-compose up -d
```

### 问题2: Graph API 调用失败

**症状**:
```
HTTP error fetching emails via Graph API
```

**检查步骤**:
1. 检查网络连接
   ```bash
   docker-compose exec outlook-email-client ping -c 3 graph.microsoft.com
   ```

2. 检查账户权限
   ```bash
   # 调用API检测端点
   curl -X POST http://localhost:8001/accounts/{email}/detect-api-method \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. 查看详细日志
   ```bash
   docker-compose logs -f | grep -i "graph"
   ```

### 问题3: 数据库迁移未执行

**症状**:
```
no such column: api_method
```

**解决方案**:
```bash
# 进入容器手动执行迁移
docker-compose exec outlook-email-client python -c "
import database
database.init_database()
print('Migration completed')
"

# 重启容器
docker-compose restart
```

## 性能优化

### 1. 容器资源限制（可选）

```yaml
services:
  outlook-email-client:
    # ... 现有配置 ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 2. 日志轮转

日志已配置30天保留期，Docker会自动管理日志大小：

```yaml
services:
  outlook-email-client:
    # ... 现有配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 监控建议

### 健康检查
容器已配置健康检查：
```bash
# 查看健康状态
docker-compose ps

# 查看健康检查日志
docker inspect outlook-email-api | grep -A 10 Health
```

### 性能监控
```bash
# 查看容器资源使用
docker stats outlook-email-api

# 查看API响应时间
curl -w "@-" -o /dev/null -s http://localhost:8001/api <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
      time_redirect:  %{time_redirect}\n
   time_pretransfer:  %{time_pretransfer}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

## 更新清单

- [x] Dockerfile 添加 graph_api_service.py
- [x] 验证 requirements.txt 包含所需依赖
- [x] 确认 docker-compose.yml 配置正确
- [x] 测试容器构建
- [x] 验证数据库迁移
- [x] 创建部署文档

## 相关文档

- [Graph API 集成文档](GRAPH_API_INTEGRATION.md)
- [实施总结](IMPLEMENTATION_SUMMARY.md)
- [Docker部署说明](docs/Docker部署说明.md)

## 总结

✅ **Docker 配置已更新完成**

- Dockerfile 添加了 `graph_api_service.py`
- docker-compose.yml 无需修改（配置已足够）
- 依赖无需更新（httpx 已存在）
- 数据库迁移自动执行
- 网络配置无需更改

只需重新构建镜像即可部署 Graph API 功能！

```bash
docker-compose build --no-cache && docker-compose up -d
```

