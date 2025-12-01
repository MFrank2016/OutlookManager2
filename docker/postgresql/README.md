# PostgreSQL Docker配置说明

## 功能特性

- ✅ 支持Docker网络连接（本地应用通过容器名连接）
- ✅ 支持远程连接（开放端口供数据库管理工具使用）
- ✅ 数据持久化（使用Docker卷）
- ✅ 健康检查
- ✅ 性能优化配置

## 使用方法

### 1. 配置环境变量

创建 `.env` 文件：

```bash
POSTGRES_DB=outlook_manager
POSTGRES_USER=outlook_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_PORT=5432
TZ=Asia/Shanghai
```

### 2. 启动PostgreSQL

```bash
docker-compose up -d
```

### 3. 连接方式

#### 方式1: Docker网络连接（本地应用）

如果应用也在Docker网络中，使用容器名连接：

```python
# 在应用的.env或配置中
DB_HOST=postgresql  # 使用容器名
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password_here
```

#### 方式2: 远程连接（数据库管理工具）

使用主机的IP地址和映射的端口：

```
主机: localhost 或 服务器IP
端口: 5432（或你在.env中设置的POSTGRES_PORT）
数据库: outlook_manager
用户名: outlook_user
密码: your_strong_password_here
```

**常用数据库管理工具连接示例**：

- **DBeaver**: 
  - Host: `localhost` 或服务器IP
  - Port: `5432`
  - Database: `outlook_manager`
  - Username: `outlook_user`
  - Password: `your_strong_password_here`

- **pgAdmin**: 
  - 创建新服务器连接
  - Host: `localhost` 或服务器IP
  - Port: `5432`
  - Database: `outlook_manager`
  - Username: `outlook_user`
  - Password: `your_strong_password_here`

- **DataGrip**:
  - Host: `localhost` 或服务器IP
  - Port: `5432`
  - Database: `outlook_manager`
  - User: `outlook_user`
  - Password: `your_strong_password_here`

### 4. 配置远程访问（可选）

如果需要从其他服务器访问，需要：

1. **配置防火墙**（在A服务器上）：
```bash
# 允许特定IP访问
sudo ufw allow from REMOTE_IP to any port 5432

# 或允许所有IP（不推荐，仅用于测试）
sudo ufw allow 5432/tcp
```

2. **配置PostgreSQL访问控制**（如果需要更精细的控制）：
```bash
# 进入容器
docker-compose exec postgresql sh

# 编辑pg_hba.conf
echo "host    all    all    REMOTE_IP/32    md5" >> /var/lib/postgresql/data/pg_hba.conf

# 重启PostgreSQL
exit
docker-compose restart postgresql
```

## 网络配置说明

### Docker网络

PostgreSQL容器连接到 `postgres-network` 网络。如果应用也在同一网络中，可以使用容器名 `postgresql` 作为主机名连接。

### 端口映射

- **容器内端口**: 5432（PostgreSQL默认端口）
- **主机端口**: 可通过 `POSTGRES_PORT` 环境变量配置（默认5432）
- **格式**: `主机端口:容器端口`

### 连接示例

#### 从Docker网络内的应用连接

```python
# 使用容器名
DB_HOST = "postgresql"
DB_PORT = 5432
```

#### 从主机或其他服务器连接

```python
# 使用主机IP或localhost
DB_HOST = "localhost"  # 或服务器IP
DB_PORT = 5432
```

## 安全建议

1. **使用强密码**: 确保 `POSTGRES_PASSWORD` 足够复杂
2. **限制远程访问**: 在生产环境中，使用防火墙限制访问IP
3. **使用SSL**: 生产环境建议启用SSL连接
4. **定期备份**: 设置自动备份策略

## 故障排查

### 问题1: 无法从远程连接

**检查步骤**:
1. 确认端口映射正确: `docker-compose ps`
2. 检查防火墙设置
3. 确认PostgreSQL正在监听所有接口: `docker-compose exec postgresql netstat -tlnp | grep 5432`
4. 检查pg_hba.conf配置

### 问题2: Docker网络内无法连接

**检查步骤**:
1. 确认应用和PostgreSQL在同一Docker网络中
2. 使用容器名 `postgresql` 作为主机名
3. 检查网络配置: `docker network inspect outlook-postgres-network`

## 相关文件

- `docker-compose.yml` - Docker Compose配置
- `init.sql` - 数据库初始化脚本
- `postgresql.conf` - PostgreSQL配置文件（可选）
- `.env` - 环境变量配置（需要创建）

