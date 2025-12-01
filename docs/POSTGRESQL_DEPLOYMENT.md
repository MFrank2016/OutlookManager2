# PostgreSQL部署指南

本文档说明如何在A服务器上部署PostgreSQL数据库，在B服务器上部署应用并连接到PostgreSQL。

## 前提条件

- A服务器：已安装Docker和Docker Compose
- B服务器：已安装Docker和Docker Compose（或Python环境）
- 网络：B服务器可以通过公网IP访问A服务器的PostgreSQL端口（5432）

## 阶段1: 在A服务器上部署PostgreSQL

### 1.1 准备配置文件

在A服务器上创建PostgreSQL配置目录：

```bash
mkdir -p /opt/outlook-postgresql
cd /opt/outlook-postgresql
```

### 1.2 创建docker-compose.yml

复制项目中的 `docker/postgresql/docker-compose.yml` 到A服务器：

```bash
# 从项目目录复制
scp docker/postgresql/docker-compose.yml user@server-a:/opt/outlook-postgresql/
```

### 1.3 创建环境变量文件

创建 `.env` 文件：

```bash
cat > .env << EOF
POSTGRES_DB=outlook_manager
POSTGRES_USER=outlook_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_PORT=5432
TZ=Asia/Shanghai
EOF
```

**重要**: 修改 `POSTGRES_PASSWORD` 为强密码！

### 1.4 启动PostgreSQL

```bash
docker-compose up -d
```

### 1.5 验证PostgreSQL运行状态

```bash
# 检查容器状态
docker-compose ps

# 检查日志
docker-compose logs postgresql

# 测试连接
docker-compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT version();"
```

### 1.6 配置防火墙（重要）

PostgreSQL已配置为监听所有接口（`listen_addresses='*'`），现在需要配置防火墙允许访问：

#### 允许特定IP访问（推荐）

```bash
# 如果使用ufw
sudo ufw allow from B_SERVER_IP to any port 5432

# 如果使用firewalld
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='B_SERVER_IP' port port='5432' protocol='tcp' accept"
sudo firewall-cmd --reload
```

#### 允许所有IP访问（仅用于测试，不推荐生产环境）

```bash
# 如果使用ufw
sudo ufw allow 5432/tcp

# 如果使用firewalld
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

### 1.7 配置PostgreSQL访问控制（可选）

PostgreSQL默认配置允许所有连接。如果需要更精细的控制，可以编辑 `pg_hba.conf`：

```bash
# 进入容器
docker-compose exec postgresql sh

# 查看当前pg_hba.conf配置
cat /var/lib/postgresql/data/pg_hba.conf

# 如果需要限制访问，编辑pg_hba.conf
# 注意：PostgreSQL容器启动时会自动配置基本的访问规则
# 如果需要自定义，可以在容器启动后修改

# 重启PostgreSQL使配置生效
exit
docker-compose restart postgresql
```

**注意**: PostgreSQL Docker镜像默认配置允许所有连接。如果需要限制访问，建议：
1. 使用防火墙限制访问IP（推荐）
2. 或修改pg_hba.conf文件（需要挂载自定义配置）

## 阶段2: 在B服务器上部署应用

### 2.1 准备应用代码

在B服务器上克隆或复制项目代码：

```bash
git clone <your-repo-url>
cd OutlookManager2
```

### 2.2 配置环境变量

创建 `.env` 文件或设置环境变量：

#### 方式1: 使用Docker网络连接（推荐，如果应用也在Docker中）

```bash
cat > .env << EOF
# 数据库配置 - 使用Docker网络
DB_TYPE=postgresql
DB_HOST=postgresql  # 使用容器名，通过Docker网络连接
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password_here

# 连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30

# 应用配置
HOST=0.0.0.0
PORT=8000
TZ=Asia/Shanghai
EOF
```

#### 方式2: 使用远程连接（如果应用不在Docker中或在不同服务器）

```bash
cat > .env << EOF
# 数据库配置 - 使用远程连接
DB_TYPE=postgresql
DB_HOST=A_SERVER_IP  # 使用A服务器的IP地址
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_strong_password_here

# 连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30

# 应用配置
HOST=0.0.0.0
PORT=8000
TZ=Asia/Shanghai
EOF
```

**重要**: 
- **Docker网络连接**: 如果应用也在Docker中，使用容器名 `postgresql` 作为 `DB_HOST`
- **远程连接**: 如果应用不在Docker中，使用A服务器的公网IP作为 `DB_HOST`
- 将 `DB_PASSWORD` 替换为在A服务器上设置的密码

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2.4 初始化数据库

运行初始化脚本创建表和索引：

```bash
python3 scripts/init_postgresql.py
```

### 2.5 启动应用

#### 方式1: 使用Docker Compose

```bash
# 修改docker-compose.yml中的环境变量，或使用.env文件
docker-compose up -d
```

#### 方式2: 直接运行Python

```bash
python3 main.py
```

### 2.6 验证应用运行

```bash
# 检查API状态
curl http://localhost:8000/api

# 检查数据库连接
curl http://localhost:8000/admin/tables
```

## 连接方式说明

### Docker网络连接（本地应用）

如果应用也在Docker网络中（使用docker-compose），可以通过容器名连接：

```python
# 在应用的.env或配置中
DB_HOST=postgresql  # 使用容器名
DB_PORT=5432
```

**优势**:
- 不需要经过网络层，性能更好
- 更安全（不暴露到公网）
- 自动DNS解析

### 远程连接（数据库管理工具）

使用主机的IP地址和映射的端口连接：

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

- **Navicat**:
  - 连接类型: PostgreSQL
  - 主机: `localhost` 或服务器IP
  - 端口: `5432`
  - 数据库: `outlook_manager`
  - 用户名: `outlook_user`
  - 密码: `your_strong_password_here`

## 数据库索引说明

PostgreSQL数据库已根据最佳实践创建了以下类型的索引：

### B-tree索引
- 主键和唯一约束自动创建
- 常用查询列的单列索引
- 关联列的索引（无外键约束）

### 复合索引
- `emails_cache(email_account, folder, date)` - 多列查询优化
- `emails_cache(email_account, date DESC)` - 排序优化

### 部分索引
- 仅索引未读邮件（减少索引大小）
- 仅索引待刷新账户

### GIN索引
- JSONB字段（tags, bound_accounts, permissions）的全文搜索优化

### 表达式索引
- 不区分大小写的邮箱搜索
- 日期范围查询优化

### 覆盖索引
- 使用INCLUDE子句避免回表查询

## 性能优化建议

### 1. 定期维护

```bash
# 在A服务器上执行
docker-compose exec postgresql psql -U outlook_user -d outlook_manager -c "VACUUM ANALYZE;"
```

### 2. 监控慢查询

在PostgreSQL配置中启用慢查询日志：

```sql
-- 在PostgreSQL中执行
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 记录超过1秒的查询
SELECT pg_reload_conf();
```

### 3. 连接池配置

根据实际负载调整连接池大小：

```bash
# 在B服务器的.env文件中
DB_POOL_SIZE=10        # 增加最小连接数
DB_MAX_OVERFLOW=20     # 增加最大连接数
```

## 故障排查

### 问题1: 无法连接到PostgreSQL

#### Docker网络连接问题

**检查步骤**:
1. 确认应用和PostgreSQL在同一Docker网络中: `docker network inspect outlook-network`
2. 检查PostgreSQL容器是否运行: `docker-compose ps`
3. 测试容器间连接: `docker-compose exec outlook-email-api ping postgresql`

**解决方案**:
```bash
# 检查网络配置
docker network ls
docker network inspect outlook-network

# 确认容器在同一网络
docker inspect outlook-postgresql | grep NetworkMode
docker inspect outlook-email-api | grep NetworkMode
```

#### 远程连接问题

**检查步骤**:
1. 检查A服务器防火墙是否允许5432端口
2. 检查PostgreSQL容器是否运行: `docker-compose ps`
3. 检查PostgreSQL日志: `docker-compose logs postgresql`
4. 测试网络连接: `telnet A_SERVER_IP 5432`
5. 确认PostgreSQL正在监听所有接口: `docker-compose exec postgresql netstat -tlnp | grep 5432`

**解决方案**:
```bash
# 在A服务器上检查端口监听
sudo netstat -tlnp | grep 5432

# 检查PostgreSQL是否监听所有接口
docker-compose exec postgresql psql -U outlook_user -d outlook_manager -c "SHOW listen_addresses;"
# 应该显示: *

# 检查PostgreSQL配置
docker-compose exec postgresql cat /var/lib/postgresql/data/pg_hba.conf
```

### 问题2: 认证失败

**检查步骤**:
1. 验证用户名和密码是否正确
2. 检查pg_hba.conf配置
3. 检查环境变量是否正确设置

**解决方案**:
```bash
# 在A服务器上重置密码
docker-compose exec postgresql psql -U postgres -c "ALTER USER outlook_user WITH PASSWORD 'new_password';"
```

### 问题3: 表不存在

**解决方案**:
```bash
# 在B服务器上重新初始化数据库
python3 scripts/init_postgresql.py
```

### 问题4: 性能问题

**检查步骤**:
1. 检查索引是否创建: `\di` 在psql中
2. 检查表统计信息: `ANALYZE;`
3. 检查慢查询日志

**解决方案**:
```bash
# 重新分析表统计信息
docker-compose exec postgresql psql -U outlook_user -d outlook_manager -c "ANALYZE;"

# 重建索引（如果需要）
docker-compose exec postgresql psql -U outlook_user -d outlook_manager -c "REINDEX DATABASE outlook_manager;"
```

## 安全建议

1. **使用强密码**: 确保PostgreSQL密码足够复杂
2. **限制访问IP**: 在pg_hba.conf中只允许B服务器IP访问
3. **使用SSL连接**: 生产环境建议启用SSL
4. **定期备份**: 设置自动备份策略
5. **监控日志**: 定期检查PostgreSQL日志

## 备份和恢复

### 备份数据库

```bash
# 在A服务器上
docker-compose exec postgresql pg_dump -U outlook_user outlook_manager > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
# 在A服务器上
docker-compose exec -T postgresql psql -U outlook_user outlook_manager < backup_20250101.sql
```

## 相关文件

- `docker/postgresql/docker-compose.yml` - PostgreSQL Docker配置
- `database/postgresql_schema.sql` - 数据库表结构
- `database/postgresql_indexes.sql` - 数据库索引定义
- `scripts/init_postgresql.py` - 数据库初始化脚本
- `config.py` - 数据库连接配置

## 注意事项

1. **不使用外键约束**: 数据库设计中没有使用外键约束，数据一致性在应用层维护
2. **JSON字段**: tags、bound_accounts、permissions等字段使用JSONB类型
3. **时区设置**: 确保A和B服务器时区一致（建议使用Asia/Shanghai）
4. **网络延迟**: 跨服务器访问可能增加延迟，建议使用连接池

## 更新日志

- 2025-12-01: 初始版本，支持PostgreSQL部署和索引优化

