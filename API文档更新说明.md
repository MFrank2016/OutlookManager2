# 📚 API文档更新说明

## 更新概览

✅ API文档已全面更新，反映系统v2.0.0的最新API列表和功能。

## 🔄 主要更新内容

### 1. **基础信息更新**
- ✅ 认证方式：更新为JWT Token认证
- ✅ 版本信息：v2.0.0
- ✅ 状态码说明：详细的HTTP状态码解释
- ✅ 认证头格式：`Authorization: Bearer <token>`

### 2. **新增API分类**

#### 🔐 认证管理 (Authentication)
```
POST   /auth/login              # 管理员登录
GET    /auth/me                 # 获取当前用户信息
POST   /auth/change-password    # 修改密码
```

#### 👥 账户管理 (Account Management)
```
GET    /accounts                # 获取账户列表
POST   /accounts                # 添加账户
DELETE /accounts/{email_id}     # 删除账户
POST   /accounts/{email_id}/refresh-token  # 手动刷新Token
```

#### 📧 邮件管理 (Email Management)
```
GET    /emails/{email_id}                # 获取邮件列表
GET    /emails/{email_id}/{message_id}   # 获取邮件详情
```

#### ⚙️ 管理面板 (Admin Panel)
```
GET    /admin/tables/{table_name}/count     # 获取表记录数
GET    /admin/tables/{table_name}           # 获取表数据
DELETE /admin/tables/{table_name}/{id}      # 删除表记录
GET    /admin/config                        # 获取系统配置
POST   /admin/config                        # 更新系统配置
```

#### 📊 系统信息 (System Info)
```
GET    /api                     # 获取系统状态（无需认证）
```

## 📝 详细API列表

### 认证相关（3个端点）

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/login` | 管理员登录，返回JWT Token | ❌ 无需 |
| GET | `/auth/me` | 获取当前登录用户信息 | ✅ 需要 |
| POST | `/auth/change-password` | 修改当前用户密码 | ✅ 需要 |

### 账户管理（4个端点）

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/accounts` | 获取账户列表（支持分页、搜索） | ✅ 需要 |
| POST | `/accounts` | 添加新账户 | ✅ 需要 |
| DELETE | `/accounts/{email_id}` | 删除指定账户 | ✅ 需要 |
| POST | `/accounts/{email_id}/refresh-token` | 手动刷新Token | ✅ 需要 |

### 邮件管理（2个端点）

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/emails/{email_id}` | 获取邮件列表（支持分页、文件夹过滤） | ✅ 需要 |
| GET | `/emails/{email_id}/{message_id}` | 获取邮件详情（HTML/纯文本） | ✅ 需要 |

### 管理面板（5个端点）

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/admin/tables/{table_name}/count` | 获取表记录数 | ✅ 需要 |
| GET | `/admin/tables/{table_name}` | 获取表数据 | ✅ 需要 |
| DELETE | `/admin/tables/{table_name}/{id}` | 删除表记录 | ✅ 需要 |
| GET | `/admin/config` | 获取所有配置 | ✅ 需要 |
| POST | `/admin/config` | 创建/更新配置 | ✅ 需要 |

### 系统信息（1个端点）

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api` | 获取系统版本和状态 | ❌ 无需 |

## 🎯 文档特性

### 1. **清晰的分类结构**
- 📡 API基础信息
- 🔐 认证管理
- 👥 账户管理
- 📧 邮件管理（原有）
- ⚙️ 管理面板（新增）
- 📊 系统信息（新增）

### 2. **完整的接口说明**
每个API端点包含：
- HTTP方法和路径
- 接口描述
- 请求参数（路径参数、查询参数、请求体）
- 响应示例（JSON格式）
- 参数类型和说明

### 3. **可视化元素**
- 🎨 HTTP方法徽章（GET、POST、DELETE等）
- 📋 参数表格
- 💻 代码示例框
- 🎯 分类标题图标

### 4. **用户友好特性**
- 📋 复制Base URL按钮
- 📥 下载文档按钮（功能已预留）
- 🚀 试用接口按钮（部分端点）
- 实时响应展示区域

## 🔑 JWT认证说明

### 获取Token
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 使用Token
```bash
curl -X GET http://localhost:8001/accounts \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token特性
- ⏱️ 有效期：24小时
- 🔄 自动刷新：需要重新登录
- 🔒 安全性：HS256算法加密
- 📦 存储位置：LocalStorage

## 📱 API调用示例

### Python示例

```python
import requests

# 1. 登录获取Token
login_response = requests.post(
    'http://localhost:8001/auth/login',
    json={'username': 'admin', 'password': 'admin123'}
)
token = login_response.json()['access_token']

# 2. 使用Token调用API
headers = {'Authorization': f'Bearer {token}'}
accounts = requests.get(
    'http://localhost:8001/accounts',
    headers=headers
)
print(accounts.json())
```

### JavaScript示例

```javascript
// 1. 登录获取Token
const loginResponse = await fetch('http://localhost:8001/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
    })
});
const { access_token } = await loginResponse.json();

// 2. 使用Token调用API
const accountsResponse = await fetch('http://localhost:8001/accounts', {
    headers: {'Authorization': `Bearer ${access_token}`}
});
const accounts = await accountsResponse.json();
console.log(accounts);
```

## 🚀 快速开始

1. **启动服务**：
   ```bash
   python main.py
   ```

2. **访问API文档**：
   - 浏览器打开：http://localhost:8001
   - 点击左侧"📖 API管理"菜单

3. **查看交互式文档**：
   - FastAPI自动文档：http://localhost:8001/docs
   - ReDoc文档：http://localhost:8001/redoc

## 📊 统计信息

- **API总数**：15个端点
- **认证端点**：3个
- **账户管理**：4个
- **邮件管理**：2个
- **管理面板**：5个
- **系统信息**：1个
- **需要认证**：14个
- **无需认证**：1个（/api）

## 🔄 版本历史

### v2.0.0 (2025-10-29)
- ✅ 新增JWT认证系统
- ✅ 新增管理面板API
- ✅ 新增系统信息API
- ✅ 更新所有API文档
- ✅ 添加认证说明
- ✅ 完善请求/响应示例

### v1.0.0
- 基础账户管理
- 邮件列表和详情查询

---

📅 **最后更新**：2025-10-29  
🔖 **文档版本**：v2.0.0  
👨‍💻 **维护者**：AI Assistant

