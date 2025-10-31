# 模块索引

快速查找各个功能所在的模块位置。

## 🎨 前端模块

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `static/index.html` | 主页面结构 | ~1780 |
| `static/css/style.css` | 样式定义 | ~2270 |
| `static/js/app.js` | 前端逻辑 | ~3018 |

## ⚙️ 配置模块

| 文件路径 | 说明 | 主要内容 |
|---------|------|----------|
| `config.py` | 系统配置 | OAuth、IMAP、连接池、缓存、日志配置 |
| `logger_config.py` | 日志配置 | 日志系统初始化和配置 |

## 📦 数据模型

| 文件路径 | 说明 | 主要模型 |
|---------|------|----------|
| `models.py` | Pydantic模型 | AccountCredentials, EmailItem, EmailListResponse, etc. |

## 🔧 服务层

| 文件路径 | 说明 | 主要功能 |
|---------|------|----------|
| `imap_pool.py` | IMAP连接池 | 连接管理、复用、状态监控 |
| `cache_service.py` | 缓存服务 | 内存缓存管理、键生成、过期处理 |
| `email_utils.py` | 邮件工具 | 邮件头解码、内容提取 |
| `account_service.py` | 账户服务 | 凭证管理、账户查询 |
| `oauth_service.py` | OAuth服务 | 令牌获取、刷新 |
| `email_service.py` | 邮件服务 | 邮件列表、详情查询 |

## 🌐 路由层

| 文件路径 | 说明 | API端点 |
|---------|------|---------|
| `routes/__init__.py` | 路由包 | 集成所有子路由 |
| `routes/auth_routes.py` | 认证路由 | /auth/login, /auth/me, /auth/change-password |
| `routes/account_routes.py` | 账户路由 | /accounts, /accounts/{id}/*, 批量操作 |
| `routes/email_routes.py` | 邮件路由 | /emails/{id}, /emails/{id}/dual-view |
| `routes/cache_routes.py` | 缓存路由 | /cache, /cache/{id} |

## 🚀 主应用

| 文件路径 | 说明 | 主要内容 |
|---------|------|----------|
| `main.py` | 应用入口 | FastAPI初始化、生命周期管理、后台任务 |

## 📚 已有模块（未修改）

| 文件路径 | 说明 |
|---------|------|
| `auth.py` | 认证模块 |
| `database.py` | 数据库操作 |
| `admin_api.py` | 管理员API |
| `batch.py` | 批处理操作 |
| `migrate.py` | 数据库迁移 |

## 🔍 功能查找指南

### 想要添加新的配置项？
👉 编辑 `config.py`

### 想要添加新的数据模型？
👉 编辑 `models.py`

### 想要添加新的API端点？
👉 在 `routes/` 目录下对应的路由文件中添加

### 想要修改邮件处理逻辑？
👉 编辑 `email_service.py` 或 `email_utils.py`

### 想要修改账户管理逻辑？
👉 编辑 `account_service.py`

### 想要修改OAuth逻辑？
👉 编辑 `oauth_service.py`

### 想要修改IMAP连接管理？
👉 编辑 `imap_pool.py`

### 想要修改缓存策略？
👉 编辑 `cache_service.py`

### 想要修改日志配置？
👉 编辑 `logger_config.py`

### 想要修改前端样式？
👉 编辑 `static/css/style.css`

### 想要修改前端逻辑？
👉 编辑 `static/js/app.js`

### 想要修改页面结构？
👉 编辑 `static/index.html`

## 📖 相关文档

- 详细架构说明: `ARCHITECTURE.md`
- 重构总结: `REFACTORING_SUMMARY.md`
- 原始项目文档: `README.md`

## 🔗 模块依赖关系

```
main.py
├── config.py (配置)
├── logger_config.py (日志)
├── models.py (模型)
├── imap_pool.py (连接池)
│   └── config.py
├── cache_service.py (缓存)
│   └── config.py
├── email_utils.py (工具)
├── account_service.py (账户)
│   ├── models.py
│   └── database.py
├── oauth_service.py (OAuth)
│   ├── config.py
│   └── models.py
├── email_service.py (邮件)
│   ├── models.py
│   ├── cache_service.py
│   ├── email_utils.py
│   ├── imap_pool.py
│   ├── oauth_service.py
│   └── database.py
└── routes/ (路由)
    ├── auth_routes.py
    ├── account_routes.py
    ├── email_routes.py
    └── cache_routes.py
```

## 💡 最佳实践

1. **遵循单一职责原则**: 每个模块只负责一件事
2. **保持低耦合**: 模块间通过明确的接口交互
3. **使用依赖注入**: 通过参数传递依赖，而非全局导入
4. **编写单元测试**: 为每个服务层函数编写测试
5. **记录日志**: 在关键操作处添加日志记录
6. **处理异常**: 合理捕获和处理异常
7. **更新文档**: 修改代码后及时更新相关文档

---

*文档生成时间: 2025-10-31*

