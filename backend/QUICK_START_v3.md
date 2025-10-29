# Outlook邮件管理系统 v3.0 - 快速开始

## 🚀 5分钟快速启动

### 1. 安装依赖（1分钟）

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库（1分钟）

```bash
python scripts/init_database.py
```

按提示操作：
- 输入 `y` 创建默认管理员
- 默认用户名：`admin`
- 默认密码：`admin123`

### 3. 启动服务（10秒）

```bash
python run_dev.py
```

看到这个输出表示成功：
```
======================================================================
  Outlook Email Manager - Development Server
======================================================================
  Environment: Development
  API Docs: http://localhost:8000/api/docs
  Health Check: http://localhost:8000/health
======================================================================
```

### 4. 测试API（1分钟）

访问：http://localhost:8000/api/docs

#### 登录获取Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

会返回：
```json
{
  "success": true,
  "access_token": "eyJ...",
  "token_type": "Bearer",
  ...
}
```

#### 使用Token访问API

```bash
# 获取系统统计
curl http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 创建账户
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@outlook.com",
    "refresh_token": "your_refresh_token",
    "client_id": "your_client_id",
    "tags": ["test"]
  }'
```

## 📚 完整文档

- **架构说明**：`backend/README_v3.md`
- **完成总结**：`backend/FINAL_COMPLETION_SUMMARY.md`
- **API文档**：http://localhost:8000/api/docs

## 🎯 所有可用API端点

### 认证
- `POST /api/v1/auth/login` - 登录
- `POST /api/v1/auth/change-password` - 修改密码

### 账户管理
- `POST /api/v1/accounts` - 创建账户
- `GET /api/v1/accounts` - 获取列表
- `GET /api/v1/accounts/{id}` - 获取详情
- `PATCH /api/v1/accounts/{id}` - 更新账户
- `DELETE /api/v1/accounts/{id}` - 删除账户
- `POST /api/v1/accounts/{id}/refresh-token` - 刷新Token

### 邮件管理
- `GET /api/v1/emails` - 获取邮件列表
- `GET /api/v1/emails/{message_id}` - 获取邮件详情
- `POST /api/v1/emails/search` - 搜索邮件

### 管理员
- `GET /api/v1/admin/profile` - 获取个人信息
- `PATCH /api/v1/admin/profile` - 更新个人信息
- `GET /api/v1/admin/stats` - 获取系统统计

### 系统
- `GET /health` - 健康检查
- `GET /api/v1/ping` - Ping测试

## 🔧 常见问题

### Q: 如何创建新的管理员？
```bash
python scripts/create_admin.py
```

### Q: 如何运行测试？
```bash
pytest
```

### Q: 如何查看日志？
日志文件在 `logs/outlook_manager.log`

### Q: 如何修改配置？
创建 `.env` 文件（参考 `.env.example`），修改配置项

## ⚠️ 安全提示

在生产环境部署前：
1. ✅ 修改默认管理员密码
2. ✅ 修改 JWT_SECRET_KEY
3. ✅ 使用 PostgreSQL 替代 SQLite
4. ✅ 启用 HTTPS
5. ✅ 配置防火墙

## 🎉 开始使用

现在你已经准备好了！访问 http://localhost:8000/api/docs 开始探索吧！

**祝你使用愉快！** 🚀

