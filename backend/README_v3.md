# Outlook邮件管理系统 v3.0 - 后端

基于DDD（领域驱动设计）和洋葱架构的现代化后端系统。

## 🏗️ 架构概览

本项目采用**洋葱架构（Onion Architecture）**，遵循**DDD（领域驱动设计）**原则：

```
backend/
└── src/
    ├── domain/              # 领域层（核心业务逻辑）
    │   ├── entities/        # 实体（Account, Admin, EmailMessage）
    │   ├── value_objects/   # 值对象（EmailAddress, Credentials, AccessToken）
    │   ├── repositories/    # 仓储接口
    │   ├── services/        # 领域服务接口
    │   └── exceptions/      # 领域异常
    │
    ├── application/         # 应用层（用例编排）
    │   ├── use_cases/       # 用例实现
    │   ├── dto/             # 数据传输对象
    │   └── interfaces/      # 外部服务接口
    │
    ├── infrastructure/      # 基础设施层（技术实现）
    │   ├── database/        # 数据库（SQLAlchemy）
    │   ├── external_services/ # 外部服务（OAuth, IMAP）
    │   ├── cache/           # 缓存实现
    │   └── logging/         # 日志配置
    │
    ├── presentation/        # 表现层（API）
    │   └── api/
    │       ├── v1/
    │       │   ├── routers/     # API路由
    │       │   ├── schemas/     # Pydantic Schemas
    │       │   └── dependencies/ # 依赖注入
    │       └── middleware/  # 中间件
    │
    ├── config/              # 配置管理
    └── main.py              # 应用入口
```

### 架构特点

1. **依赖倒置**：核心业务逻辑不依赖外部框架
2. **高内聚低耦合**：清晰的层次边界
3. **易于测试**：各层可独立测试
4. **易于替换**：外部服务可轻松替换

## 🚀 快速开始

### 环境要求

- Python 3.11+
- SQLite（开发）/ PostgreSQL（生产）
- Redis（可选，用于缓存）

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制环境变量模板（.env.example被忽略，手动创建.env）
# 编辑.env文件，设置必要的配置
```

关键配置项：
- `DATABASE_URL`: 数据库连接URL
- `JWT_SECRET_KEY`: JWT密钥（生产环境必须修改）
- `OAUTH_TOKEN_URL`: Microsoft OAuth2端点
- `REDIS_URL`: Redis连接URL（可选）

### 初始化数据库

```bash
# 自动创建表（开发环境）
# 首次运行时会自动初始化
python -m src.main
```

### 启动开发服务器

```bash
# 方式1：使用启动脚本
python run_dev.py

# 方式2：直接运行
cd src
python main.py

# 方式3：使用uvicorn
uvicorn src.main:app --reload
```

访问：
- API文档：http://localhost:8000/api/docs
- 健康检查：http://localhost:8000/health

## 📚 核心概念

### 1. 领域层（Domain）

包含核心业务逻辑，独立于外部框架。

#### 实体（Entities）

```python
# Account - 账户实体
account = Account(
    email=EmailAddress.create("user@outlook.com"),
    refresh_token="token",
    client_id="client_id"
)
account.update_refresh_token("new_token")
account.activate()
```

#### 值对象（Value Objects）

```python
# EmailAddress - 不可变的邮箱地址
email = EmailAddress.create("user@outlook.com")
domain = email.get_domain()  # "outlook.com"
is_outlook = email.is_outlook()  # True
```

#### 仓储接口（Repository Interfaces）

定义数据访问的抽象接口，具体实现在基础设施层。

### 2. 应用层（Application）

编排业务用例，协调领域对象。

#### 用例示例

```python
# 创建账户用例
use_case = CreateAccountUseCase(account_repository)
result = await use_case.execute(CreateAccountDTO(...))
```

### 3. 基础设施层（Infrastructure）

提供技术实现，如数据库、外部服务等。

#### 数据库

使用SQLAlchemy 2.0异步ORM：

```python
async with get_session() as session:
    repository = AccountRepositoryImpl(session)
    account = await repository.get_by_email(email)
```

#### 外部服务

- **OAuth客户端**：Microsoft OAuth2认证
- **IMAP客户端**：异步IMAP邮件访问
- **缓存服务**：内存/Redis缓存

### 4. 表现层（Presentation）

FastAPI REST API。

#### API端点

```
POST   /api/v1/auth/login                  # 登录
POST   /api/v1/accounts                    # 创建账户
GET    /api/v1/accounts                    # 获取账户列表
GET    /api/v1/accounts/{id}               # 获取账户详情
PATCH  /api/v1/accounts/{id}               # 更新账户
DELETE /api/v1/accounts/{id}               # 删除账户
POST   /api/v1/accounts/{id}/refresh-token # 刷新Token
```

## 🛠️ 开发指南

### 添加新功能

遵循洋葱架构，由内而外开发：

1. **领域层**：定义实体、值对象、仓储接口
2. **应用层**：实现用例、定义DTO
3. **基础设施层**：实现仓储、外部服务
4. **表现层**：创建API路由、Schema

### 代码规范

- 使用类型注解
- 遵循PEP 8
- 编写文档字符串
- 使用异步编程（async/await）

### 测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 覆盖率
pytest --cov=src tests/
```

## 🔒 安全性

- JWT认证
- 密码bcrypt加密
- CORS配置
- Rate Limiting（待实现）
- 输入验证（Pydantic）

## 📊 性能优化

- 异步I/O（asyncio）
- 数据库连接池
- IMAP连接池（待优化）
- 缓存机制
- 分页查询

## 🐛 故障排查

### 数据库连接失败

检查`DATABASE_URL`配置，确保数据库服务运行。

### OAuth认证失败

检查`OAUTH_TOKEN_URL`和`client_id`配置。

### IMAP连接超时

调整`IMAP_CONNECTION_TIMEOUT`配置。

## 📝 待完成工作

- [ ] IMAP客户端完整实现（邮件解析、搜索等）
- [ ] JWT服务完整实现
- [ ] Redis缓存完整实现
- [ ] 邮件路由实现
- [ ] Rate Limiting中间件
- [ ] 完整的单元测试
- [ ] 集成测试
- [ ] Alembic数据库迁移
- [ ] 从v2.0的数据迁移脚本
- [ ] API文档完善
- [ ] 性能监控和日志追踪

## 🔗 相关链接

- FastAPI文档：https://fastapi.tiangolo.com/
- SQLAlchemy文档：https://docs.sqlalchemy.org/
- Pydantic文档：https://docs.pydantic.dev/

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

