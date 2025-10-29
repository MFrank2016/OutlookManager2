# 前端快速启动指南

## 🚀 5分钟快速启动

### 1. 安装依赖

```bash
cd frontend
npm install
```

如果使用 yarn 或 pnpm：
```bash
yarn install
# 或
pnpm install
```

### 2. 配置环境

创建 `.env.local` 文件：

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

或手动创建文件并添加以下内容：
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 访问应用

打开浏览器访问 http://localhost:3000

默认登录凭证：
- **用户名**: admin
- **密码**: admin123

## ✅ 启动检查清单

- [ ] Node.js 18+ 已安装
- [ ] 依赖安装完成
- [ ] 环境变量已配置
- [ ] 后端服务运行在 http://localhost:8000
- [ ] 开发服务器启动成功
- [ ] 可以访问登录页面

## 🔧 常见问题

### 端口被占用

如果 3000 端口被占用，可以指定其他端口：

```bash
PORT=3001 npm run dev
```

### 依赖安装失败

尝试清理缓存并重新安装：

```bash
rm -rf node_modules package-lock.json
npm install
```

### 无法连接后端

1. 确认后端服务正在运行：
```bash
curl http://localhost:8000/health
```

2. 检查 `.env.local` 中的 API URL 配置

3. 查看浏览器控制台是否有 CORS 错误

## 📁 目录结构

```
frontend/
├── app/              # 页面和路由
├── lib/              # 工具函数
├── types/            # TypeScript类型
├── public/           # 静态资源
└── package.json      # 项目配置
```

## 🎯 下一步

- 浏览仪表板了解系统概况
- 在"账户管理"添加Outlook账户
- 在"邮件管理"查看邮件列表

## 💡 开发技巧

### 热重载

修改代码后，页面会自动刷新，无需手动重启服务器。

### TypeScript检查

在开发时运行类型检查：

```bash
npm run type-check
```

### 代码格式化

使用 Prettier 格式化代码：

```bash
npm run format
```

## 📚 更多信息

查看完整文档：[README.md](./README.md)

