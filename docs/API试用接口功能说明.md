# API试用接口功能说明

## 功能概述

为Outlook邮件管理系统的所有API端点添加了**试用接口**功能，用户可以直接在API文档页面测试所有API端点，无需使用第三方工具。

## 更新时间
2024年10月30日

---

## 已支持的API端点

### 📝 认证API（3个）

1. **POST /auth/login** - 管理员登录
2. **GET /auth/me** - 获取当前管理员信息
3. **POST /auth/change-password** - 修改密码

### 👥 账户管理API（7个）

1. **GET /accounts** - 获取账户列表（支持多维度筛选）
2. **POST /accounts** - 添加新账户
3. **DELETE /accounts/{email_id}** - 删除账户
4. **PUT /accounts/{email_id}/tags** - 更新账户标签
5. **POST /accounts/{email_id}/refresh-token** - 单个账户刷新Token
6. **POST /accounts/batch-refresh-tokens** - 批量刷新Token
7. **POST /accounts/{email_id}/refresh-token** (refreshToken) - 手动刷新Token

### 📧 邮件管理API（3个）

1. **GET /emails/{email_id}** - 获取邮件列表
2. **GET /emails/{email_id}/{message_id}** - 获取邮件详情
3. **GET /emails/{email_id}/dual-view** - 获取双栏视图邮件

### 🗄️ 管理面板API（5个）

1. **GET /admin/tables/{table_name}/count** - 获取表记录数
2. **GET /admin/tables/{table_name}** - 获取表数据
3. **DELETE /admin/tables/{table_name}/{record_id}** - 删除表记录
4. **GET /admin/config** - 获取系统配置
5. **POST /admin/config** - 更新系统配置

### 🗑️ 缓存管理API（2个）

1. **DELETE /cache/{email_id}** - 清除指定邮箱缓存
2. **DELETE /cache** - 清除所有缓存

### 📊 系统信息API（1个）

1. **GET /api** - 获取系统状态

---

## 使用方法

### 1. 访问API文档页面

在Web界面中点击侧边栏的"📚 API文档"菜单项，或直接访问：
```
http://localhost:8000
```
然后在导航栏选择"API文档"。

### 2. 选择要测试的API

每个API端点右侧都有一个"🚀 试用接口"按钮，点击即可打开测试界面。

### 3. 填写参数

根据API要求填写：

- **路径参数**：如 `email_id`、`message_id` 等
- **查询参数**：如 `page`、`page_size`、`folder` 等
- **请求体**：JSON格式的请求数据

### 4. 执行测试

点击"发送请求"按钮，系统会：
1. 自动添加认证Token（如果需要）
2. 构建完整的API请求
3. 发送请求到后端
4. 显示响应结果

### 5. 查看结果

响应结果会实时显示在测试界面中，包括：
- HTTP状态码
- 响应数据（JSON格式化）
- 错误信息（如果有）

---

## 功能特点

### ✨ 完整覆盖
- 所有21个API端点都支持试用
- 包括认证、账户、邮件、管理、缓存等全部功能

### 🔐 自动认证
- 无需认证的API（如登录）直接调用
- 需要认证的API自动附加JWT Token
- Token自动从当前会话获取

### 📝 参数预填
- 所有参数都有默认示例值
- 可以直接使用默认值测试
- 也可以修改为实际值

### 🎨 友好界面
- 清晰的参数分组（路径参数、查询参数、请求体）
- JSON语法高亮
- 实时响应显示

### 🔄 快速重置
- 点击"重置表单"恢复默认值
- 关闭对话框保留当前输入
- 方便反复测试

---

## 示例场景

### 场景1：测试登录API

1. 点击"POST /auth/login"的"试用接口"按钮
2. 默认值已经填好：
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
3. 点击"发送请求"
4. 查看返回的JWT Token

### 场景2：测试获取账户列表

1. 先登录获取Token（自动保存）
2. 点击"GET /accounts"的"试用接口"按钮
3. 修改查询参数：
   - `page`: 1
   - `page_size`: 10
   - `refresh_status`: `failed`（只看失败的）
4. 点击"发送请求"
5. 查看筛选后的账户列表

### 场景3：测试批量刷新Token

1. 点击"POST /accounts/batch-refresh-tokens"的"试用接口"按钮
2. 设置查询参数：
   - `refresh_status`: `failed`（只刷新失败的账户）
   - `email_search`: ``（留空表示所有）
3. 点击"发送请求"
4. 查看批量刷新结果统计

### 场景4：测试获取邮件

1. 点击"GET /emails/{email_id}"的"试用接口"按钮
2. 填写路径参数：
   - `email_id`: 实际的邮箱地址
3. 设置查询参数：
   - `folder`: `inbox`
   - `page`: 1
   - `page_size`: 20
4. 点击"发送请求"
5. 查看邮件列表

---

## 技术实现

### API配置对象

每个API端点都在`API_CONFIGS`对象中配置：

```javascript
const API_CONFIGS = {
    'batchRefreshTokens': {
        method: 'POST',
        endpoint: '/accounts/batch-refresh-tokens',
        query: {
            email_search: '',
            tag_search: '',
            refresh_status: '',
            time_filter: '',
            after_date: ''
        },
        requiresAuth: true
    },
    // ... 更多配置
};
```

### 参数类型

支持三种参数类型：

1. **path**：路径参数，会替换URL中的占位符
   ```javascript
   path: { email_id: 'example@outlook.com' }
   ```

2. **query**：查询参数，会添加到URL后面
   ```javascript
   query: { page: 1, page_size: 10 }
   ```

3. **body**：请求体，JSON格式
   ```javascript
   body: { username: 'admin', password: 'admin123' }
   ```

### 认证处理

```javascript
if (config.requiresAuth) {
    response = await apiRequest(url, options);
} else {
    response = await fetch(url, options);
}
```

---

## API端点清单

### 需要认证的API（18个）

所有这些API都需要JWT Token认证：

- GET /auth/me
- POST /auth/change-password
- GET /accounts
- POST /accounts
- DELETE /accounts/{email_id}
- PUT /accounts/{email_id}/tags
- POST /accounts/{email_id}/refresh-token
- POST /accounts/batch-refresh-tokens
- GET /emails/{email_id}
- GET /emails/{email_id}/{message_id}
- GET /emails/{email_id}/dual-view
- DELETE /cache/{email_id}
- DELETE /cache
- GET /admin/tables/{table_name}/count
- GET /admin/tables/{table_name}
- DELETE /admin/tables/{table_name}/{record_id}
- GET /admin/config
- POST /admin/config

### 无需认证的API（3个）

这些API可以直接调用：

- POST /auth/login（登录）
- GET /api（系统信息）

---

## 注意事项

### 🔐 认证要求

- 大部分API需要先登录获取Token
- Token有效期为24小时
- Token过期后需要重新登录

### 📝 参数格式

- 邮箱地址需要URL编码（自动处理）
- 日期格式使用ISO 8601（如：2024-01-01T12:00:00）
- JSON请求体必须格式正确

### ⚠️ 测试注意

- DELETE操作会真实删除数据，请谨慎使用
- 批量操作可能耗时较长，请耐心等待
- 测试环境建议使用测试账户

---

## 相关文件

- `static/index.html` - 前端实现（API测试模态框、配置对象）
- `main.py` - 后端API端点
- `docs/API试用接口功能说明.md` - 本文档

---

## 未来改进

可以考虑的功能增强：

1. **保存测试历史**
   - 记录最近的测试请求
   - 快速重放历史请求

2. **导出测试用例**
   - 导出为curl命令
   - 导出为Postman collection

3. **批量测试**
   - 一键测试所有API
   - 生成测试报告

4. **响应美化**
   - 更好的JSON格式化
   - 语法高亮
   - 折叠/展开

5. **错误提示**
   - 更友好的错误信息
   - 参数验证提示
   - 示例值建议

---

**所有API试用接口功能已完成！** 🎉

