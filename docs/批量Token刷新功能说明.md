# 批量Token刷新功能说明

## 功能概述

为Outlook邮件管理系统新增了手动批量更新Token的功能，支持多维度筛选和批量操作，提升了系统的可维护性和易用性。

## 主要功能

### 1. 多维度账户筛选

支持以下筛选条件：

#### 刷新状态筛选
- **全部状态**：显示所有账户
- **从未刷新**：显示`last_refresh_time`为空的账户
- **刷新成功**：显示`refresh_status = 'success'`的账户
- **刷新失败**：显示`refresh_status = 'failed'`的账户
- **待刷新**：显示`refresh_status = 'pending'`的账户

#### 时间范围筛选（后端支持，前端可扩展）
- **今日未更新**：最后刷新时间早于今天00:00的账户
- **一周内未更新**：最后刷新时间早于7天前的账户
- **一月内未更新**：最后刷新时间早于30天前的账户
- **自定义日期**：指定日期后未更新的账户

#### 其他筛选条件
- **邮箱搜索**：按邮箱地址模糊搜索
- **标签搜索**：按标签模糊搜索

### 2. 批量刷新Token

- 支持基于当前筛选条件批量刷新Token
- 显示确认对话框，告知将影响的账户数量和筛选条件
- 实时显示刷新进度和结果
- 详细的成功/失败统计和错误信息

## API端点

### 1. GET /accounts（已扩展）

获取账户列表，支持多维度筛选。

**查询参数：**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认10，最大100）
- `email_search`: 邮箱模糊搜索
- `tag_search`: 标签模糊搜索
- `refresh_status`: 刷新状态筛选 (all, never_refreshed, success, failed, pending)
- `time_filter`: 时间过滤器 (today, week, month, custom)
- `after_date`: 自定义日期（ISO格式，配合time_filter=custom使用）

**示例：**
```bash
# 获取所有从未刷新的账户
GET /accounts?refresh_status=never_refreshed

# 获取一周内未更新的失败账户
GET /accounts?refresh_status=failed&time_filter=week

# 搜索特定邮箱的待刷新账户
GET /accounts?email_search=example&refresh_status=pending
```

**响应示例：**
```json
{
  "total_accounts": 15,
  "page": 1,
  "page_size": 10,
  "total_pages": 2,
  "accounts": [
    {
      "email_id": "user@outlook.com",
      "client_id": "xxx",
      "status": "active",
      "tags": ["工作"],
      "last_refresh_time": "2024-01-01T12:00:00",
      "next_refresh_time": "2024-01-04T12:00:00",
      "refresh_status": "success"
    }
  ]
}
```

### 2. POST /accounts/batch-refresh-tokens（新增）

批量刷新符合条件的账户Token。

**查询参数：**（与GET /accounts相同的筛选参数）
- `email_search`: 邮箱模糊搜索
- `tag_search`: 标签模糊搜索
- `refresh_status`: 刷新状态筛选
- `time_filter`: 时间过滤器
- `after_date`: 自定义日期

**示例：**
```bash
# 刷新所有从未刷新的账户
POST /accounts/batch-refresh-tokens?refresh_status=never_refreshed

# 刷新所有失败的账户
POST /accounts/batch-refresh-tokens?refresh_status=failed

# 刷新特定标签的账户
POST /accounts/batch-refresh-tokens?tag_search=工作
```

**响应示例：**
```json
{
  "total_processed": 10,
  "success_count": 8,
  "failed_count": 2,
  "details": [
    {
      "email": "user1@outlook.com",
      "status": "success",
      "message": "Token refreshed successfully"
    },
    {
      "email": "user2@outlook.com",
      "status": "failed",
      "message": "HTTP 400 error refreshing token"
    }
  ]
}
```

## 前端使用

### 1. 账户筛选

在账户管理页面的搜索区域：

1. 输入邮箱关键词（可选）
2. 输入标签关键词（可选）
3. 选择刷新状态筛选器：
   - 全部状态
   - 从未刷新
   - 刷新成功
   - 刷新失败
   - 待刷新
4. 点击"搜索"按钮

### 2. 批量刷新Token

1. 使用筛选器定位需要刷新的账户
2. 点击"批量刷新Token"按钮
3. 确认对话框显示：
   - 当前筛选条件
   - 将要刷新的账户数量
4. 确认后开始批量刷新
5. 完成后显示统计结果

### 3. 单个账户刷新

每个账户卡片都有"刷新Token"按钮，可以单独刷新某个账户。

## 数据库字段

账户表（accounts）中的Token相关字段：

- `last_refresh_time`: 最后刷新时间（ISO格式）
- `next_refresh_time`: 下次刷新时间（ISO格式）
- `refresh_status`: 刷新状态 (pending/success/failed)
- `refresh_error`: 刷新错误信息

## 后台自动刷新

系统后台任务每24小时自动刷新所有账户的Token，无需手动操作。

手动批量刷新适用于以下场景：
- 新添加的账户需要立即验证
- 刷新失败的账户需要重试
- 凭证更新后需要立即刷新
- 系统维护后批量验证账户状态

## 技术实现

### 后端

1. **database.py**
   - 新增 `get_accounts_by_filters()` 函数
   - 支持复杂的SQL查询条件组合
   - 处理时间范围计算

2. **main.py**
   - 扩展 `GET /accounts` 端点
   - 新增 `POST /accounts/batch-refresh-tokens` 端点
   - 新增 `BatchRefreshResult` 模型

### 前端

1. **UI组件**
   - 刷新状态下拉选择器
   - 批量刷新按钮
   - 确认对话框

2. **JavaScript函数**
   - `loadAccounts()`: 支持刷新状态参数
   - `searchAccounts()`: 包含刷新状态条件
   - `showBatchRefreshDialog()`: 显示批量刷新确认对话框
   - `batchRefreshTokens()`: 执行批量刷新操作

## 注意事项

1. **批量操作耗时**：刷新大量账户可能需要较长时间，请耐心等待
2. **错误处理**：单个账户刷新失败不会影响其他账户
3. **日志记录**：所有刷新操作都会记录到日志文件
4. **权限要求**：需要管理员JWT Token认证

## 未来扩展

可以考虑添加的功能：

1. 前端UI支持时间范围筛选器
2. 批量刷新进度条（实时显示）
3. 导出刷新结果报告
4. 定时任务的灵活配置
5. 刷新失败重试机制

## 相关文件

- `database.py`: 数据库查询函数
- `main.py`: API端点实现
- `static/index.html`: 前端UI和JavaScript
- `docs/批量Token刷新功能说明.md`: 本文档

