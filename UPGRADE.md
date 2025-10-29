# Outlook邮件管理系统 v2.0 升级指南

## 📋 升级概述

本次升级（v1.0 → v2.0）带来以下重大改进：

### 🎯 新功能
1. ✅ **JWT管理员认证** - 安全的访问控制
2. ✅ **滚动日志系统** - 30天日志保留，自动清理
3. ✅ **SQLite数据库** - 替代JSON文件存储
4. ✅ **管理面板** - 可视化管理所有数据表
5. ✅ **系统配置管理** - 动态配置系统参数

---

## 🚀 快速升级步骤

### 1. 安装新依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- `python-jose[cryptography]` - JWT认证
- `passlib[bcrypt]` - 密码加密
- `python-multipart` - 表单数据处理

### 2. 数据迁移

运行迁移脚本，将现有 `accounts.json` 数据迁移到SQLite数据库：

```bash
python migrate.py
```

迁移脚本会：
- 创建SQLite数据库表结构
- 迁移所有账户数据
- 创建默认管理员账户
- 初始化系统配置

**默认管理员凭据：**
- 用户名：`admin`
- 密码：`admin123`
- **⚠️ 请首次登录后立即修改密码！**

### 3. 启动应用

```bash
# 直接启动
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 首次登录

1. 访问登录页面：http://localhost:8000/static/login.html
2. 使用默认凭据登录
3. 立即修改密码（在管理面板或使用API）

---

## 🐳 Docker 升级

### 更新配置

`docker-compose.yml` 已更新，新增日志卷挂载：

```yaml
volumes:
  - ./data.db:/app/data.db        # 数据库文件
  - ./logs:/app/logs              # 日志目录
  - ./accounts.json:/app/accounts.json  # 迁移用
```

### 重新构建和启动

```bash
# 停止旧容器
docker-compose down

# 重新构建镜像
docker-compose build

# 启动新容器
docker-compose up -d
```

### 在容器中运行迁移

```bash
# 进入容器
docker exec -it outlook-email-api sh

# 运行迁移脚本
python migrate.py

# 退出容器
exit
```

---

## 📊 新功能使用指南

### 1. 管理员登录

访问：`http://localhost:8000/static/login.html`

登录后会自动跳转到主页面，所有API调用会自动携带JWT token。

### 2. 管理面板

登录后，在主页面左侧菜单可以找到"管理面板"选项。

管理面板功能：
- 📋 查看所有数据表
- ✏️ 直接编辑表数据（增删改查）
- ⚙️ 管理系统配置
- 👥 管理管理员账户

### 3. API认证

所有API端点（除登录接口外）现在都需要JWT认证：

```bash
# 获取token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 使用token访问API
curl -X GET http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. 密码管理

**通过API修改密码：**

```bash
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "admin123", "new_password": "new_secure_password"}'
```

### 5. 查看日志

日志文件位于 `logs/outlook_manager.log`

```bash
# 查看最新日志
tail -f logs/outlook_manager.log

# 查看特定日期的日志
ls logs/
# outlook_manager.log.2024-01-15
```

日志会自动按天轮转，保留30天后自动删除。

---

## 🗂️ 数据库管理

### 查看数据库

```bash
# 安装 sqlite3（如果没有）
# Ubuntu/Debian: sudo apt install sqlite3
# macOS: 自带

# 打开数据库
sqlite3 data.db

# 查看所有表
.tables

# 查看表结构
.schema accounts

# 查询数据
SELECT * FROM accounts;

# 退出
.quit
```

### 备份数据库

```bash
# 备份数据库文件
cp data.db data.db.backup

# 或使用SQLite导出
sqlite3 data.db .dump > backup.sql
```

### 恢复数据库

```bash
# 从备份文件恢复
cp data.db.backup data.db

# 或从SQL导入
sqlite3 data.db < backup.sql
```

---

## 🔧 配置管理

### 系统配置项

系统配置存储在 `system_config` 表中，可通过管理面板或API修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `IMAP_SERVER` | outlook.office365.com | IMAP服务器地址 |
| `IMAP_PORT` | 993 | IMAP服务器端口 |
| `MAX_CONNECTIONS` | 5 | 每个邮箱的最大连接数 |
| `CONNECTION_TIMEOUT` | 30 | 连接超时时间（秒） |
| `SOCKET_TIMEOUT` | 15 | Socket超时时间（秒） |
| `CACHE_EXPIRE_TIME` | 60 | 缓存过期时间（秒） |
| `TOKEN_REFRESH_INTERVAL` | 3 | Token刷新间隔（天） |
| `LOG_RETENTION_DAYS` | 30 | 日志保留天数 |

### 通过API更新配置

```bash
curl -X PUT http://localhost:8000/admin/config/MAX_CONNECTIONS \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "10", "description": "最大连接数"}'
```

---

## ❗ 注意事项

### 1. 数据迁移
- ✅ 迁移成功后，建议备份 `accounts.json` 为 `accounts.json.backup`
- ✅ 确认所有数据迁移正确后，可以删除旧的JSON文件
- ⚠️ 不要在迁移过程中同时运行旧版和新版应用

### 2. 安全性
- 🔒 立即修改默认管理员密码
- 🔒 JWT密钥默认是随机生成的，重启后会改变（可通过环境变量固定）
- 🔒 生产环境建议使用HTTPS

### 3. 性能
- 📈 SQLite适合中小规模使用（< 1000个账户）
- 📈 大规模使用建议迁移到PostgreSQL或MySQL
- 📈 日志文件会占用磁盘空间，注意监控

### 4. 兼容性
- ⚠️ 所有API调用现在都需要JWT token
- ⚠️ 前端应用需要处理登录和token刷新
- ⚠️ 旧版的直接文件访问不再有效

---

## 🆘 故障排查

### 问题：无法登录

```bash
# 重置管理员密码
python -c "
import database as db
import auth
db.init_database()
db.update_admin_password('admin', auth.hash_password('admin123'))
print('密码已重置为: admin123')
"
```

### 问题：迁移失败

```bash
# 删除数据库重新迁移
rm data.db
python migrate.py
```

### 问题：Token失效

- Token有效期为24小时
- 清除浏览器中的 `auth_token`，重新登录
- 检查服务器时间是否正确

### 问题：日志不记录

```bash
# 检查日志目录权限
ls -la logs/
chmod 777 logs/

# 检查磁盘空间
df -h
```

---

## 📞 获取帮助

- 📖 查看API文档：http://localhost:8000/docs
- 🐛 报告问题：创建 GitHub Issue
- 💬 技术支持：查看项目README

---

**升级完成后，您的系统将拥有更强大的安全性、可维护性和扩展性！** 🎉

