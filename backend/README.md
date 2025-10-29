# Outlook邮件管理系统 - 后端

基于**洋葱架构（Onion Architecture）**和**领域驱动设计（DDD）**的现代化FastAPI后端应用。

## 📁 项目结构

```
backend/
├── src/
│   ├── domain/                 # 领域层（核心业务逻辑）
│   │   ├── entities/           # 实体：Account, EmailMessage, Admin
│   │   ├── value_objects/      # 值对象：EmailAddress, Credentials, Token
│   │   ├── repositories/       # 仓储接口（抽象）
│   │   ├── services/           # 领域服务
│   │   └── exceptions/         # 领域异常
│   │
│   ├── application/            # 应用层（用例编排）
│   │   ├── use_cases/          # 用例：业务流程编排
│   │   ├── dto/                # 数据传输对象
│   │   └── interfaces/         # 应用层接口
│   │
│   ├── infrastructure/         # 基础设施层（技术实现）
│   │   ├── database/           # 数据库（SQLAlchemy）
│   │   ├── external_services/  # 外部服务（IMAP, OAuth）
│   │   ├── cache/              # 缓存实现
│   │   └── logging/            # 日志配置
│   │
│   ├── presentation/           # 表现层（API端点）
│   │   ├── api/v1/             # API v1
│   │   │   ├── routers/        # FastAPI路由
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── dependencies/   # 依赖注入
│   │   └── middleware/         # 中间件
│   │
│   ├── config/                 # 配置管理
│   │   ├── settings.py         # 应用配置
│   │   └── constants.py        # 常量定义
│   │
│   └── shared/                 # 共享工具
│
├── tests/                      # 测试
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── e2e/                    # 端到端测试
│
├── alembic/                    # 数据库迁移
├── requirements.txt            # 依赖包
└── .env.example                # 环境变量示例
```

## 🏗️ 架构原则

### 洋葱架构层次

1. **领域层（Domain Layer）** - 核心
   - 包含业务规则和业务逻辑
   - 不依赖任何外层
   - 纯粹的Python代码，无框架依赖

2. **应用层（Application Layer）**
   - 协调领域层完成业务用例
   - 依赖领域层接口
   - 不依赖基础设施层

3. **基础设施层（Infrastructure Layer）**
   - 实现领域层定义的接口
   - 包含所有技术实现细节
   - 依赖外部框架和库

4. **表现层（Presentation Layer）**
   - 处理HTTP请求和响应
   - 调用应用层用例
   - FastAPI路由和中间件

### 依赖规则

依赖方向：**表现层 → 应用层 → 领域层 ← 基础设施层**

- 外层可以依赖内层
- 内层不能依赖外层
- 通过接口反转依赖

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置数据库、JWT密钥等
```

### 3. 初始化数据库

```bash
alembic upgrade head
```

### 4. 启动应用

```bash
# 开发环境
uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
gunicorn src.presentation.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 📝 开发规范

### 代码风格

- 遵循PEP 8
- 使用Black格式化
- 使用isort排序导入
- 使用mypy类型检查

```bash
# 格式化代码
black src/

# 排序导入
isort src/

# 类型检查
mypy src/
```

### 提交规范

使用约定式提交（Conventional Commits）：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 🔑 核心概念

### 实体（Entity）

具有唯一标识的业务对象：

```python
from src.domain.entities import Account

account = Account(
    email=EmailAddress("user@example.com"),
    refresh_token="token",
    client_id="client_id"
)
```

### 值对象（Value Object）

不可变的业务值：

```python
from src.domain.value_objects import EmailAddress

email = EmailAddress.create("user@example.com")
domain = email.get_domain()  # "example.com"
```

### 仓储（Repository）

数据访问抽象：

```python
from src.domain.repositories import IAccountRepository

# 接口定义在领域层
# 实现在基础设施层
class AccountRepositoryImpl(IAccountRepository):
    async def get_by_email(self, email: EmailAddress) -> Account:
        # 数据库查询实现
        pass
```

### 用例（Use Case）

业务流程编排：

```python
from src.application.use_cases.account import CreateAccountUseCase

use_case = CreateAccountUseCase(account_repository)
account = await use_case.execute(account_dto)
```

## 📚 技术栈

- **FastAPI** 0.109+ - Web框架
- **Pydantic** 2.6+ - 数据验证
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - 数据库迁移
- **Pydantic Settings** - 配置管理
- **python-jose** - JWT认证
- **httpx** - HTTP客户端
- **structlog** - 结构化日志

## 📖 API文档

API遵循RESTful设计，统一响应格式：

### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "data": { /* 实际数据 */ },
  "error": null
}
```

### 错误响应

```json
{
  "success": false,
  "message": "错误描述",
  "data": null,
  "error": {
    "code": "E3000",
    "details": { /* 错误详情 */ }
  }
}
```

## 🔧 配置说明

主要配置项（在`.env`文件中）：

- `DATABASE_URL` - 数据库连接URL
- `JWT_SECRET_KEY` - JWT密钥（生产环境必须修改）
- `IMAP_SERVER` - IMAP服务器地址
- `REDIS_URL` - Redis连接URL（可选）
- `LOG_LEVEL` - 日志级别

详见`.env.example`文件。

## 📞 支持

如有问题，请提交Issue或联系开发团队。

---

**Version:** 3.0.0  
**License:** MIT  
**Architecture:** Onion Architecture + DDD

