# 验证码规则引擎设计

## 目标

为 OutlookManager2 增加一套可配置、可测试、可追踪的验证码识别系统，覆盖：

- 后端规则引擎
- 识别结果落库
- 管理面板规则 CRUD + 实时测试
- 主站邮件页 / 分享页自动复制并提醒

## 核心约束

- 定向规则优先于通用规则
- 同层规则按优先级从高到低
- 命中第一条即停止
- 单条规则支持 `AND / OR`
- 多候选验证码优先取离关键词最近的
- 成功识别必须记录到数据库
- 分享页与主站邮件页使用一致的自动复制提醒逻辑

## 架构

### 1. 规则层

新增 `verification_rules` 表：

- `scope_type`: `targeted` / `global`
- `match_mode`: `and` / `or`
- `sender_pattern`
- `subject_pattern`
- `body_pattern`
- `extract_pattern`
- `is_regex`
- `priority`
- `enabled`

### 2. 识别执行层

新增 `verification_rule_service.py`，统一负责：

- 规则读取与排序
- 发件人 / 主题 / 正文 / HTML 文本归一化
- 规则命中判断
- 提取正则执行
- fallback 到内置 `verification_code_detector.py`
- 识别结果和命中过程整理

### 3. 记录层

新增 `verification_detection_records` 表，只记录成功识别：

- `email_account`
- `message_id`
- `detected_code`
- `rule_id`
- `rule_name`
- `source` (`runtime` / `test`)
- `page_source`
- `matched_sender`
- `matched_subject`
- `matched_body_excerpt`
- `created_at`

同时继续把最终 `verification_code` 回写到：

- `emails_cache`
- `email_details_cache`

## 运行时链路

### 主邮件页 / 分享页

1. 后端拉取邮件
2. 规则引擎识别验证码
3. 成功后写入缓存字段 + 检测记录
4. 前端发现新的 `message_id + verification_code`
5. 自动复制到剪贴板并 toast 提醒

### 管理面板测试链路

1. 管理员选择账号与指定邮件
2. 后端抓取该邮件详情
3. 运行单条规则或全量规则链
4. 返回详细命中过程
5. 若成功，写入 `verification_detection_records (source=test)`，但不污染正式邮件缓存

## 分阶段实现

### 第一阶段

- 表结构
- DAO / service
- 运行时识别落库
- 管理端 API

### 第二阶段

- 管理面板规则页
- 实时测试面板

### 第三阶段

- 主站邮件页自动复制提醒
- 分享页自动复制提醒

## 验证标准

- `pytest tests -q` 继续通过
- `npm run lint` 不新增 error
- 规则优先级、AND/OR、fallback、落库有自动化测试
- 管理端可创建 / 编辑 / 删除 / 测试规则
- 主站页与分享页都能在首次发现新验证码时自动复制并提醒
