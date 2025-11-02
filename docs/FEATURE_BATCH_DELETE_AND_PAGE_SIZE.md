# 批量删除账户和分页大小设置功能

## 功能概述

本次更新为账户管理页面添加了两个重要功能：
1. **批量删除账户** - 支持选择多个账户并一次性删除
2. **分页大小设置** - 允许用户自定义每页显示的账户数量

## 功能详情

### 1. 批量删除账户

#### 前端功能
- **全选复选框**：位于统计信息栏左侧，可一键选择/取消选择当前页所有账户
- **单选复选框**：每个账户行前都有复选框，可单独选择
- **批量删除按钮**：选中账户后自动显示在页面头部，显示已选数量
- **已选计数**：实时显示已选择的账户数量

#### 后端API
- **端点**: `POST /accounts/batch-delete`
- **权限**: 需要管理员权限
- **请求体**:
  ```json
  {
    "email_ids": ["email1@example.com", "email2@example.com"]
  }
  ```
- **响应**:
  ```json
  {
    "total_processed": 2,
    "success_count": 2,
    "failed_count": 0,
    "details": [
      {
        "email": "email1@example.com",
        "status": "success",
        "message": "Account deleted successfully"
      }
    ]
  }
  ```

#### 使用流程
1. 在账户列表页面勾选要删除的账户
2. 点击页面头部出现的"批量删除"按钮
3. 确认删除操作
4. 系统显示删除结果（成功/失败数量）
5. 自动刷新账户列表

### 2. 分页大小设置

#### 功能特点
- **位置**：统计信息栏右侧
- **选项**：10、20、50、100 条/页
- **持久化**：切换后立即生效，重新加载第一页
- **自动清空选择**：切换分页大小时自动清空已选账户

#### 实现细节
- 使用下拉选择器，样式美观
- 切换时清空缓存，确保数据准确
- 响应式设计，移动端友好

## 技术实现

### 数据模型 (models.py)
```python
class BatchDeleteRequest(BaseModel):
    """批量删除账户请求模型"""
    email_ids: List[str] = Field(..., description="要删除的邮箱账户列表")

class BatchDeleteResult(BaseModel):
    """批量删除结果模型"""
    total_processed: int
    success_count: int
    failed_count: int
    details: List[dict]
```

### 路由处理 (routes/account_routes.py)
- 新增 `batch_delete_accounts` 端点
- 循环处理每个账户的删除
- 记录成功/失败详情
- 返回详细的批量操作结果

### 前端交互 (accounts.js)
- `selectedAccounts` Set 存储已选账户
- `toggleSelectAll()` 全选/取消全选
- `toggleAccountSelection()` 单个账户选择
- `updateBatchDeleteButton()` 更新按钮显示状态
- `batchDeleteAccounts()` 执行批量删除
- `changePageSize()` 切换分页大小

### 样式设计 (accounts.css)
- `.accounts-stats-bar` 统计信息栏布局
- `.batch-select-container` 全选复选框样式
- `.page-size-selector` 分页大小选择器样式
- `.account-cell-with-checkbox` 账户行复选框布局
- 响应式设计适配移动端

## 用户体验优化

1. **视觉反馈**
   - 选中账户后按钮自动显示
   - 实时显示已选数量
   - 删除过程中显示加载状态

2. **操作确认**
   - 批量删除前显示确认对话框
   - 列出前5个待删除账户
   - 显示总数量

3. **结果通知**
   - 成功：显示成功删除数量
   - 部分失败：显示成功和失败数量
   - 完全失败：显示错误信息

4. **自动清理**
   - 删除后自动清空选择
   - 自动刷新列表
   - 切换分页时清空选择

## 安全性

1. **权限控制**：批量删除需要管理员权限
2. **二次确认**：删除前需要用户确认
3. **详细日志**：记录所有批量删除操作
4. **错误处理**：单个账户删除失败不影响其他账户

## 兼容性

- ✅ 桌面端浏览器（Chrome, Firefox, Safari, Edge）
- ✅ 移动端浏览器（iOS Safari, Android Chrome）
- ✅ 响应式布局自适应
- ✅ 向后兼容现有功能

## 更新日期

2025-11-02

## 作者

Outlook Manager Team

