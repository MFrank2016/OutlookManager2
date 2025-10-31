# 📁 项目文件结构说明

本文档详细说明了 OutlookManager2 项目的文件组织结构和各目录的用途。

## 🎯 整理原则

为了提高项目的可维护性和可读性，我们按照以下原则组织文件：

1. **职责单一**：每个目录只包含特定类型的文件
2. **层次清晰**：目录结构一目了然，便于快速定位
3. **易于扩展**：新增功能可以方便地找到对应位置
4. **符合规范**：遵循Python和Web项目的最佳实践

## 📂 目录结构

```
OutlookManager2/
├── 📂 根目录 - 核心模块和配置
│   ├── main.py                 # ⭐ FastAPI主应用入口
│   ├── config.py               # 系统配置常量
│   ├── models.py               # Pydantic数据模型
│   ├── logger_config.py        # 日志配置
│   ├── database.py             # SQLite数据库操作
│   ├── auth.py                 # JWT认证模块
│   ├── admin_api.py            # 管理面板API
│   ├── account_service.py      # 账户服务
│   ├── oauth_service.py        # OAuth2服务
│   ├── email_service.py        # 邮件服务
│   ├── email_utils.py          # 邮件工具函数
│   ├── imap_pool.py            # IMAP连接池
│   ├── cache_service.py        # 缓存服务
│   ├── requirements.txt        # Python依赖列表
│   ├── README.md               # 项目主文档
│   ├── data.db                 # SQLite数据库文件（运行时生成）
│   └── accounts.json           # 账户数据（备用）
│
├── 📂 routes/ - API路由模块
│   ├── __init__.py             # 路由包初始化
│   ├── auth_routes.py          # 认证相关路由
│   ├── account_routes.py       # 账户管理路由
│   ├── email_routes.py         # 邮件管理路由
│   └── cache_routes.py         # 缓存管理路由
│
├── 📂 static/ - 前端静态资源
│   ├── index.html              # 主应用界面
│   ├── login.html              # 登录页面
│   ├── css/
│   │   └── style.css           # 全局样式
│   └── js/
│       └── app.js              # 前端JavaScript逻辑
│
├── 📂 docs/ - 项目文档
│   ├── ARCHITECTURE.md         # 架构设计文档
│   ├── MODULE_INDEX.md         # 模块索引
│   ├── REFACTORING_SUMMARY.md  # 重构总结
│   ├── README.md               # 文档目录说明
│   ├── QUICK_START.md          # 快速开始指南
│   ├── CHANGELOG.md            # 更新日志
│   ├── UPGRADE.md              # 升级指南
│   ├── Docker部署说明.md
│   ├── API试用接口功能说明.md
│   ├── 批量Token刷新功能说明.md
│   ├── 管理面板使用说明.md
│   └── images/                 # 文档配图
│       ├── account-add.png
│       ├── account-management.png
│       ├── api-docs.png
│       └── email-list.png
│
├── 📂 docker/ - Docker相关文件
│   ├── Dockerfile              # Docker镜像构建文件
│   ├── docker-compose.yml      # Docker Compose编排文件
│   ├── docker-entrypoint.sh    # 容器启动脚本
│   └── docker.env.example      # 环境变量示例
│
├── 📂 scripts/ - 工具脚本
│   ├── migrate.py              # 数据库迁移脚本
│   ├── batch.py                # 批量处理工具
│   ├── check_imports.py        # 导入检查工具
│   ├── fix_encoding.py         # 编码修复工具
│   ├── correct_split.py        # 文件拆分工具
│   └── detect_and_fix_encoding.py  # 编码检测工具
│
├── 📂 tests/ - 测试文件
│   ├── test_admin_panel_apis.py    # 管理面板API测试
│   ├── test_new_features.py        # 新功能测试
│   └── test_token_refresh.py       # Token刷新测试
│
├── 📂 backups/ - 备份文件
│   ├── main.py.backup          # 重构前的主文件备份
│   └── index.html.backup       # 重构前的HTML备份
│
└── 📂 logs/ - 日志文件（运行时生成）
    ├── outlook_manager.log     # 当前日志
    ├── outlook_manager.log.2025-10-29
    └── outlook_manager.log.2025-10-30
```

## 📋 目录详细说明

### 1. 根目录 - 核心模块

**用途**：存放项目的核心业务逻辑模块和配置文件

**文件说明**：
- `main.py` - FastAPI应用入口，定义路由和启动配置
- `config.py` - 系统配置常量（IMAP服务器、OAuth配置等）
- `models.py` - Pydantic数据模型定义
- `*_service.py` - 业务服务层（账户、邮件、OAuth等）
- `*_utils.py` - 工具函数模块

**为什么这样组织**：
- ✅ 核心代码集中，便于快速定位主要逻辑
- ✅ 符合Python项目的标准结构
- ✅ 便于IDE自动识别和导入

### 2. routes/ - API路由模块

**用途**：存放所有API路由定义，按功能模块分类

**组织方式**：
```
routes/
├── auth_routes.py      # /auth/* 认证相关API
├── account_routes.py   # /accounts/* 账户管理API
├── email_routes.py     # /emails/* 邮件管理API
└── cache_routes.py     # /cache/* 缓存管理API
```

**为什么这样组织**：
- ✅ 路由与业务逻辑分离
- ✅ 便于API版本管理
- ✅ 支持团队协作开发

### 3. static/ - 前端静态资源

**用途**：存放前端HTML、CSS、JavaScript文件

**组织方式**：
```
static/
├── *.html          # HTML页面
├── css/            # 样式文件
│   └── style.css
└── js/             # JavaScript文件
    └── app.js
```

**为什么这样组织**：
- ✅ 前后端分离，职责清晰
- ✅ 符合Web项目标准结构
- ✅ 便于CDN部署和缓存优化

### 4. docs/ - 项目文档

**用途**：存放所有项目相关文档

**文档类型**：
- **技术文档**：架构设计、API说明、模块索引
- **用户文档**：快速开始、使用说明、部署指南
- **开发文档**：更新日志、升级指南、重构总结
- **多媒体**：截图、流程图、架构图

**为什么这样组织**：
- ✅ 文档集中管理，便于查阅
- ✅ 支持文档版本控制
- ✅ 便于生成文档网站

### 5. docker/ - Docker相关文件

**用途**：存放Docker镜像构建和容器编排相关文件

**文件说明**：
- `Dockerfile` - Docker镜像构建指令
- `docker-compose.yml` - 服务编排配置
- `docker-entrypoint.sh` - 容器启动脚本
- `docker.env.example` - 环境变量模板

**使用方式**：
```bash
cd docker
docker-compose up -d
```

**为什么这样组织**：
- ✅ Docker文件集中管理
- ✅ 便于多环境部署（dev/test/prod）
- ✅ 支持Docker Compose直接运行

### 6. scripts/ - 工具脚本

**用途**：存放开发和维护相关的工具脚本

**脚本类型**：
- **数据库**：`migrate.py` - 数据库迁移
- **批处理**：`batch.py` - 批量操作工具
- **开发工具**：`check_imports.py` - 导入检查
- **维护工具**：编码修复、文件拆分等

**使用方式**：
```bash
python scripts/migrate.py
python scripts/batch.py --help
```

**为什么这样组织**：
- ✅ 脚本与核心代码分离
- ✅ 便于脚本管理和版本控制
- ✅ 避免污染项目根目录

### 7. tests/ - 测试文件

**用途**：存放单元测试、集成测试、功能测试

**测试类型**：
- **API测试**：测试各个API端点
- **功能测试**：测试具体业务功能
- **集成测试**：测试模块间集成

**运行方式**：
```bash
pytest tests/
python tests/test_admin_panel_apis.py
```

**为什么这样组织**：
- ✅ 测试代码与业务代码分离
- ✅ 便于CI/CD集成
- ✅ 符合Python测试规范

### 8. backups/ - 备份文件

**用途**：存放重要文件的备份版本

**备份策略**：
- 重构前自动备份
- 重要更新前手动备份
- 保留历史版本以便回滚

**为什么这样组织**：
- ✅ 备份文件不污染工作目录
- ✅ 便于版本对比
- ✅ 支持快速回滚

### 9. logs/ - 日志文件

**用途**：存放应用运行日志（运行时自动生成）

**日志策略**：
- 按天轮转
- 保留30天
- 自动清理过期日志

**为什么这样组织**：
- ✅ 日志与代码分离
- ✅ 便于日志分析和监控
- ✅ 支持日志收集系统集成

## 🎨 设计优势

### 1. 清晰的关注点分离

```
核心业务逻辑 → 根目录（*.py）
API接口定义  → routes/
前端资源     → static/
项目文档     → docs/
部署配置     → docker/
辅助工具     → scripts/
测试代码     → tests/
```

### 2. 易于导航和查找

- **新手开发者**：能快速理解项目结构
- **维护人员**：能快速定位需要修改的文件
- **部署人员**：能轻松找到部署相关配置

### 3. 支持持续集成

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 构建Docker镜像
cd docker && docker build -t app .

# 查看文档
open docs/README.md
```

### 4. 便于团队协作

- **前端开发**：只需关注 `static/` 目录
- **后端开发**：主要在根目录和 `routes/`
- **运维人员**：重点关注 `docker/` 和配置文件
- **文档编写**：专注于 `docs/` 目录

## 🔄 文件迁移记录

### 重构日期：2025-10-31

#### 移动的文件：

1. **Docker文件** → `docker/`
   - Dockerfile
   - docker-compose.yml
   - docker-entrypoint.sh

2. **测试文件** → `tests/`
   - test_admin_panel_apis.py
   - test_new_features.py
   - test_token_refresh.py

3. **脚本文件** → `scripts/`
   - migrate.py
   - batch.py
   - check_imports.py
   - fix_encoding.py
   - correct_split.py
   - detect_and_fix_encoding.py

4. **文档文件** → `docs/`
   - ARCHITECTURE.md
   - MODULE_INDEX.md
   - REFACTORING_SUMMARY.md
   - （其他文档已经在docs/中）

5. **备份文件** → `backups/`
   - main.py.backup
   - index.html.backup

## 📝 使用建议

### 添加新功能时

1. **新建服务模块** → 根目录创建 `xxx_service.py`
2. **新建API路由** → `routes/` 创建 `xxx_routes.py`
3. **新建前端页面** → `static/` 添加HTML/CSS/JS
4. **编写测试** → `tests/` 创建 `test_xxx.py`
5. **更新文档** → `docs/` 添加或更新相关文档

### 部署时

1. **本地部署**：直接运行 `python main.py`
2. **Docker部署**：进入 `docker/` 目录，运行 `docker-compose up -d`
3. **查看日志**：检查 `logs/` 目录或使用 `docker logs`

### 维护时

1. **数据库迁移**：运行 `python scripts/migrate.py`
2. **批量操作**：使用 `scripts/` 下的工具脚本
3. **查看文档**：参考 `docs/` 下的相关文档
4. **回滚代码**：使用 `backups/` 中的备份文件

## ⚠️ 注意事项

1. **不要修改目录结构**，除非有充分理由
2. **新文件要放到正确的目录**，保持结构清晰
3. **更新路径引用**，移动文件后记得更新import路径
4. **保持README同步**，结构变更后更新主文档
5. **备份重要文件**，修改前做好备份

## 🔗 相关文档

- [项目架构文档](docs/ARCHITECTURE.md)
- [模块索引](docs/MODULE_INDEX.md)
- [重构总结](docs/REFACTORING_SUMMARY.md)
- [快速开始指南](docs/QUICK_START.md)

---

**最后更新**: 2025-10-31  
**版本**: 2.0  
**维护者**: Outlook Manager Team

