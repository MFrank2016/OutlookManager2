# 用户权限管理 - 快速开始指南

## 🚀 5分钟快速上手

### 第一步：启动系统

```bash
# 启动应用
python main.py
```

系统会自动：
- ✅ 检测并迁移旧的 `admins` 表到 `users` 表
- ✅ 创建默认管理员账户（如果不存在）
- ✅ 初始化权限系统

### 第二步：管理员登录

1. 打开浏览器访问: `http://localhost:8000/static/login.html`
2. 使用默认管理员账户登录：
   - **用户名**: `admin`
   - **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

### 第三步：创建普通用户

#### 方法1: 通过用户管理页面（推荐）

1. 登录后，点击侧边栏的 **"管理面板"**
2. 点击 **"用户管理"** 标签
3. 点击 **"打开用户管理页面"** 按钮
4. 在新页面中点击 **"➕ 创建用户"**
5. 填写用户信息：

```
用户名: testuser
密码: test123456
邮箱: test@example.com (可选)
角色: 普通用户
权限: ☑️ 查看邮件
      ☑️ 发送邮件
      ☑️ 删除邮件
绑定账户: ☑️ user1@outlook.com
         ☑️ user2@outlook.com
账户启用: ☑️
```

6. 点击 **"创建用户"**

#### 方法2: 通过 API

```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456",
    "email": "test@example.com",
    "role": "user",
    "is_active": true,
    "permissions": ["view_emails", "send_emails", "delete_emails"],
    "bound_accounts": ["user1@outlook.com", "user2@outlook.com"]
  }'
```

### 第四步：测试普通用户登录

1. 退出管理员账户（点击侧边栏底部的"退出登录"）
2. 使用新创建的普通用户登录：
   - **用户名**: `testuser`
   - **密码**: `test123456`

3. 验证权限：
   - ✅ 只能看到绑定的邮箱账户（user1@outlook.com, user2@outlook.com）
   - ✅ 不能看到其他账户
   - ✅ 不能访问管理面板
   - ✅ 操作按钮根据权限显示

---

## 📋 常见场景

### 场景1: 为用户添加更多权限

1. 以管理员身份登录
2. 进入用户管理页面
3. 找到目标用户，点击 **"编辑"**
4. 在"权限配置"中勾选需要的权限
5. 点击 **"保存更改"**

### 场景2: 为用户绑定新的邮箱账户

1. 以管理员身份登录
2. 进入用户管理页面
3. 找到目标用户，点击 **"编辑"**
4. 在"绑定账户"中勾选新的账户
5. 点击 **"保存更改"**

### 场景3: 禁用用户账户

1. 以管理员身份登录
2. 进入用户管理页面
3. 找到目标用户，点击 **"编辑"**
4. 取消勾选 **"账户启用"**
5. 点击 **"保存更改"**

该用户将无法登录，但数据保留。

### 场景4: 将普通用户提升为管理员

1. 以管理员身份登录
2. 进入用户管理页面
3. 找到目标用户，点击 **"编辑"**
4. 将"角色"改为 **"管理员"**
5. 点击 **"保存更改"**

⚠️ 管理员拥有所有权限，无需单独配置。

### 场景5: 修改密码

#### 用户自己修改密码：
1. 登录后点击右上角用户名
2. 选择"修改密码"
3. 输入旧密码和新密码
4. 确认修改

#### 管理员重置用户密码：
目前需要通过 API 或数据库直接操作。

---

## 🔐 权限说明

### 可配置的权限

| 权限代码 | 权限名称 | 说明 |
|---------|---------|------|
| `view_emails` | 查看邮件 | 查看绑定账户的邮件列表和详情 |
| `send_emails` | 发送邮件 | 发送邮件 |
| `delete_emails` | 删除邮件 | 删除邮件 |
| `manage_accounts` | 管理账户 | 修改账户标签等信息 |
| `view_admin_panel` | 访问管理面板 | 查看管理面板（通常只给管理员） |
| `manage_users` | 管理用户 | 创建、编辑、删除用户（仅管理员） |
| `manage_cache` | 管理缓存 | 清除缓存 |
| `manage_config` | 管理系统配置 | 修改系统配置（仅管理员） |

### 推荐的权限组合

#### 只读用户
```
✅ view_emails
```

#### 普通用户
```
✅ view_emails
✅ send_emails
✅ delete_emails
```

#### 高级用户
```
✅ view_emails
✅ send_emails
✅ delete_emails
✅ manage_accounts
✅ manage_cache
```

#### 管理员
```
✅ 所有权限（自动拥有）
```

---

## 🎯 最佳实践

### 1. 账户管理

- ✅ 为每个实际用户创建独立账户
- ✅ 使用强密码（至少8位，包含字母、数字、符号）
- ✅ 定期审查用户权限
- ✅ 及时禁用离职人员账户

### 2. 权限分配

- ✅ 遵循"最小权限原则"
- ✅ 只授予必要的权限
- ✅ 定期审查和调整权限
- ✅ 记录权限变更原因

### 3. 账户绑定

- ✅ 根据实际工作需要绑定账户
- ✅ 避免过度授权
- ✅ 定期审查绑定关系
- ✅ 及时解除不需要的绑定

### 4. 安全建议

- ✅ 首次登录后立即修改默认密码
- ✅ 定期更新密码
- ✅ 不要共享账户
- ✅ 退出时记得点击"退出登录"
- ✅ 在公共电脑上使用后清除浏览器缓存

---

## 🔍 故障排查

### 问题1: 创建用户时提示"用户名已存在"

**解决方案**: 更换一个不同的用户名。

### 问题2: 普通用户登录后看不到任何账户

**原因**: 没有为该用户绑定账户。

**解决方案**:
1. 管理员登录
2. 编辑该用户
3. 在"绑定账户"中选择账户
4. 保存更改

### 问题3: 用户无法执行某些操作

**原因**: 缺少相应权限。

**解决方案**:
1. 管理员登录
2. 编辑该用户
3. 在"权限配置"中添加需要的权限
4. 保存更改

### 问题4: 忘记管理员密码

**解决方案**:
```bash
# 方法1: 使用 Python 脚本重置
python -c "
import database as db
db.update_user_password('admin', 'new_password_here')
print('密码已重置')
"

# 方法2: 直接操作数据库
sqlite3 data.db
UPDATE users SET password_hash = '<bcrypt_hash>' WHERE username = 'admin';
```

---

## 📊 用户管理界面说明

### 用户列表

显示所有用户的基本信息：
- **ID**: 用户唯一标识
- **用户名**: 登录用户名
- **邮箱**: 用户邮箱（可选）
- **角色**: 管理员/普通用户
- **绑定账户数**: 该用户可访问的邮箱账户数量
- **状态**: 启用/禁用
- **创建时间**: 账户创建时间
- **操作**: 编辑/删除按钮

### 筛选和搜索

- **搜索框**: 输入用户名或邮箱进行搜索
- **角色筛选**: 按管理员/普通用户筛选
- **重置筛选**: 清除所有筛选条件

### 创建/编辑用户

**必填字段**:
- 用户名（创建时）
- 密码（创建时）
- 角色

**可选字段**:
- 邮箱
- 权限配置（普通用户）
- 绑定账户（普通用户）
- 账户启用状态

**注意事项**:
- 用户名创建后不可修改
- 编辑时不需要重新输入密码
- 管理员自动拥有所有权限，无需配置
- 普通用户必须绑定账户才能使用系统

---

## 🎓 进阶使用

### 使用 API 管理用户

#### 获取 Token

```bash
# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')
```

#### 获取用户列表

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/admin/users?page=1&page_size=20"
```

#### 创建用户

```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123",
    "email": "newuser@example.com",
    "role": "user",
    "permissions": ["view_emails"],
    "bound_accounts": ["user@outlook.com"]
  }'
```

#### 更新用户

```bash
curl -X PUT http://localhost:8000/admin/users/newuser \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "updated@example.com",
    "permissions": ["view_emails", "send_emails"]
  }'
```

#### 删除用户

```bash
curl -X DELETE http://localhost:8000/admin/users/newuser \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📞 获取帮助

- 📖 查看完整文档: [USER_PERMISSION_SYSTEM_COMPLETE.md](./USER_PERMISSION_SYSTEM_COMPLETE.md)
- 🐛 报告问题: 查看日志文件 `logs/outlook_manager.log`
- 💡 功能建议: 提交 GitHub Issue

---

**祝使用愉快！** 🎉
