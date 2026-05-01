# OutlookManager2 微软交互统一与 API v2 设计

## 背景

当前 `OutlookManager2` 已经从早期的单文件、单 IMAP 读取模型，发展为同时支持：

- OAuth2 token 获取与缓存
- IMAP 读取链路
- Microsoft Graph 读取 / 删除 / 发送链路
- 按账户 `api_method` 分流
- LRU + 数据库缓存
- 验证码规则检测
- 批量导入、状态跟踪与后台任务

这套能力已经明显强于旧版 `OutlookManager`，但也带来了新的结构问题：

1. 微软交互策略分散在 `oauth_service.py`、`email_service.py`、`graph_api_service.py`、`account_routes.py` 等多个模块中。
2. `api_method` 同时承担“用户配置”“能力检测结果”“运行时路由依据”三种语义，边界不清。
3. 外部 API 以历史演进为主，缺少统一的预检、能力探测、健康检查与调试语义。
4. 前端、批量导入、分享页、管理接口都在不同层面直接感知 Graph/IMAP 细节。
5. 旧项目里“先验证、再导入”“只试不落库”的轻量交互思路，在新项目中没有被体系化继承。

本次设计目标不是回退到旧架构，而是吸收旧项目更简单、更可控的交互思想，重构出一套统一的微软访问内核，并以双轨方式对外提供更清晰的 API v2。

## 目标

本次设计聚焦六件事：

1. 统一 Outlook/Microsoft 交互内核，把 token、capability、provider 选路、fallback、debug override 统一收口。
2. 吸收旧项目 `verify-only`、`import-verified`、单链路调试思路，补齐账户接入生命周期。
3. 把 `api_method` 从“真相字段”降级为兼容字段，改用 `strategy + capability + health` 模型。
4. 对外新增一套规范化 `v2` API，同时保留 `v1` 兼容层。
5. 前端、批量导入任务、管理接口、分享/邮件访问逻辑统一依赖新服务层。
6. 采用可回滚的阶段式迁移，确保现有用户、旧前端、脚本调用不断服务。

## 非目标

本次设计不包含以下大范围改造：

- 不重做权限与认证模型。
- 不与验证码规则引擎大改并行推进。
- 不同时处理 Docker/compose/部署链路收敛。
- 不在本轮重写分享页产品语义。
- 不移除现有 `v1` API，也不做破坏式升级。

## 参考对比结论

对旧版 `OutlookManager` 的比对显示：

- 旧项目只有两条微软交互链路：
  - `https://login.microsoftonline.com/consumers/oauth2/v2.0/token`
  - `outlook.live.com:993` IMAP
- 旧项目具备两个值得继承的交互思想：
  - `check_only` / `verify-only`：验证 refresh token 与 client_id，但不落库
  - `verify` 与 `import` 解耦：先做预检，再做正式导入

而 `OutlookManager2` 现状已经具备：

- `outlook.office365.com:993` IMAP
- `graph.microsoft.com` 邮件列表、详情、删除、发送
- OAuth2 scope fallback
- `api_method` 探测与缓存
- 多层缓存与错误重试

因此本次统一的核心方向不是“把旧实现搬回来”，而是：

**把旧项目的轻量验证和可调试思路，正式吸收到 `OutlookManager2` 的平台架构中。**

## 总体架构

建议在现有服务层之上增加统一的 **Microsoft Access Layer**，并拆成以下五个角色。

### 1. TokenBroker

职责：

- 统一管理 refresh token → access token
- 管理 IMAP scope / Graph scope 的选择与 fallback
- 统一处理 token 缓存、过期判断、刷新、401 重试
- 统一记录 token 级别错误与最后成功时间

### 2. CapabilityResolver

职责：

- 统一判断账户是否支持 Graph API、IMAP 或两者都可用
- 维护 capability snapshot
- 输出推荐 provider，而不是把 provider 判断散落在上层业务代码里

### 3. MailGateway

职责：

- 对上层暴露统一动作：
  - `list`
  - `detail`
  - `delete`
  - `batch_delete`
  - `send`
- 内部按策略分发到 Graph provider 或 IMAP provider
- 统一记录 provider 选路、fallback 与运行健康状态

### 4. AccountLifecycleService

职责：

- 统一账户生命周期动作：
  - `probe`
  - `register`
  - `import_verified`
  - `refresh`
  - `detect_capability`
  - `health`
- 把“先验证、再保存”的产品语义显式化

### 5. ApiFacade

职责：

- 暴露统一的 `v2` API
- 提供 `v1 adapter` 兼容层
- 负责请求参数、响应模型与内部服务层语义的映射

整体原则是：

**上层按业务动作调用，下层再决定走 Graph 还是 IMAP。**

## API v2 对外契约

建议新增统一前缀：`/api/v2`。

### 一、账户预检与接入

#### `POST /api/v2/accounts/probe`

用途：

- 验证 `refresh_token + client_id` 是否可用
- 不落库
- 仅返回能力与建议

建议响应：

```json
{
  "token_ok": true,
  "capability": {
    "graph_available": true,
    "imap_available": true,
    "recommended_provider": "graph"
  },
  "lifecycle_state": "probed",
  "warnings": []
}
```

#### `POST /api/v2/accounts`

用途：

- 正式注册单账户
- 完整落库并初始化策略、能力、健康状态

#### `POST /api/v2/accounts/import`

用途：

- 批量导入账户
- 支持两种模式：
  - `dry_run`
  - `commit`

`dry_run` 只预检，不写库；`commit` 在预检通过后正式入库。

### 二、账户能力与状态

#### `POST /api/v2/accounts/{email}/capability-detection`

用途：

- 重新探测 Graph / IMAP 可用性
- 更新 capability snapshot

#### `POST /api/v2/accounts/{email}/token-refresh`

用途：

- 主动刷新 token
- 更新 token 与健康状态

#### `GET /api/v2/accounts/{email}/health`

用途：

- 返回账户运行健康摘要
- 给前端、运维、外部脚本排障使用

建议包含：

- 当前 strategy
- capability snapshot
- 最近 provider
- token 是否有效
- 最近错误
- 最近成功时间

### 三、邮件访问

#### `GET /api/v2/accounts/{email}/messages`

统一支持：

- `folder`
- `page`
- `page_size`
- `sender_search`
- `subject_search`
- `sort_by`
- `sort_order`
- `start_time`
- `end_time`
- 调试级 override 参数（见下文）

#### `GET /api/v2/accounts/{email}/messages/{message_id}`

用途：获取统一的邮件详情。

#### `DELETE /api/v2/accounts/{email}/messages/{message_id}`

用途：删除单封邮件。

#### `DELETE /api/v2/accounts/{email}/messages?folder=inbox`

用途：按文件夹批量删除。

#### `POST /api/v2/accounts/{email}/messages/send`

用途：发送邮件。

### 四、调试与策略

#### `GET /api/v2/accounts/{email}/delivery-strategy`

返回：

- `strategy_mode`
- `recommended_provider`
- `last_provider_used`
- `override_active`

#### `POST /api/v2/accounts/{email}/delivery-strategy/override`

用途：

- 临时强制 provider
- 临时跳过缓存
- 仅用于调试与运维

建议支持：

- `provider=auto|graph|imap`
- `skip_cache=true|false`
- `ttl_seconds`

## 统一状态机与选路策略

建议把 provider 决策统一为如下链路：

```text
请求进入
  → 读取请求级 override
  → 读取账户级 strategy_mode
  → 读取 capability snapshot
  → 选择 provider
  → 执行动作
  → 成功则更新 health
  → 失败则按策略 fallback 或记录错误
```

### 优先级规则

#### 1. 请求级 override（最高优先级）

- 只用于调试
- 默认不持久化
- 可选：
  - `provider=graph|imap|auto`
  - `skip_cache=true|false`

#### 2. 账户级 strategy_mode

建议枚举：

- `auto`
- `graph_preferred`
- `imap_only`
- `graph_only`

语义：

- `auto`：系统根据 capability 与健康状态自动选路
- `graph_preferred`：优先 Graph，必要时允许降级 IMAP
- `imap_only`：只走 IMAP，不自动升级
- `graph_only`：只走 Graph，不自动降级

#### 3. capability snapshot

需要维护：

- `graph_available`
- `imap_available`
- `recommended_provider`
- `last_probe_at`
- `last_probe_source`

#### 4. 执行期 fallback

- `auto` 模式：
  - 优先走 recommended provider
  - 若遇到 scope、401、provider unavailable，再尝试另一 provider
- `graph_preferred`：
  - 优先 Graph
  - 仅在已知可回退错误下尝试 IMAP
- `graph_only` / `imap_only`：
  - 不做自动切换
  - 直接返回明确错误

### 生命周期状态

建议增加统一生命周期状态：

- `new`
- `probed`
- `registered`
- `healthy`
- `degraded`
- `auth_failed`

这样前端和外部脚本都可以看到：

- 账户是否仅完成预检
- 当前是健康还是降级
- 为什么走 Graph / 为什么切回 IMAP

## 数据模型与持久化设计

建议把 `api_method` 从主决策字段降级为兼容字段，新主模型拆成四组数据。

### 1. 接入凭证

保留：

- `email`
- `refresh_token`
- `client_id`
- `access_token`
- `token_expires_at`

### 2. 策略配置

新增：

- `strategy_mode`
- `debug_override_provider`
- `debug_override_skip_cache`
- `debug_override_expires_at`

### 3. 能力快照

新增：

- `graph_available`
- `imap_available`
- `recommended_provider`
- `last_probe_at`
- `last_probe_source`
- `capability_version`

### 4. 运行健康状态

新增：

- `lifecycle_state`
- `last_provider_used`
- `last_success_at`
- `last_error_at`
- `last_error_code`
- `last_error_message`

### 表结构建议

建议：

- `accounts` 表继续保存高频查询字段与索引字段
- 复杂快照使用两个 JSON 字段承载：
  - `capability_snapshot_json`
  - `provider_health_json`

好处：

- SQLite / PostgreSQL 都易于兼容
- 常查字段仍可索引与筛选
- 复杂诊断信息不需要频繁改表结构

### `api_method` 兼容策略

保留 `api_method`，但只用于兼容层：

- `graph_api` ≈ `graph_preferred`
- `imap` ≈ `imap_only` 或 `auto + graph unavailable`

未来内部决策应只依赖：

- `strategy_mode`
- capability snapshot
- provider health

## 迁移与兼容层设计

本次升级采用 **加法迁移 + 适配转发**。

### 第一步：扩表但不改旧语义

新增字段：

- `strategy_mode`
- `lifecycle_state`
- `last_provider_used`
- `capability_snapshot_json`
- `provider_health_json`

默认值先补齐，但不立即删除或停用 `api_method`。

### 第二步：统一服务层落地

建立：

- `TokenBroker`
- `CapabilityResolver`
- `MailGateway`
- `AccountLifecycleService`

但 `v1` 路由暂不改变接口契约，只转发到新服务层。

### 第三步：建立 V1 Adapter

老接口通过 adapter 映射：

- 老 `/accounts` → `AccountLifecycleService`
- 老 `/emails` → `MailGateway`
- 老 `detect-api-method` → `capability-detection`

响应结构继续保持原样，adapter 负责字段映射与兼容。

### 第四步：新增 `v2`

- 文档、OpenAPI、SDK 示例全部以 `v2` 为准
- 新前端、新脚本优先接 `v2`
- 旧前端与老脚本继续跑 `v1`

### 第五步：数据回填

建议回填策略：

- `api_method=graph_api` → `strategy_mode=graph_preferred`
- `api_method=imap` → `strategy_mode=imap_only`
- 已有成功 token 与正常邮件访问记录 → `registered/healthy`
- 连续失败或认证异常 → `degraded/auth_failed`

### 第六步：兼容期观测

兼容期需要统计：

- `v1` / `v2` 请求量
- provider 选路分布
- fallback 频率
- 典型错误码
- 同账户在 `v1` / `v2` 下的行为一致性

建议在 `v1` 响应头中增加：

- `Deprecation`
- `Sunset`

## 测试与验收策略

本次改造不适合一次性切换，建议拆成四个可回滚阶段。

### 阶段 A：数据与服务骨架

内容：

- 扩表
- 建统一服务骨架
- 暂不切业务流量

验收：

- 旧接口行为不变
- 迁移脚本可重复执行
- 基础模型测试通过

### 阶段 B：v2 只读能力

内容：

- 上线 `probe`
- 上线 `health`
- 上线 `capability-detection`
- 上线 `messages list/detail`

验收：

- 同账户在 `v1` / `v2` 下，核心读取结果一致
- provider 选路日志可追踪
- 只读链路 smoke 稳定

### 阶段 C：写操作统一

内容：

- 接入 `register`
- 接入 `import`
- 接入 `refresh`
- 接入 `delete`
- 接入 `send`
- batch import 切到统一生命周期服务

验收：

- 单账户/批量账户都可跑通
- Graph/IMAP fallback 有明确自动化覆盖
- 删除、发送、刷新成功写回健康状态

### 阶段 D：前端与外部 API 迁移

内容：

- 前端默认改走 `v2`
- `v1` 进入兼容层
- README / OpenAPI / 迁移文档统一改口径

验收：

- 真实页面完成 `probe → register → list → detail → delete/send` 全链路
- 新旧接口共存一段时间无回归

### 测试层次

建议至少覆盖五层测试：

1. **单元测试**：scope 决策、provider 选路、状态迁移
2. **契约测试**：`v1 adapter`、`v2 schema`
3. **集成测试**：Graph provider、IMAP provider、缓存层
4. **回归测试**：分享页、验证码规则、批量导入等既有链路
5. **真实 smoke**：至少 1 个 Graph 账户 + 1 个 IMAP 账户

## 推荐实施顺序

建议按“先统一内核，再开新接口，最后切前端与外部调用”的顺序推进。

### 1. 先做数据迁移 + 服务骨架

- 先让微软交互真相只保留一份
- 不立即动页面和旧接口行为

### 2. 再做 `v2` 只读接口

- 优先验证新架构稳定性
- 风险最低，收益最高

### 3. 再接写操作

- `register / import / refresh / delete / send`
- batch import 一起切到统一生命周期

### 4. 最后切前端与外部 API

- 前端默认走 `v2`
- `v1` 通过 adapter 兼容
- 文档和示例全部切到新口径

### 不建议一起改的内容

本轮不建议与以下改造并行：

- verification rule 大改
- auth 权限模型大改
- compose / 部署链路整理
- 分享页产品语义重写

## 最终建议

本次重构的最优路径不是“回到旧项目”，而是：

1. 保留 `OutlookManager2` 现有的 Graph/IMAP 双栈能力。
2. 吸收旧项目“先试、再存；先验证、再导入；给调试留直通车”的交互思想。
3. 用统一服务层收口微软交互策略。
4. 通过 `v2` API 把外部契约从“协议驱动”升级为“能力驱动”。

最终成功标准应是：

- 同一账户在 `auto / graph / imap` 下行为可解释
- `v1` 不炸，`v2` 可正式接入前端和外部调用方
- `probe / capability / health / override` 能真正帮助排障
- 微软交互逻辑只保留一份，后续演进不再重复分叉

## 2026-04-30 落地补充

截至 2026 年 4 月 30 日，这条设计线已经补齐了下面这些最小可用面：

- `v2` 账户写接口：`register / import(dry_run|commit) / token-refresh`
- `v2` 邮件写接口：`delete / batch-delete / send`
- 前端最小接入：账户页 health / delivery-strategy 摘要、批量导入 dry-run、邮件页 `/api/v2` 调试读链路

同时，`v1` 兼容层已经开始显式发出弃用信号：

- `Deprecation: true`
- `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`

这代表设计进入了“**双轨并行，但默认新能力走 v2**”的阶段。

### 当前推荐口径

1. **新接入一律优先 `/api/v2`**
   - 尤其是 `probe / health / delivery-strategy / messages`
   - 新脚本不再围绕 `api_method` 直接分流

2. **旧调用方暂不强制迁移**
   - `/accounts`、`/emails` 仍保持兼容
   - 但它们的行为本质上已经是 adapter 到统一服务层

3. **迁移文档与操作指引要同步收口**
   - README 负责给出主入口
   - runbook 负责解释 `v1` vs `v2` 差异、dry-run 导入、override 排障

如果后续继续推进，下一阶段的重点不应再是“补第三套路径”，而是：

- 让前端默认读链路切到 `v2`
- 把外部调用方和运维脚本逐步从 `v1` 切出
- 到 Sunset 日期前，确保 `v1` 只承担兼容职责，不再承接新语义
