# 用户密码修改功能说明

## 功能概述

管理员现在可以在用户管理页面直接修改任何用户的密码，无需知道用户的旧密码。

## 更新内容

### 1. 后端 API

#### 新增模型 (`models.py`)

```python
class PasswordUpdateRequest(BaseModel):
    """修改密码请求模型"""
    
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")
```

#### 新增 API 端点 (`admin_api.py`)

**端点**: `PUT /admin/users/{username}/password`

**权限**: 仅管理员

**请求体**:
```json
{
  "new_password": "newpassword123"
}
```

**响应**:
```json
{
  "message": "用户 {username} 密码修改成功"
}
```

**功能**:
- 验证管理员权限
- 检查用户是否存在
- 对新密码进行哈希处理
- 更新数据库中的密码

### 2. 前端界面

#### 用户列表操作按钮

在用户管理页面的每个用户行中，添加了"改密码"按钮：

```
[编辑] [改密码] [删除]
```

#### 修改密码模态框

新增了一个独立的模态框用于修改密码，包含：

1. **用户名** (只读，显示要修改密码的用户)
2. **新密码** (必填，至少6位)
3. **确认密码** (必填，必须与新密码一致)

#### JavaScript 函数

- `changePassword(username)` - 打开修改密码模态框
- `closePasswordModal()` - 关闭修改密码模态框
- `handlePasswordSubmit(event)` - 处理密码修改提交

### 3. 密码验证

前端验证：
- ✅ 新密码长度至少6位
- ✅ 两次输入的密码必须一致
- ✅ 不能为空

后端验证：
- ✅ 管理员权限检查
- ✅ 用户存在性检查
- ✅ 密码长度验证（Pydantic 模型）
- ✅ 密码哈希处理（使用 bcrypt）

## 使用方法

### 管理员修改用户密码

1. 登录管理员账户
2. 进入"管理面板" → "用户管理"
3. 在用户列表中找到要修改密码的用户
4. 点击该用户行的"改密码"按钮
5. 在弹出的模态框中：
   - 确认用户名（自动填充）
   - 输入新密码（至少6位）
   - 再次输入新密码确认
6. 点击"确认修改"
7. 系统提示"密码修改成功"

## 安全特性

### 1. 权限控制
- ✅ 仅管理员可以修改密码
- ✅ 使用 JWT Token 验证身份
- ✅ 每次请求都验证管理员权限

### 2. 密码安全
- ✅ 密码使用 bcrypt 哈希存储
- ✅ 前端不显示原密码
- ✅ 传输过程中使用 HTTPS（生产环境）
- ✅ 密码长度限制（最少6位）

### 3. 用户体验
- ✅ 独立的修改密码界面
- ✅ 密码二次确认
- ✅ 实时验证提示
- ✅ 操作成功/失败通知

## API 测试

### 使用 curl 测试

```bash
# 修改用户密码
curl -X PUT "http://localhost:8000/admin/users/testuser/password" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "newpassword123"
  }'
```

### 预期响应

成功：
```json
{
  "message": "用户 testuser 密码修改成功"
}
```

失败（非管理员）：
```json
{
  "detail": "需要管理员权限"
}
```

失败（用户不存在）：
```json
{
  "detail": "用户 testuser 不存在"
}
```

## 数据库变更

无需数据库结构变更，使用现有的 `update_user_password` 函数。

## 文件变更清单

### 修改的文件

1. **models.py**
   - 新增 `PasswordUpdateRequest` 模型

2. **admin_api.py**
   - 导入 `PasswordUpdateRequest`
   - 新增 `update_user_password` API 端点

3. **static/user-management.html**
   - 添加"改密码"按钮到用户列表
   - 新增修改密码模态框 HTML
   - 新增 `changePassword()` 函数
   - 新增 `closePasswordModal()` 函数
   - 新增 `handlePasswordSubmit()` 函数
   - 添加模态框外部点击关闭事件

### 未修改的文件

- `database.py` - 已有 `update_user_password` 函数
- `auth.py` - 已有 `hash_password` 函数

## 注意事项

1. **管理员自己的密码**: 管理员也可以修改自己的密码，但建议使用"个人设置"中的修改密码功能（如果有）

2. **密码强度**: 当前只要求最少6位，建议在生产环境中增加密码强度要求（大小写、数字、特殊字符等）

3. **密码重置通知**: 当前没有邮件通知功能，建议在修改密码后通知用户

4. **操作日志**: 建议记录密码修改操作的审计日志

## 后续改进建议

1. ✨ 增加密码强度要求（大小写字母、数字、特殊字符）
2. ✨ 添加密码强度指示器
3. ✨ 发送密码修改通知邮件给用户
4. ✨ 记录密码修改操作日志
5. ✨ 添加"生成随机密码"功能
6. ✨ 支持批量重置密码
7. ✨ 密码修改历史记录
8. ✨ 强制用户首次登录修改密码

## 测试检查清单

- [x] 管理员可以成功修改用户密码
- [x] 普通用户无法访问修改密码 API
- [x] 密码长度验证正常工作
- [x] 两次密码不一致时提示错误
- [x] 修改不存在的用户时返回404错误
- [x] 修改后用户可以使用新密码登录
- [x] 模态框可以正常打开和关闭
- [x] 点击模态框外部可以关闭
- [x] 成功/失败通知正常显示

## 版本信息

- **功能版本**: v1.0
- **添加日期**: 2025-11-02
- **作者**: AI Assistant
- **状态**: ✅ 已完成并测试

---

**相关文档**:
- [用户权限系统完整文档](./USER_PERMISSION_SYSTEM_COMPLETE.md)
- [用户管理快速开始](./USER_MANAGEMENT_QUICK_START.md)

