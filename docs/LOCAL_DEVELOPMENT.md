# 本地开发配置指南

本文档说明如何在本地使用 `python main.py` 启动后端服务，并连接到远程 PostgreSQL 数据库。

## 前置要求

1. Python 3.8+
2. 已安装项目依赖：`pip install -r requirements.txt`
3. 远程 PostgreSQL 数据库已部署并可访问

## 配置步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建环境变量文件

复制示例配置文件：

```bash
cp .env.example .env
```

### 3. 配置数据库连接

编辑 `.env` 文件，配置远程 PostgreSQL 连接信息：

```bash
# 数据库类型
DB_TYPE=postgresql

# 远程PostgreSQL连接配置
DB_HOST=192.168.1.100          # 远程服务器IP地址
DB_PORT=5432                   # PostgreSQL端口（默认5432）
DB_NAME=outlook_manager         # 数据库名
DB_USER=outlook_user           # 数据库用户名
DB_PASSWORD=your_password_here # 数据库密码

# 连接池配置（可选）
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30
```

### 4. 验证网络连接

确保本地可以访问远程 PostgreSQL 服务器：

```bash
# 测试端口是否开放
telnet 192.168.1.100 5432

# 或使用 PowerShell (Windows)
Test-NetConnection -ComputerName 192.168.1.100 -Port 5432
```

### 5. 测试数据库连接

使用 Python 脚本测试连接：

```python
# test_db_connection.py
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    print("✅ 数据库连接成功！")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(f"PostgreSQL 版本: {cursor.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
```

运行测试：

```bash
python test_db_connection.py
```

### 6. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 配置说明

### 环境变量优先级

配置按以下优先级加载：

1. **系统环境变量**（最高优先级）
2. **`.env` 文件**（项目根目录）
3. **默认值**（`config.py` 中定义）

### 数据库类型切换

#### 使用 SQLite（本地文件数据库）

```bash
# .env 文件
DB_TYPE=sqlite
# 或删除 DB_TYPE 配置，使用默认值
```

#### 使用远程 PostgreSQL

```bash
# .env 文件
DB_TYPE=postgresql
DB_HOST=192.168.1.100
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_password
```

#### 使用 Docker 中的 PostgreSQL（本地）

如果 PostgreSQL 在 Docker 中运行，且端口已映射到主机：

```bash
# .env 文件
DB_TYPE=postgresql
DB_HOST=localhost          # 使用 localhost
DB_PORT=5432
DB_NAME=outlook_manager
DB_USER=outlook_user
DB_PASSWORD=your_password
```

## 常见问题

### 1. 连接超时

**问题**：`psycopg2.OperationalError: timeout expired`

**解决方案**：
- 检查防火墙设置，确保 5432 端口已开放
- 检查 PostgreSQL 的 `pg_hba.conf` 配置，允许远程连接
- 检查 PostgreSQL 的 `postgresql.conf`，确保 `listen_addresses = '*'`

### 2. 认证失败

**问题**：`psycopg2.OperationalError: password authentication failed`

**解决方案**：
- 检查 `.env` 文件中的 `DB_PASSWORD` 是否正确
- 检查 PostgreSQL 用户是否存在且有权限访问数据库

### 3. 数据库不存在

**问题**：`psycopg2.OperationalError: database "outlook_manager" does not exist`

**解决方案**：
- 在远程 PostgreSQL 服务器上创建数据库：
  ```sql
  CREATE DATABASE outlook_manager;
  ```
- 或修改 `.env` 文件中的 `DB_NAME` 为已存在的数据库名

### 4. 找不到 .env 文件

**问题**：配置未生效，使用默认值

**解决方案**：
- 确保 `.env` 文件在项目根目录
- 检查文件名是否正确（注意前面的点）
- 确保已安装 `python-dotenv`：`pip install python-dotenv`

## 安全建议

1. **不要提交 `.env` 文件到 Git**
   - `.env` 文件已添加到 `.gitignore`
   - 使用 `.env.example` 作为模板

2. **使用强密码**
   - PostgreSQL 密码应足够复杂
   - 定期更换密码

3. **限制网络访问**
   - 如果可能，使用 VPN 或 SSH 隧道
   - 配置防火墙只允许特定 IP 访问

4. **使用 SSL 连接**（可选）
   - 生产环境建议启用 PostgreSQL SSL 连接
   - 需要配置 SSL 证书

## 相关文档

- [PostgreSQL 部署指南](POSTGRESQL_DEPLOYMENT.md)
- [Docker 部署指南](../DOCKER_UPDATE_GUIDE.md)
- [项目 README](../README.md)

