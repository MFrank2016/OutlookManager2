# OutlookManager v3.0 项目启动指南

**版本**: 3.0.0  
**状态**: ✅ 生产就绪  
**完成度**: 95%

---

## 📋 快速概览

OutlookManager v3.0 是一个现代化的Outlook邮件管理系统，采用前后端分离架构：

- **后端**: Python + FastAPI + SQLAlchemy (洋葱架构/DDD)
- **前端**: Next.js 14 + TypeScript + Tailwind CSS
- **数据库**: SQLite (开发) / PostgreSQL (生产推荐)

---

## 🚀 一键启动（推荐）

### Windows

```bash
# 后端
cd backend
python run_dev.py

# 新开一个终端窗口
# 前端
cd frontend
npm install
npm run dev
```

### Linux/Mac

```bash
# 后端
cd backend
./run.sh

# 新开一个终端
# 前端
cd frontend
npm install
npm run dev
```

然后访问:
- **前端**: http://localhost:3000
- **后端API文档**: http://localhost:8000/docs
- **默认凭证**: admin / admin123

---

## 📖 详细启动步骤

### 第一步：环境准备

#### 系统要求
- **Python**: 3.11+ (推荐 3.13)
- **Node.js**: 18.0+
- **操作系统**: Windows 10+, Linux, macOS

#### 检查版本
```bash
python --version  # 应该 >= 3.11
node --version    # 应该 >= 18.0
npm --version
```

### 第二步：后端启动

#### 2.1 进入后端目录
```bash
cd backend
```

#### 2.2 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 2.3 安装依赖
```bash
pip install -r requirements.txt
```

#### 2.4 初始化数据库
```bash
python scripts/init_database.py
```

#### 2.5 创建管理员账户
```bash
python scripts/create_admin.py
```
默认会创建:
- 用户名: admin
- 密码: admin123

#### 2.6 启动后端服务
```bash
python run_dev.py
```

服务运行在: http://localhost:8000

#### 2.7 验证后端
访问 http://localhost:8000/docs 查看API文档

### 第三步：前端启动

#### 3.1 新开终端，进入前端目录
```bash
cd frontend
```

#### 3.2 安装依赖
```bash
npm install
```

如果使用 yarn 或 pnpm:
```bash
yarn install
# 或
pnpm install
```

#### 3.3 配置环境变量（可选）
```bash
# Windows
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local

# Linux/Mac
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

默认已经配置好，通常不需要修改。

#### 3.4 启动前端服务
```bash
npm run dev
```

服务运行在: http://localhost:3000

#### 3.5 访问应用
打开浏览器访问 http://localhost:3000

---

## 🎯 首次使用指南

### 1. 登录系统
- 访问 http://localhost:3000
- 输入默认凭证:
  - 用户名: `admin`
  - 密码: `admin123`

### 2. 查看仪表板
- 登录后自动跳转到仪表板
- 查看系统统计信息

### 3. 添加Outlook账户
- 点击"账户管理"
- 点击"➕ 添加账户"
- 填写账户信息:
  - 邮箱地址
  - Refresh Token（从Azure获取）
  - Client ID（Azure应用ID）
  - 标签（可选）

### 4. 查看邮件
- 点击"邮件管理"
- 选择账户
- 选择文件夹（收件箱/已发送等）
- 浏览邮件列表

---

## 🔧 常见问题解决

### 后端问题

#### ❌ ModuleNotFoundError: No module named 'src'
**解决**:
```bash
cd backend
python run_dev.py  # 而不是直接运行 main.py
```

#### ❌ 数据库文件不存在
**解决**:
```bash
cd backend
python scripts/init_database.py
```

#### ❌ 端口8000被占用
**解决**:
1. 找到占用端口的进程：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```
2. 结束进程或修改端口配置

### 前端问题

#### ❌ npm install 失败
**解决**:
```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### ❌ 无法连接后端
**检查**:
1. 后端服务是否运行: http://localhost:8000/health
2. `.env.local` 配置是否正确
3. 浏览器控制台是否有CORS错误

#### ❌ 端口3000被占用
**解决**:
```bash
PORT=3001 npm run dev
```

### 登录问题

#### ❌ 登录失败 - Invalid credentials
**解决**:
```bash
cd backend
python scripts/create_admin.py
# 重新创建管理员账户
```

#### ❌ Token验证失败
**解决**:
1. 清除浏览器localStorage
2. 重新登录

---

## 📁 项目结构

```
OutlookManager2/
├── backend/                 # 后端（FastAPI）
│   ├── src/                # 源代码
│   │   ├── domain/        # 领域层
│   │   ├── application/   # 应用层
│   │   ├── infrastructure/# 基础设施层
│   │   ├── presentation/  # 表现层（API）
│   │   └── config/        # 配置
│   ├── scripts/           # 脚本工具
│   ├── tests/             # 测试
│   ├── requirements.txt   # 依赖
│   └── run_dev.py         # 启动脚本
│
├── frontend/               # 前端（Next.js）
│   ├── app/               # 页面路由
│   ├── lib/               # 工具库
│   ├── types/             # 类型定义
│   ├── package.json       # 依赖
│   └── next.config.js     # 配置
│
├── docs/                   # 文档
├── data.db                # SQLite数据库
└── README.md              # 项目说明
```

---

## 🔐 安全注意事项

### 开发环境
- ✅ 使用默认凭证 (admin/admin123)
- ✅ SQLite数据库
- ✅ 调试模式开启

### 生产环境
- ⚠️ **必须修改默认密码**
- ⚠️ **使用PostgreSQL数据库**
- ⚠️ **配置HTTPS**
- ⚠️ **设置强JWT密钥**
- ⚠️ **配置CORS白名单**
- ⚠️ **启用速率限制**

---

## 📊 系统监控

### 健康检查
```bash
# 后端
curl http://localhost:8000/health

# 前端
curl http://localhost:3000
```

### 日志查看
```bash
# 后端日志
tail -f backend/logs/outlook_manager.log

# 前端日志（控制台）
# 浏览器开发者工具 -> Console
```

---

## 🧪 测试指南

### 后端测试
```bash
cd backend
pytest tests/
```

### 前端测试
```bash
cd frontend
npm run test
```

### API测试
```bash
cd backend
python test_api.py
```

---

## 📚 更多文档

- **后端文档**: `backend/README.md`
- **前端文档**: `frontend/README.md`
- **API文档**: http://localhost:8000/docs (运行后访问)
- **重构进度**: `REFACTORING_PROGRESS.md`
- **后端完成报告**: `backend/BACKEND_VERIFICATION_COMPLETE.md`
- **前端完成报告**: `frontend/COMPLETION_REPORT.md`

---

## 💡 开发技巧

### 后端开发
```bash
# 热重载开发
python run_dev.py

# 生成数据库迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head
```

### 前端开发
```bash
# 热重载开发
npm run dev

# 类型检查
npm run type-check

# 代码格式化
npm run format

# 构建生产版本
npm run build
```

---

## 🎓 学习资源

### 后端技术栈
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/

### 前端技术栈
- Next.js: https://nextjs.org/docs
- React: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/docs
- TypeScript: https://www.typescriptlang.org/docs

---

## 🚀 部署指南

### Docker部署（推荐）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 手动部署
参考各自目录的部署文档：
- `backend/README.md` - 后端部署
- `frontend/README.md` - 前端部署

---

## 📞 获取帮助

### 问题排查顺序
1. 查看本文档常见问题
2. 查看具体模块的README
3. 查看日志文件
4. 检查控制台错误
5. 验证环境配置

### 快速诊断命令
```bash
# 检查后端状态
curl http://localhost:8000/health

# 检查前端状态
curl http://localhost:3000

# 查看后端日志
tail -n 50 backend/logs/outlook_manager.log

# 查看进程
ps aux | grep python  # 后端
ps aux | grep node    # 前端
```

---

## 🎉 下一步

系统启动成功后，您可以：

1. ✅ 修改管理员密码
2. ✅ 添加Outlook账户
3. ✅ 探索邮件管理功能
4. ✅ 查看API文档
5. ✅ 自定义配置
6. ✅ 部署到生产环境

---

**祝您使用愉快！** 🚀

如有问题，请查看详细文档或检查日志文件。

