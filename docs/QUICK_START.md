# 快速开始指南

## 🚀 一键启动（推荐）

### Windows
```cmd
run.bat
```

### Linux/Mac
```bash
chmod +x run.sh
./run.sh
```

脚本会自动：
- ✅ 检查Python环境
- ✅ 创建虚拟环境
- ✅ 安装依赖包
- ✅ 迁移旧数据（如果有）
- ✅ 初始化数据库
- ✅ 启动应用

---

## 🐳 Docker部署

### 1. 构建并启动
```bash
docker-compose up -d
```

### 2. 进入容器运行迁移（首次启动）
```bash
docker exec -it outlook-email-api python migrate.py
```

### 3. 查看日志
```bash
docker logs -f outlook-email-api
```

---

## 📦 手动安装

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行数据迁移（如果从v1.0升级）
```bash
python migrate.py
```

### 3. 启动应用
```bash
python main.py
```

---

## 🌐 访问系统

启动成功后，在浏览器访问：

- **主页面**: http://localhost:8000
- **登录页面**: http://localhost:8000/static/login.html  
- **API文档**: http://localhost:8000/docs

### 默认管理员账户

- **用户名**: `admin`
- **密码**: `admin123`  
- ⚠️ **请首次登录后立即修改密码！**

---

## 🔐 修改密码

### 方式1：通过API（推荐）

```bash
# 1. 登录获取token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. 使用token修改密码
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "admin123", "new_password": "your_new_password"}'
```

### 方式2：通过数据库（紧急情况）

```bash
python -c "import database as db; import auth; db.update_admin_password('admin', auth.hash_password('new_password')); print('密码已重置')"
```

---

## 📊 数据管理

### 查看数据库
```bash
sqlite3 data.db

# 查看所有表
.tables

# 查看账户
SELECT email, refresh_status FROM accounts;

# 退出
.quit
```

### 备份数据
```bash
# 备份数据库文件
cp data.db data.db.backup.$(date +%Y%m%d)

# 或导出SQL
sqlite3 data.db .dump > backup.sql
```

---

## 🔧 常用操作

### 添加邮箱账户
通过登录后的web界面，或使用API：

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@outlook.com",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "client_id": "YOUR_CLIENT_ID",
    "tags": ["工作"]
  }'
```

### 查看日志
```bash
# 实时查看日志
tail -f logs/outlook_manager.log

# 查看最近100行
tail -n 100 logs/outlook_manager.log

# 搜索错误日志
grep ERROR logs/outlook_manager.log
```

### 清除缓存
```bash
curl -X DELETE http://localhost:8000/cache \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ❗ 故障排查

### 问题：端口8000被占用
```bash
# Linux/Mac
lsof -i :8000
kill -9 PID

# Windows
netstat -ano | findstr :8000
taskkill /PID PID /F

# 或修改端口
# 编辑 main.py 末尾的 PORT = 8001
```

### 问题：无法登录
```bash
# 重置管理员密码
python -c "import database as db; import auth; db.init_database(); db.update_admin_password('admin', auth.hash_password('admin123')); print('密码已重置为: admin123')"
```

### 问题：数据库损坏
```bash
# 备份旧数据库
mv data.db data.db.old

# 重新迁移
python migrate.py
```

---

## 📞 获取帮助

- 📖 **详细升级指南**: 查看 `UPGRADE.md`
- 🐛 **问题报告**: 创建 GitHub Issue
- 💬 **API文档**: http://localhost:8000/docs

---

**祝使用愉快！** 🎉

