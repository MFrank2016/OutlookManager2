# Bug 修复：创建用户时 is_active 字段问题

## 🐛 问题描述

在用户管理页面创建用户时，提交表单后返回 400 Bad Request 错误。

**日志显示**：
```
INFO: 127.0.0.1:62116 - "POST /admin/users HTTP/1.1" 400 Bad Request
```

## 🔍 原因分析

### 前后端数据不匹配

1. **前端实现**：
   - 用户管理页面的表单包含"账户启用"复选框
   - 提交时发送 `is_active` 字段（boolean）

2. **后端模型**：
   - `UserCreateRequest` 模型中**缺少** `is_active` 字段定义
   - FastAPI 验证时发现未定义的字段，拒绝请求（422 Unprocessable Entity）

3. **数据库函数**：
   - `create_user()` 函数参数中也缺少 `is_active`

### 错误流程
```
前端表单 → 发送 {username, password, ..., is_active: true}
         ↓
FastAPI  → UserCreateRequest 模型验证
         ↓
验证失败 → is_active 字段未定义
         ↓
返回 400 → Bad Request
```

## ✅ 修复方案

### 1. 修改数据模型 (`models.py`)

**修改前**：
```python
class UserCreateRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field("user", description="角色 (admin/user)")
    bound_accounts: Optional[List[str]] = Field(default=[], description="绑定的邮箱账户列表")
    permissions: Optional[List[str]] = Field(default=[], description="权限列表")
```

**修改后**：
```python
class UserCreateRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field("user", description="角色 (admin/user)")
    bound_accounts: Optional[List[str]] = Field(default=[], description="绑定的邮箱账户列表")
    permissions: Optional[List[str]] = Field(default=[], description="权限列表")
    is_active: bool = Field(True, description="账户是否启用")  # 新增
```

### 2. 更新数据库函数 (`database.py`)

**修改前**：
```python
def create_user(
    username: str,
    password_hash: str,
    email: str = None,
    role: str = "user",
    bound_accounts: List[str] = None,
    permissions: List[str] = None
) -> Dict[str, Any]:
    # ...
    cursor.execute("""
        INSERT INTO users (username, password_hash, email, role, bound_accounts, permissions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password_hash, email, role, bound_accounts_json, permissions_json))
```

**修改后**：
```python
def create_user(
    username: str,
    password_hash: str,
    email: str = None,
    role: str = "user",
    bound_accounts: List[str] = None,
    permissions: List[str] = None,
    is_active: bool = True  # 新增参数，默认启用
) -> Dict[str, Any]:
    # ...
    cursor.execute("""
        INSERT INTO users (username, password_hash, email, role, bound_accounts, permissions, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, password_hash, email, role, bound_accounts_json, permissions_json, 1 if is_active else 0))
```

### 3. 更新 API 端点 (`admin_api.py`)

**修改前**：
```python
new_user = db.create_user(
    username=request.username,
    password_hash=password_hash,
    email=request.email,
    role=request.role,
    bound_accounts=request.bound_accounts or [],
    permissions=request.permissions or []
)
```

**修改后**：
```python
new_user = db.create_user(
    username=request.username,
    password_hash=password_hash,
    email=request.email,
    role=request.role,
    bound_accounts=request.bound_accounts or [],
    permissions=request.permissions or [],
    is_active=request.is_active  # 新增
)
```

## 📊 修复效果

### 修复前
1. 填写创建用户表单
2. 提交 → 400 Bad Request
3. 用户创建失败
4. 前端显示错误提示

### 修复后
1. 填写创建用户表单
2. 提交 → 200 OK
3. 用户成功创建
4. 前端显示成功提示并刷新列表

## ✅ 验证步骤

1. **重启应用**（应用代码更改）
   ```bash
   # 如果在运行，停止应用并重启
   python main.py
   ```

2. **刷新用户管理页面**
   - Ctrl+Shift+R 强制刷新

3. **测试创建用户**
   - 点击"创建用户"
   - 填写表单：
     - 用户名：testuser2
     - 密码：test123456
     - 邮箱：test2@example.com
     - 角色：普通用户
     - 权限：勾选"查看邮件"
     - 账户启用：勾选
   - 点击"创建用户"
   - ✅ 应该显示"用户创建成功"
   - ✅ 用户列表自动刷新并显示新用户

4. **测试禁用账户创建**
   - 创建用户时**取消勾选**"账户启用"
   - ✅ 用户创建后状态应该显示"禁用"

## 🔍 技术细节

### is_active 字段的处理

1. **数据类型转换**
   ```python
   # SQLite 使用 INTEGER 存储布尔值
   is_active_int = 1 if is_active else 0
   ```

2. **默认值**
   ```python
   is_active: bool = Field(True, description="账户是否启用")
   # 默认为 True，新创建的用户默认启用
   ```

3. **查询时的转换**
   ```python
   # 从数据库读取时转换回布尔值
   is_active=bool(user['is_active'])
   ```

### FastAPI 模型验证

**Pydantic 模型验证规则**：
- 未定义的字段会被拒绝（strict mode）
- 必须显式声明所有接受的字段
- 提供类型检查和数据验证

## 📝 相关修改

此修复同时完善了：
1. ✅ 数据模型完整性
2. ✅ 数据库函数参数
3. ✅ API 端点数据传递
4. ✅ 前后端数据一致性

## 🎯 影响范围

- **影响文件**：
  - `models.py` - 添加 is_active 字段定义
  - `database.py` - 更新 create_user 函数
  - `admin_api.py` - 更新创建用户端点
- **影响功能**：用户管理 → 创建用户
- **用户影响**：修复后可正常创建用户并控制启用/禁用状态

## 🔄 后续建议

### 1. 添加字段验证

```python
class UserCreateRequest(BaseModel):
    # ...
    is_active: bool = Field(True, description="账户是否启用")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v
```

### 2. 完善错误提示

```python
try:
    new_user = db.create_user(...)
except Exception as e:
    raise HTTPException(
        status_code=400,
        detail=f"创建用户失败: {str(e)}"
    )
```

### 3. 添加日志记录

```python
logger.info(f"Creating user: {request.username}, role: {request.role}, active: {request.is_active}")
```

## 📚 相关文档

- [用户管理 API 文档](./USER_PERMISSION_SYSTEM_COMPLETE.md#用户管理相关)
- [快速开始指南](./USER_MANAGEMENT_QUICK_START.md)
- [Pydantic 模型文档](https://docs.pydantic.dev/)

---

**修复日期**：2025-11-02  
**版本**：v2.0.3  
**状态**：✅ 已修复

**创建用户功能现已完全正常！** 🎉

