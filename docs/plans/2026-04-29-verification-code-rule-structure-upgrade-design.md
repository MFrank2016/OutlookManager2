# 验证码规则结构升级设计

## 背景

当前 `OutlookManager2` 的验证码规则仍是单条字段模型：

- `sender_pattern`
- `subject_pattern`
- `body_pattern`
- `extract_pattern`

它已经能完成基础识别，但存在三个明显限制：

1. 一条规则内只能表达非常有限的匹配条件。
2. “是否处理这封邮件” 与 “从哪里提取验证码” 混在一起，语义不清。
3. 管理端测试页只能从下拉列表选择邮件，无法直接输入 `message_id` 做定点测试。

同时，用户希望在邮件页面更直接地看到邮件 ID，方便在测试页复用。

## 目标

本次升级聚焦四件事：

1. 优化验证码匹配功能。
2. 一条规则支持多条匹配规则。
3. 提取规则可明确选择来源：从主题提取、从内容提取。
4. 在邮件页面展示邮件 ID，并在验证码测试页支持手动指定邮件 ID。

## 最终规则语义

一条验证码规则由两部分组成：

### 1. 匹配规则列表

用于判断“这封邮件是否应该进入验证码提取阶段”。

每条匹配规则包含：

- `source_type`: `sender` / `subject` / `body`
- `keyword`: 关键词
- `sort_order`: 排序值（仅用于界面稳定展示）

匹配语义固定为：

- **任意一条匹配规则命中即可进入提取阶段**
- 匹配规则只支持“关键词包含”，不引入正则

### 2. 提取规则列表

用于判断“应该从哪里以及如何提取验证码”。

每条提取规则包含：

- `source_type`: `subject` / `body`
- `extract_pattern`: 正则表达式
- `sort_order`: 顺序值

提取语义固定为：

- **按顺序依次尝试提取**
- **第一条成功提取到验证码的规则直接返回结果**

## 运行时执行流程

后端统一构造邮件上下文：

- `from_email`
- `subject`
- `body_text`

然后执行如下流程：

1. 载入启用规则，按优先级从高到低遍历。
2. 对当前规则执行匹配规则列表：
   - 任意 matcher 命中，则该规则进入提取阶段。
   - 若全部未命中，则当前规则未命中，继续下一个规则。
3. 对已命中的规则执行提取规则列表：
   - 按 `sort_order` 顺序逐条尝试。
   - 第一条成功提取即返回结果。
4. 若匹配阶段命中，但全部 extractor 提取失败：
   - 记录“匹配命中但未提取成功”的调试信息。
   - 继续下一个验证码规则，或最终进入 fallback。
5. 若所有配置规则均未得到结果，则继续沿用已有 fallback 检测逻辑。

这样可以把“要不要处理”与“怎么提取”彻底分离，规则语义更稳定，也更容易解释测试结果。

## 数据模型改造

建议把当前单表结构升级为“规则主表 + 两张子表”。

### 主表：`verification_rules`

保留并收敛为：

- `id`
- `name`
- `priority`
- `enabled`
- `description`
- `created_at`
- `updated_at`

移除旧模型中的：

- `scope_type`
- `match_mode`
- `sender_pattern`
- `subject_pattern`
- `body_pattern`
- `extract_pattern`
- `is_regex`

### 子表：`verification_rule_matchers`

字段建议：

- `id`
- `rule_id`
- `source_type`
- `keyword`
- `sort_order`
- `created_at`
- `updated_at`

### 子表：`verification_rule_extractors`

字段建议：

- `id`
- `rule_id`
- `source_type`
- `extract_pattern`
- `sort_order`
- `created_at`
- `updated_at`

### 迁移策略

为避免现有规则丢失，升级时执行一次轻量迁移：

- 若旧规则存在 `sender_pattern`，迁移为一条 `sender matcher`
- 若旧规则存在 `subject_pattern`，迁移为一条 `subject matcher`
- 若旧规则存在 `body_pattern`，迁移为一条 `body matcher`
- 旧 `extract_pattern` 迁移为一条 extractor，默认来源 `body`

迁移完成后，运行时与前端均只使用新结构，不保留双写逻辑。

## 后端服务与 API 设计

### Service 层

`verification_rule_service.py` 改为围绕新结构工作：

- 加载规则主表 + matcher 列表 + extractor 列表
- 输出结构化测试过程：
  - 命中的 matcher
  - 尝试过的 extractor 顺序
  - 最终验证码来源
- 继续支持成功识别记录落库

### 管理端规则 CRUD API

保留现有路径，不改 URL：

- `GET /admin/verification-rules`
- `POST /admin/verification-rules`
- `PUT /admin/verification-rules/{rule_id}`
- `DELETE /admin/verification-rules/{rule_id}`

但请求/响应体改为嵌套结构，例如：

```json
{
  "name": "Microsoft 登录验证码",
  "priority": 100,
  "enabled": true,
  "description": "微软主题验证码",
  "matchers": [
    { "source_type": "sender", "keyword": "microsoft", "sort_order": 1 },
    { "source_type": "subject", "keyword": "security code", "sort_order": 2 }
  ],
  "extractors": [
    { "source_type": "subject", "extract_pattern": "(\\d{6})", "sort_order": 1 },
    { "source_type": "body", "extract_pattern": "(\\d{6})", "sort_order": 2 }
  ]
}
```

### 管理端测试 API

继续保留：

- `POST /admin/verification-rules/test`

请求体保持一个最终生效的 `message_id` 字段：

```json
{
  "email_account": "demo@example.com",
  "message_id": "AAMkAG...",
  "rule_id": 12
}
```

前端规则：

- 若“手输邮件 ID”有值，则优先把该值作为 `message_id`
- 若输入框为空，则使用下拉选中的邮件 ID

响应体新增：

- `matched_matchers`
- `extractor_attempts`
- `resolved_code_source`（`subject` / `body` / `fallback`）

## 前端交互设计

### 1. 验证码规则编辑器

把当前单表单升级成规则编辑器。

#### 基础信息区

- 规则名称
- 优先级
- 启用状态
- 描述

#### 匹配规则列表区

- 支持新增 / 删除
- 每条包含：
  - 来源：发件人 / 主题 / 内容
  - 关键词
- 区块提示文案：**任意一条命中即可进入提取**

#### 提取规则列表区

- 支持新增 / 删除
- 每条包含：
  - 来源：主题 / 内容
  - 提取正则
- 区块提示文案：**按顺序依次提取，命中即停止**

### 2. 验证码测试面板

保留现有两类入口，并新增手动覆盖能力：

- 账号下拉选择
- 邮件下拉列表
- 手输 `message_id` 输入框

交互优先级：

1. 手输 `message_id`
2. 下拉选择邮件

下拉项展示内容建议包括：

- 主题
- 发件人
- `message_id`
- 已识别验证码（如有）

测试结果中应清楚展示：

- 命中的 matcher
- 尝试过的 extractor
- 最终验证码
- 命中来源
- 原始 JSON

### 3. 邮件页展示邮件 ID

邮件 ID 应做到“列表可见，详情完整”。

#### 桌面邮件列表

在主题/预览区追加一行弱化小字：

- `ID: <message_id>`

#### 移动端卡片

在卡片信息区补一行：

- `ID: <message_id>`

#### 邮件详情弹窗

当前已有邮件 ID 展示，继续保留，并补一个复制按钮，降低手动复制成本。

## 错误处理

需要覆盖以下场景：

1. 规则没有 matcher
   - 保存时直接阻止，提示至少配置一条匹配规则。
2. 规则没有 extractor
   - 保存时直接阻止，提示至少配置一条提取规则。
3. extractor 正则非法
   - 后端校验失败，前端显示明确错误信息。
4. 手输 `message_id` 不存在
   - 测试接口返回 404，并提示具体账号/邮件 ID。
5. 规则匹配成功但提取失败
   - 返回结构化调试信息，不要只给“未识别”一句话。

## 自动化测试方案

### 后端单元测试

至少覆盖：

1. 任意 matcher 命中即可进入提取阶段。
2. subject extractor 优先于 body extractor。
3. 第一个 extractor 失败时会继续尝试后续 extractor。
4. matcher 命中但 extractor 全失败时会正确进入 fallback。
5. 测试接口支持使用手动指定的 `message_id`。
6. 旧规则数据能正确迁移为新结构。

### 管理 API 测试

至少覆盖：

1. 新建带多个 matcher / extractor 的规则。
2. 更新规则顺序与内容。
3. 删除规则后子项一并清理。
4. 指定账号 + 下拉邮件测试。
5. 指定账号 + 手输 `message_id` 测试。

### 前端验证

至少完成：

1. `npm run lint -- --max-warnings=0`
2. 规则编辑器增删 matcher / extractor 无报错
3. 测试页手输 `message_id` 时优先于下拉选择
4. 邮件列表与详情页稳定显示邮件 ID

## 实施建议

建议按以下顺序落地：

1. 数据表与 DAO 改造
2. `verification_rule_service.py` 重构
3. 管理端 API 调整
4. 规则编辑器 UI 重构
5. 测试页手输 `message_id` 支持
6. 邮件页 ID 展示优化
7. 单测、API 测试、lint 验证

这样可以先把核心语义收稳，再补界面与交互，不会出现前端先改完、后端结构却还没定型的问题。
