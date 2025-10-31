# 📧 Outlook邮件管理系统

<div align="center">

**基于FastAPI和现代Web技术的企业级Outlook邮件管理系统**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [部署指南](#-部署指南) • [API文档](#-api文档) • [开发指南](#-开发指南)

</div>

---

## 📖 项目简介

Outlook邮件管理系统是一个功能强大、易于使用的企业级邮件管理平台，支持多账户管理、智能筛选、批量操作和完整的RESTful API。系统采用现代化的技术栈，提供优秀的性能和用户体验。

### 🎯 核心优势

- **🚀 高性能**: IMAP连接池、智能缓存、异步处理
- **🔒 安全可靠**: OAuth2认证、JWT Token、完整的权限控制
- **📊 功能完善**: 多账户管理、批量操作、智能筛选、实时统计
- **🎨 现代界面**: 响应式设计、移动端适配、友好的用户体验
- **🔧 易于部署**: Docker支持、一键部署、完整文档
- **📡 API优先**: 21个RESTful API端点、在线测试、详细文档

---

## ✨ 功能特性

### 🏠 主要功能

#### 👥 账户管理

- ✅ 多账户管理 - 支持无限个Outlook邮箱账户
- ✅ 批量添加账户 - 快速导入大量账户
- ✅ 账户标签管理 - 灵活的分类和组织
- ✅ **批量Token刷新** - 支持多维度筛选批量刷新
- ✅ 账户状态监控 - 实时显示刷新状态和时间

#### 📧 邮件管理

- ✅ 邮件列表查看 - 收件箱和垃圾箱
- ✅ 双栏视图 - 同时查看多个文件夹
- ✅ 邮件详情查看 - 支持HTML和纯文本
- ✅ 智能搜索 - 按标题、发件人、日期搜索
- ✅ 分页加载 - 高效处理大量邮件
- ✅ 缓存管理 - 智能缓存优化性能

#### 🔄 Token管理

- ✅ **自动刷新** - 后台定时任务每天自动刷新
- ✅ **手动刷新** - 单个账户即时刷新
- ✅ **批量刷新** - 支持多维度筛选批量刷新
  - 按刷新状态筛选（从未刷新、成功、失败、待刷新）
  - 按邮箱搜索
  - 按标签搜索
  - 按时间范围筛选（今日、一周、一月、自定义）
- ✅ 刷新状态追踪 - 详细的刷新历史和错误信息

#### 🔐 认证与安全

- ✅ JWT Token认证 - 安全的访问控制
- ✅ 管理员系统 - 完整的用户管理
- ✅ 密码加密存储 - bcrypt哈希加密
- ✅ Token自动续期 - 24小时有效期
- ✅ OAuth2集成 - Microsoft OAuth2认证

#### 📡 API接口

- ✅ **21个RESTful API** - 完整的功能覆盖
- ✅ **在线测试** - 所有API都可直接在界面测试
- ✅ API文档 - 详细的参数说明和示例
- ✅ Swagger文档 - 自动生成的交互式文档
- ✅ 错误处理 - 标准化的错误响应

#### 🗄️ 数据管理

- ✅ SQLite数据库 - 轻量级、高性能
- ✅ 数据持久化 - 账户、配置、日志
- ✅ 管理面板 - 数据库表管理和查询
- ✅ 数据导出 - 支持CSV等格式
- ✅ 自动备份 - 数据安全保障

#### 🎨 用户界面

- ✅ 现代化设计 - 简洁、美观、易用
- ✅ 响应式布局 - 完美支持桌面和移动设备
- ✅ 实时通知 - 操作反馈和状态提示
- ✅ 深色模式支持 - 护眼舒适
- ✅ 键盘快捷键 - 提高操作效率

#### 🔧 系统特性

- ✅ Docker支持 - 一键部署
- ✅ 日志系统 - 按天轮转，保留30天
- ✅ 错误恢复 - 自动重连和重试
- ✅ 性能监控 - 系统状态实时监控
- ✅ 配置管理 - 灵活的系统配置

---

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.11+ （推荐 3.11）
- **数据库**: SQLite 3.0+（内置）
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **内存**: 最低 512MB，推荐 2GB+
- **磁盘**: 最低 500MB 可用空间

### 🔧 本地安装

#### 1. 克隆项目

```bash
git clone <repository-url>
cd OutlookManager2
```

#### 2. 安装依赖

**方式一：使用虚拟环境（推荐）**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**方式二：直接安装**

```bash
pip install -r requirements.txt
```

#### 3. 初始化数据库

```bash
# 数据库会在首次启动时自动创建
# 如需手动初始化：
python scripts/migrate.py
```

#### 4. 启动服务

**开发环境**

```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# 或直接运行
python main.py
```

**生产环境**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 5. 访问系统

启动成功后访问：

- 🌐 **Web界面**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs
- 📖 **ReDoc文档**: http://localhost:8000/redoc
- 📊 **系统状态**: http://localhost:8000/api

**默认管理员账户**：
- 用户名: `admin`
- 密码: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

---

## 🐳 Docker部署

### 快速部署

```bash
# 使用Docker Compose（推荐）
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

```bash
# 构建镜像
cd docker
docker build -t outlook-manager .

# 运行容器
docker run -d \
  --name outlook-email-api \
  -p 8000:8000 \
  -v $(pwd)/../data.db:/app/data.db \
  -v $(pwd)/../logs:/app/logs \
  outlook-manager

# 查看日志
docker logs -f outlook-email-api
```

### Docker Compose配置

```yaml
version: '3.8'

services:
  outlook-email-client:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data.db:/app/data.db
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

详细部署文档：[Docker部署说明](docs/Docker部署说明.md)

---

## 📡 API文档

### API端点总览

系统提供 **21个RESTful API端点**，所有端点都支持在线测试。

#### 📝 认证API（3个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/auth/login` | 管理员登录 | ❌ |
| GET | `/auth/me` | 获取当前管理员信息 | ✅ |
| POST | `/auth/change-password` | 修改密码 | ✅ |

#### 👥 账户管理API（7个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/accounts` | 获取账户列表 | ✅ |
| POST | `/accounts` | 添加新账户 | ✅ |
| DELETE | `/accounts/{email_id}` | 删除账户 | ✅ |
| PUT | `/accounts/{email_id}/tags` | 更新账户标签 | ✅ |
| POST | `/accounts/{email_id}/refresh-token` | 刷新单个账户Token | ✅ |
| **POST** | **`/accounts/batch-refresh-tokens`** | **批量刷新Token** ⭐ | ✅ |

#### 📧 邮件管理API（3个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/emails/{email_id}` | 获取邮件列表 | ✅ |
| GET | `/emails/{email_id}/{message_id}` | 获取邮件详情 | ✅ |
| GET | `/emails/{email_id}/dual-view` | 获取双栏视图邮件 | ✅ |

#### 🗄️ 管理面板API（5个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/admin/tables/{table_name}/count` | 获取表记录数 | ✅ |
| GET | `/admin/tables/{table_name}` | 获取表数据 | ✅ |
| DELETE | `/admin/tables/{table_name}/{record_id}` | 删除表记录 | ✅ |
| GET | `/admin/config` | 获取系统配置 | ✅ |
| POST | `/admin/config` | 更新系统配置 | ✅ |

#### 🗑️ 缓存管理API（2个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| DELETE | `/cache/{email_id}` | 清除指定邮箱缓存 | ✅ |
| DELETE | `/cache` | 清除所有缓存 | ✅ |

#### 📊 系统信息API（1个）

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api` | 获取系统状态 | ❌ |

### API使用示例

#### 登录获取Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 获取账户列表

```bash
curl -X GET "http://localhost:8000/accounts?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 批量刷新Token

```bash
curl -X POST "http://localhost:8000/accounts/batch-refresh-tokens?refresh_status=failed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应：
```json
{
  "total_processed": 10,
  "success_count": 8,
  "failed_count": 2,
  "details": [...]
}
```

详细API文档：[API试用接口功能说明](docs/API试用接口功能说明.md)

---

## 📚 使用指南

### 1️⃣ 添加邮箱账户

**前置要求**：需要从Azure Portal获取：
- Client ID（应用程序ID）
- Refresh Token（刷新令牌）

**步骤**：
1. 登录系统
2. 点击左侧菜单 "📧 邮箱账户管理"
3. 点击 "➕ 添加账户" 按钮
4. 填写邮箱地址、Refresh Token和Client ID
5. （可选）添加标签，如"工作"、"个人"
6. 点击 "🔍 测试连接" 验证配置
7. 点击 "➕ 添加账户" 完成

### 2️⃣ 批量添加账户

1. 点击 "📦 批量添加" 按钮
2. 按格式输入（每行一个账户）：
   ```
   邮箱地址----refresh_token----client_id
   ```
3. 点击 "✓ 验证格式" 检查数据
4. 点击 "🚀 开始批量添加"
5. 等待处理完成，查看结果统计

### 3️⃣ 批量刷新Token

**使用场景**：
- 新添加的账户需要立即验证
- 刷新失败的账户需要重试
- 凭证更新后需要立即刷新
- 系统维护后批量验证账户状态

**步骤**：
1. 在账户管理页面使用筛选器：
   - 选择刷新状态（从未刷新、失败、成功等）
   - 输入邮箱关键词（可选）
   - 输入标签关键词（可选）
2. 点击 "🔄 批量刷新Token" 按钮
3. 确认对话框会显示：
   - 当前筛选条件
   - 将要刷新的账户数量
4. 点击确定执行批量刷新
5. 查看详细的刷新结果

### 4️⃣ 查看邮件

1. 在账户列表中点击 "📧 查看邮件"
2. 选择文件夹：全部、收件箱、垃圾箱
3. 使用搜索框查找特定邮件
4. 点击邮件查看详细内容
5. 使用 "🔄 刷新" 按钮更新邮件列表

### 5️⃣ API在线测试

1. 访问 "📚 API文档" 页面
2. 找到要测试的API端点
3. 点击 "🚀 试用接口" 按钮
4. 填写必要的参数
5. 点击 "发送请求"
6. 查看响应结果

---

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（可选）：

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_FILE=data.db

# 日志配置
LOG_DIR=logs
LOG_RETENTION_DAYS=30

# IMAP配置
IMAP_SERVER=outlook.live.com
IMAP_PORT=993

# 连接池配置
MAX_CONNECTIONS=5
CONNECTION_TIMEOUT=30

# 缓存配置
CACHE_EXPIRE_TIME=60

# JWT配置（生产环境请修改）
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_HOURS=24
```

### Azure应用配置

1. **注册应用**
   - 访问 [Azure Portal](https://portal.azure.com)
   - Azure Active Directory → 应用注册 → 新注册
   - 记录 Application (client) ID

2. **配置权限**
   - API权限 → 添加权限 → Microsoft Graph
   - 选择委托权限：
     - `IMAP.AccessAsUser.All`
     - `offline_access`
   - 管理员同意授予权限

3. **获取Refresh Token**
   - 使用OAuth2授权码流程
   - 或使用第三方工具获取

详细配置：[Azure应用配置指南](docs/QUICK_START.md)

---

## 🛠️ 开发指南

### 项目结构

```
OutlookManager2/
├── main.py                 # FastAPI主应用（入口）
├── config.py               # 系统配置
├── models.py               # 数据模型
├── logger_config.py        # 日志配置
├── database.py             # SQLite数据库模块
├── auth.py                 # JWT认证模块
├── admin_api.py            # 管理面板API
├── account_service.py      # 账户服务
├── oauth_service.py        # OAuth服务
├── email_service.py        # 邮件服务
├── email_utils.py          # 邮件工具
├── imap_pool.py            # IMAP连接池
├── cache_service.py        # 缓存服务
│
├── routes/                 # 路由模块
│   ├── __init__.py
│   ├── auth_routes.py      # 认证路由
│   ├── account_routes.py   # 账户路由
│   ├── email_routes.py     # 邮件路由
│   └── cache_routes.py     # 缓存路由
│
├── static/                 # 前端资源
│   ├── index.html          # 主前端页面
│   ├── login.html          # 登录页面
│   ├── css/
│   │   └── style.css       # 样式文件
│   └── js/
│       └── app.js          # JavaScript逻辑
│
├── docs/                   # 文档目录
│   ├── ARCHITECTURE.md     # 架构文档
│   ├── MODULE_INDEX.md     # 模块索引
│   ├── REFACTORING_SUMMARY.md  # 重构总结
│   ├── 批量Token刷新功能说明.md
│   ├── Docker部署说明.md
│   ├── API试用接口功能说明.md
│   └── images/             # 截图和图片
│
├── docker/                 # Docker相关文件
│   ├── Dockerfile          # Docker镜像配置
│   ├── docker-compose.yml  # Docker编排配置
│   ├── docker-entrypoint.sh # 启动脚本
│   └── docker.env.example  # 环境变量示例
│
├── scripts/                # 工具脚本
│   ├── migrate.py          # 数据库迁移
│   ├── batch.py            # 批量处理工具
│   └── check_imports.py    # 导入检查
│
├── tests/                  # 测试文件
│   ├── test_admin_panel_apis.py
│   ├── test_new_features.py
│   └── test_token_refresh.py
│
├── backups/                # 备份文件
│   ├── main.py.backup
│   └── index.html.backup
│
├── logs/                   # 日志目录
│   └── outlook_manager.log
│
├── data.db                 # SQLite数据库
├── accounts.json           # 账户数据（备用）
├── requirements.txt        # Python依赖
└── README.md               # 项目说明（本文件）
```

### 数据库结构

#### accounts表
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    refresh_token TEXT NOT NULL,
    client_id TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    last_refresh_time TEXT,
    next_refresh_time TEXT,
    refresh_status TEXT DEFAULT 'pending',
    refresh_error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### admins表
```sql
CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);
```

#### system_config表
```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 技术栈

#### 后端
- **框架**: FastAPI 0.115.0
- **认证**: JWT (python-jose)
- **密码**: bcrypt
- **HTTP客户端**: httpx
- **IMAP**: imaplib (标准库)
- **数据验证**: Pydantic
- **数据库**: SQLite 3

#### 前端
- **HTML5** + **CSS3** + **Vanilla JavaScript**
- 响应式设计
- 无框架依赖
- 现代ES6+语法

#### 部署
- **ASGI服务器**: Uvicorn
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx（可选）

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd OutlookManager2

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或使用脚本
./run.sh  # Linux/Mac
run.bat   # Windows
```

### 代码规范

- **Python**: PEP 8
- **命名**: snake_case（函数、变量），PascalCase（类）
- **类型提示**: 使用Type Hints
- **文档**: Docstring（Google风格）
- **日志**: 使用logging模块

### 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📈 性能优化

### IMAP连接池

```python
# 配置连接池大小
MAX_CONNECTIONS = 5  # 每个邮箱的最大连接数
CONNECTION_TIMEOUT = 30  # 连接超时（秒）
SOCKET_TIMEOUT = 15  # Socket超时（秒）
```

### 缓存策略

```python
# 缓存过期时间
CACHE_EXPIRE_TIME = 60  # 秒

# 手动清除缓存
DELETE /cache/{email_id}  # 清除指定邮箱缓存
DELETE /cache             # 清除所有缓存
```

### 数据库优化

```bash
# SQLite优化
sqlite3 data.db "VACUUM;"
sqlite3 data.db "ANALYZE;"
```

### 并发处理

```bash
# 使用多个worker进程
uvicorn main:app --workers 4

# 或使用gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 🔒 安全建议

### 生产环境

1. **修改默认密码**
   ```bash
   # 首次登录后立即修改
   POST /auth/change-password
   ```

2. **使用强密钥**
   ```bash
   # 生成随机密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **启用HTTPS**
   ```nginx
   # Nginx SSL配置
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

4. **限制访问**
   ```nginx
   # IP白名单
   allow 192.168.1.0/24;
   deny all;
   ```

5. **定期备份**
   ```bash
   # 每天备份数据库
   0 2 * * * cp /app/data.db /backup/data.db.$(date +\%Y\%m\%d)
   ```

---

## 🐛 故障排查

### 常见问题

#### 1. 连接超时

**问题**: IMAP连接超时

**解决**:
```python
# 增加超时时间
CONNECTION_TIMEOUT = 60
SOCKET_TIMEOUT = 30
```

#### 2. Token过期

**问题**: Refresh Token失效

**解决**:
1. 检查Azure应用权限
2. 重新获取Refresh Token
3. 更新账户配置

#### 3. 数据库锁定

**问题**: Database is locked

**解决**:
```bash
# 关闭所有连接
sudo systemctl restart outlook-manager

# 或检查锁定
fuser data.db
```

#### 4. 内存不足

**问题**: Out of memory

**解决**:
```bash
# 减少worker数量
uvicorn main:app --workers 2

# 或增加系统内存
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/outlook_manager.log

# Docker日志
docker-compose logs -f

# 系统日志（Linux）
sudo journalctl -u outlook-manager -f
```

---

## 📝 更新日志

### v2.1.0 (2024-10-30)

#### 新增功能
- ✨ **批量Token刷新功能**
  - 支持多维度筛选（邮箱、标签、刷新状态、时间）
  - 智能确认对话框
  - 详细的结果统计

- ✨ **API试用接口**
  - 所有21个API端点支持在线测试
  - 自动Token认证
  - 参数预填和验证

- ✨ **新增API端点**
  - `POST /accounts/batch-refresh-tokens`
  - `PUT /accounts/{email_id}/tags`
  - `GET /emails/{email_id}/dual-view`
  - `DELETE /cache/{email_id}`
  - `DELETE /cache`

#### 优化改进
- 🚀 扩展账户筛选功能
- 🚀 优化数据库查询性能
- 🚀 改进错误处理机制
- 🚀 完善API文档

#### Docker支持
- 📦 新增 `docker-entrypoint.sh`
- 📦 新增 `.dockerignore`
- 📦 优化镜像构建

#### 文档完善
- 📚 新增8个专业文档
- 📚 详细的使用说明
- 📚 完整的部署指南

### v2.0.0 (之前版本)

- 🎉 初始发布
- ✅ 多账户管理
- ✅ 邮件查看
- ✅ JWT认证
- ✅ SQLite数据库

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Web框架
- [SQLite](https://www.sqlite.org/) - 嵌入式数据库
- [python-jose](https://github.com/mpdavis/python-jose) - JWT实现
- [httpx](https://www.python-httpx.org/) - HTTP客户端
- [passlib](https://passlib.readthedocs.io/) - 密码哈希

---

## 📞 联系方式

- **问题反馈**: 在GitHub Issues中提交
- **功能建议**: 欢迎提交Pull Request
- **技术支持**: 查看文档或联系开发团队

---

## 🎯 路线图

### 近期计划

- [ ] 邮件搜索增强（全文搜索）
- [ ] 邮件规则引擎
- [ ] 附件管理功能
- [ ] 邮件分类和标签
- [ ] 移动端App

### 长期计划

- [ ] 支持其他邮件协议（POP3、SMTP）
- [ ] 支持其他邮件服务商（Gmail、163等）
- [ ] AI邮件分类
- [ ] 邮件模板系统
- [ ] 团队协作功能

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个Star ⭐**

**📧 Outlook邮件管理系统 v2.1.0**

Made with ❤️ by Outlook Manager Team

[返回顶部](#-outlook邮件管理系统)

</div>

