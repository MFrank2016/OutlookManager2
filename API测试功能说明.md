# 🚀 API测试功能说明

## 功能概述

已为所有15个API端点添加了**试用接口**功能，支持在浏览器中直接测试API，无需额外工具。

## ✨ 功能特性

### 1. **完整的API测试支持**
- ✅ 支持所有HTTP方法（GET、POST、DELETE）
- ✅ 支持路径参数编辑
- ✅ 支持查询参数编辑
- ✅ 支持请求体JSON编辑
- ✅ 自动JWT Token认证
- ✅ 实时响应展示

### 2. **参数编辑能力**
- 📝 **路径参数** - 可编辑文本框（如：email_id、table_name）
- 🔍 **查询参数** - 根据类型自动选择输入框：
  - 文本参数：文本输入框
  - 数字参数：数字输入框
  - 布尔参数：复选框
- 📄 **请求体** - JSON编辑器（自动格式化）

### 3. **智能认证处理**
- 🔐 需要JWT的接口：自动携带Token
- 🌐 无需认证的接口：直接请求
- ⏱️ Token过期自动提示

### 4. **友好的交互界面**
- 🎨 美观的模态框设计
- 📊 实时响应结果展示（JSON格式化）
- ✅ 成功/错误状态区分（绿色/红色）
- 🔄 一键重置表单
- 📋 响应结果支持复制

## 📋 支持的API列表

### 🔐 认证管理（3个）

| 端点 | 方法 | 配置Key | 可编辑参数 |
|------|------|---------|------------|
| `/auth/login` | POST | `login` | 请求体（username, password） |
| `/auth/me` | GET | `me` | 无 |
| `/auth/change-password` | POST | `changePassword` | 请求体（old_password, new_password） |

### 👥 账户管理（4个）

| 端点 | 方法 | 配置Key | 可编辑参数 |
|------|------|---------|------------|
| `/accounts` | GET | `accounts` | 查询参数（page, page_size, email_search, tag_search） |
| `/accounts` | POST | `addAccount` | 请求体（email_id, refresh_token, client_id, tags） |
| `/accounts/{email_id}` | DELETE | `deleteAccount` | 路径参数（email_id） |
| `/accounts/{email_id}/refresh-token` | POST | `refreshToken` | 路径参数（email_id） |

### 📧 邮件管理（2个）

| 端点 | 方法 | 配置Key | 可编辑参数 |
|------|------|---------|------------|
| `/emails/{email_id}` | GET | `emails` | 路径参数（email_id）<br>查询参数（folder, page, page_size, refresh） |
| `/emails/{email_id}/{message_id}` | GET | `emailDetail` | 路径参数（email_id, message_id） |

### ⚙️ 管理面板（5个）

| 端点 | 方法 | 配置Key | 可编辑参数 |
|------|------|---------|------------|
| `/admin/tables/{table_name}/count` | GET | `tableCount` | 路径参数（table_name） |
| `/admin/tables/{table_name}` | GET | `tableData` | 路径参数（table_name） |
| `/admin/tables/{table_name}/{record_id}` | DELETE | `deleteTableRecord` | 路径参数（table_name, record_id） |
| `/admin/config` | GET | `getConfig` | 无 |
| `/admin/config` | POST | `updateConfig` | 请求体（key, value, description） |

### 📊 系统信息（1个）

| 端点 | 方法 | 配置Key | 可编辑参数 |
|------|------|---------|------------|
| `/api` | GET | `systemInfo` | 无 |

## 🎯 使用方法

### 1. **访问API文档页面**
```
http://localhost:8001
→ 点击左侧 "📖 API管理" 菜单
```

### 2. **测试API**
1. 找到要测试的API端点
2. 点击右侧的 **🚀 试用接口** 按钮
3. 在弹出的测试窗口中：
   - 查看/编辑路径参数
   - 查看/编辑查询参数
   - 编辑JSON请求体（如适用）
4. 点击 **▶️ 发送请求** 按钮
5. 查看响应结果

### 3. **参数编辑示例**

#### 示例1：测试获取账户列表
```javascript
// 点击 "GET /accounts" 的 "试用接口" 按钮
// 编辑查询参数：
page: 1
page_size: 20
email_search: outlook.com
tag_search: 工作

// 点击 "发送请求" 查看结果
```

#### 示例2：测试添加账户
```javascript
// 点击 "POST /accounts" 的 "试用接口" 按钮
// 编辑请求体：
{
  "email_id": "test@outlook.com",
  "refresh_token": "your_refresh_token_here",
  "client_id": "your_client_id_here",
  "tags": ["测试", "个人"]
}

// 点击 "发送请求" 查看结果
```

#### 示例3：测试删除账户
```javascript
// 点击 "DELETE /accounts/{email_id}" 的 "试用接口" 按钮
// 编辑路径参数：
email_id: test@outlook.com

// 点击 "发送请求" 查看结果
```

#### 示例4：测试管理员登录（无需Token）
```javascript
// 点击 "POST /auth/login" 的 "试用接口" 按钮
// 编辑请求体：
{
  "username": "admin",
  "password": "admin123"
}

// 点击 "发送请求" 获取Token
```

## 💡 高级功能

### 1. **重置表单**
点击 **🔄 重置** 按钮恢复默认参数值

### 2. **JSON格式验证**
- 请求体JSON格式错误会自动提示
- 自动美化JSON显示（2空格缩进）

### 3. **响应状态识别**
- ✅ **成功响应** - 绿色背景，JSON格式化显示
- ❌ **错误响应** - 红色背景，错误信息显示

### 4. **快捷键支持**（待实现）
- `Ctrl+Enter` - 发送请求
- `Esc` - 关闭测试窗口

## 🔧 技术实现

### API配置对象
```javascript
const API_CONFIGS = {
    'apiKey': {
        method: 'GET|POST|DELETE',
        endpoint: '/api/path/{param}',
        path: { param: 'default_value' },      // 路径参数
        query: { key: 'value' },               // 查询参数
        body: { key: 'value' },                // 请求体
        requiresAuth: true|false               // 是否需要JWT
    }
}
```

### 参数类型识别
```javascript
// 自动根据参数类型选择输入控件
typeof value === 'boolean' → checkbox
typeof value === 'number'  → number input
typeof value === 'string'  → text input
Array/Object              → JSON textarea
```

### JWT自动处理
```javascript
if (config.requiresAuth) {
    // 使用现有的 apiRequest() 函数，自动携带Token
    response = await apiRequest(url, options);
} else {
    // 无需认证，直接fetch
    response = await fetch(API_BASE + url, options);
}
```

## 📱 界面截图（描述）

### 测试窗口布局
```
┌─────────────────────────────────────────┐
│ 🚀 测试API: /accounts                 × │
├─────────────────────────────────────────┤
│ 请求信息                                 │
│ 方法: GET                                │
│ 端点: /accounts                          │
│                                          │
│ 查询参数 ▼                               │
│ ┌────────────────────┐                  │
│ │ page          [1  ]│                  │
│ │ page_size     [10 ]│                  │
│ │ email_search  [   ]│                  │
│ │ tag_search    [   ]│                  │
│ └────────────────────┘                  │
│                                          │
│ 响应结果 ▼                               │
│ ┌────────────────────────────────────┐  │
│ │ {                                  │  │
│ │   "total_accounts": 25,            │  │
│ │   "accounts": [...]                │  │
│ │ }                                  │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [▶️ 发送请求] [🔄 重置] [✖️ 关闭]        │
└─────────────────────────────────────────┘
```

## 🌟 优势

### 对比Postman/cURL
- ✅ 无需安装额外工具
- ✅ 自动集成JWT认证
- ✅ 参数默认值预填充
- ✅ 响应实时展示
- ✅ 与文档无缝集成

### 对比Swagger UI
- ✅ 更现代的UI设计
- ✅ 中文界面
- ✅ 自定义参数默认值
- ✅ 轻量级实现

## 🔍 调试技巧

### 1. **查看请求详情**
打开浏览器开发者工具（F12）→ Network标签，查看实际发送的请求

### 2. **Token过期处理**
如果收到401错误：
1. 重新访问登录页面：`/static/login.html`
2. 使用`admin`/`admin123`登录
3. 返回继续测试

### 3. **JSON格式错误**
请求体必须是有效的JSON：
```json
❌ 错误: { key: value }
✅ 正确: { "key": "value" }
```

## 📊 统计信息

- **总API端点数**：15个
- **支持试用的端点**：15个（100%）
- **可编辑参数类型**：路径参数、查询参数、请求体
- **HTTP方法支持**：GET、POST、DELETE
- **认证方式**：JWT Token（自动）

## 🚀 未来增强

- [ ] 添加请求历史记录
- [ ] 支持批量测试
- [ ] 导出为cURL命令
- [ ] 导出为Postman Collection
- [ ] 请求/响应时间统计
- [ ] 快捷键支持
- [ ] 响应结果语法高亮
- [ ] 参数自动完成

---

📅 **创建日期**：2025-10-29  
🔖 **版本**：v2.0.0  
👨‍💻 **作者**：AI Assistant

