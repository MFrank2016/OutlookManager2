# OutlookManager 前端

OutlookManager v3.0 的现代化前端应用，基于 Next.js 14 + TypeScript + Tailwind CSS 构建。

## 🚀 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript 5.3
- **样式**: Tailwind CSS 3.4
- **UI组件**: Radix UI
- **状态管理**: React Hooks
- **HTTP客户端**: Fetch API
- **表单验证**: React Hook Form + Zod

## 📁 项目结构

```
frontend/
├── app/                    # Next.js 应用路由
│   ├── dashboard/         # 仪表板页面
│   │   ├── accounts/     # 账户管理
│   │   ├── emails/       # 邮件管理
│   │   └── layout.tsx    # 仪表板布局
│   ├── login/            # 登录页面
│   ├── globals.css       # 全局样式
│   ├── layout.tsx        # 根布局
│   └── page.tsx          # 首页（重定向）
├── lib/                   # 工具库
│   └── api-client.ts     # API客户端
├── types/                 # TypeScript类型定义
│   └── index.ts          # 类型导出
├── public/               # 静态资源
├── .env.example          # 环境变量示例
├── next.config.js        # Next.js配置
├── tailwind.config.ts    # Tailwind配置
└── tsconfig.json         # TypeScript配置
```

## 🛠️ 开发指南

### 前置要求

- Node.js 18.0 或更高版本
- npm 或 yarn 或 pnpm

### 安装依赖

```bash
cd frontend
npm install
```

### 配置环境变量

创建 `.env.local` 文件：

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
npm start
```

### 代码检查

```bash
npm run lint          # ESLint检查
npm run type-check    # TypeScript类型检查
npm run format        # Prettier格式化
```

## 📄 页面说明

### 登录页面 (`/login`)
- 用户认证
- JWT Token管理
- 自动重定向到仪表板

### 仪表板 (`/dashboard`)
- 系统统计概览
- 快速操作入口
- 实时数据展示

### 账户管理 (`/dashboard/accounts`)
- 账户列表展示
- 添加/删除账户
- 刷新Token
- 标签管理

### 邮件管理 (`/dashboard/emails`)
- 邮件列表查看
- 文件夹切换（收件箱、已发送等）
- 邮件详情展示
- 搜索和筛选

## 🎨 设计系统

### 颜色主题

项目使用 Tailwind CSS 和 CSS 变量实现主题系统，支持亮色/暗色模式。

### 响应式设计

- **移动端**: < 768px
- **平板**: 768px - 1024px
- **桌面**: > 1024px

## 🔌 API集成

API客户端位于 `lib/api-client.ts`，提供以下功能：

- 自动Token管理
- 请求/响应拦截
- 错误处理
- 类型安全

### 使用示例

```typescript
import { apiClient } from "@/lib/api-client";

// 登录
const response = await apiClient.login({
  username: "admin",
  password: "admin123"
});

// 获取账户列表
const accounts = await apiClient.getAccounts();

// 创建账户
const newAccount = await apiClient.createAccount({
  email: "user@outlook.com",
  refresh_token: "token",
  client_id: "client_id",
  tags: ["personal"]
});
```

## 🔐 认证流程

1. 用户在登录页面输入凭证
2. 调用 `/api/v1/auth/login` 获取JWT Token
3. Token存储在localStorage
4. 后续请求自动携带Token
5. Token失效时自动跳转到登录页

## 📦 依赖说明

### 核心依赖
- `next`: React框架
- `react` & `react-dom`: UI库
- `typescript`: 类型支持
- `tailwindcss`: CSS框架

### UI组件
- `@radix-ui/*`: 无样式UI组件库
- `lucide-react`: 图标库
- `clsx` & `tailwind-merge`: 样式工具

### 工具库
- `react-hook-form`: 表单管理
- `zod`: 数据验证
- `date-fns`: 日期处理
- `zustand`: 状态管理（可选）

## 🚧 待开发功能

- [ ] 暗色模式切换
- [ ] 邮件详情页面
- [ ] 高级搜索功能
- [ ] 批量操作
- [ ] 邮件标签管理
- [ ] 导出功能
- [ ] 多语言支持

## 📝 开发规范

### 代码风格
- 使用 TypeScript 严格模式
- 遵循 ESLint 规则
- 使用 Prettier 格式化
- 组件使用函数式写法

### 文件命名
- 组件文件：PascalCase (例如：`AccountList.tsx`)
- 工具文件：kebab-case (例如：`api-client.ts`)
- 页面文件：小写 (例如：`page.tsx`)

### Git提交
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 🐛 问题排查

### 开发服务器无法启动
- 检查端口3000是否被占用
- 删除 `.next` 文件夹并重新启动
- 检查 Node.js 版本

### API请求失败
- 确认后端服务运行在 http://localhost:8000
- 检查 `.env.local` 配置
- 查看浏览器控制台错误

### 类型错误
- 运行 `npm run type-check`
- 检查 `types/index.ts` 类型定义
- 确保后端API响应与类型定义一致

## 📚 相关文档

- [Next.js文档](https://nextjs.org/docs)
- [Tailwind CSS文档](https://tailwindcss.com/docs)
- [TypeScript文档](https://www.typescriptlang.org/docs)
- [Radix UI文档](https://www.radix-ui.com/docs)

## 📄 许可证

MIT License

---

**开发者**: OutlookManager Team  
**版本**: 3.0.0  
**最后更新**: 2025-10-29

