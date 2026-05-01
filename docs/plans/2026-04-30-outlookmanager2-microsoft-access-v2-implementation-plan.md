# OutlookManager2 Microsoft Access Layer & API v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不打断现有 `v1` 调用方的前提下，为 `OutlookManager2` 落地统一的 Microsoft Access Layer，并新增可用的 `api/v2` 账户/邮件接口与前端接入骨架。

**Architecture:** 先补齐数据库与账户元数据字段，再把 token、capability、provider 选路收口到新的 `microsoft_access/` 服务包；其上新增 `routes/v2`，同时让现有 `v1` 路由逐步转发到统一服务层。实现顺序严格遵循“只读优先、写操作后置、兼容层始终在线”的策略。

**Tech Stack:** FastAPI, Pydantic, SQLite/PostgreSQL DAO, httpx, imaplib, React/Next.js, Axios, React Query, TypeScript, pytest, node:test

## 当前基线与已知 blocker

在 worktree `.worktrees/microsoft-access-v2` 内已经确认：

- `python3 -m pytest -q` → `62 passed, 12 skipped`
- `npm --prefix frontend test` → `6 passed, 0 failed`
- `cd frontend && npx tsc --noEmit` 当前失败：
  - `frontend/src/lib/theme.test.ts(4,51): error TS5097`

因此本计划第一步先修复前端 TS 基线，避免后续每次前端验证都被旧错误污染。

---

### Task 1: 修复前端 TypeScript 基线并锁定验证入口

**Files:**
- Modify: `frontend/src/lib/theme.test.ts`
- Modify: `frontend/package.json`（如需要调整 test/tsc 配置）
- Test: `frontend/src/lib/theme.test.ts`

**Step 1: 写出基线修复前的验证记录**

Run:

```bash
cd frontend && npx tsc --noEmit
```

Expected: 失败并包含 `TS5097`。

**Step 2: 做最小修复**

把 `.ts` 扩展名 import 改成无扩展名，避免要求 `allowImportingTsExtensions`：

```ts
import { getNextTheme, getThemeToggleLabel } from "./theme";
```

不要在这一步顺手引入 `type: module` 或改大范围 tsconfig。

**Step 3: 验证 node:test 仍能跑通**

Run:

```bash
npm --prefix frontend test
```

Expected: `6 pass, 0 fail`。

**Step 4: 验证前端类型检查恢复为绿**

Run:

```bash
cd frontend && npx tsc --noEmit
```

Expected: exit 0。

**Step 5: Commit**

```bash
git add frontend/src/lib/theme.test.ts frontend/package.json
git commit -m "test: fix frontend typescript baseline"
```

---

### Task 2: 扩展账户领域模型与数据库迁移骨架

**Files:**
- Modify: `models.py`
- Modify: `database.py`
- Modify: `dao/account_dao.py`
- Modify: `account_service.py`
- Create: `tests/test_microsoft_access_schema.py`

**Step 1: 先写失败的 schema / migration 测试**

在 `tests/test_microsoft_access_schema.py` 里覆盖：

```python
def test_account_credentials_exposes_strategy_fields():
    credentials = AccountCredentials(
        email="user@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    assert credentials.strategy_mode == "auto"
    assert credentials.lifecycle_state == "new"


def test_init_database_adds_microsoft_access_columns(tmp_path, monkeypatch):
    # 初始化临时 sqlite DB
    # 调用 init_database()
    # 断言 accounts 表含 strategy_mode / lifecycle_state / capability_snapshot_json / provider_health_json
    ...
```

**Step 2: 扩展 Pydantic 模型，但保留 `api_method`**

在 `models.py` 中给 `AccountCredentials` / `AccountInfo` 增加：

- `strategy_mode: str = "auto"`
- `lifecycle_state: str = "new"`
- `last_provider_used: Optional[str] = None`
- `capability_snapshot_json: Optional[str] = None`
- `provider_health_json: Optional[str] = None`

本阶段先保留字符串/JSON 文本，不急着引入更多嵌套模型。

**Step 3: 添加 SQLite / PostgreSQL 迁移列**

在 `database.py` 的 accounts 初始化与增量迁移里新增：

- `strategy_mode TEXT DEFAULT 'auto'`
- `lifecycle_state TEXT DEFAULT 'new'`
- `last_provider_used TEXT`
- `capability_snapshot_json TEXT DEFAULT '{}'`
- `provider_health_json TEXT DEFAULT '{}'`

PostgreSQL 分支同步补列。

**Step 4: 更新 DAO 读写**

在 `dao/account_dao.py` 中：

- `create()` 支持传入 `strategy_mode`
- `update_account()` 支持更新新字段
- 新增安全的 JSON encode/decode 帮助函数
- `get_by_email()` / `get_by_filters()` 返回解析后的 capability / health 数据（至少保证字符串存在且可读）

**Step 5: 更新 `account_service.py` 映射**

`get_account_credentials()` / `save_account_credentials()` 需要传递新增字段，且不破坏旧调用。

**Step 6: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_microsoft_access_schema.py
python3 -m pytest -q tests/test_token_cache.py tests/test_token_refresh.py
```

Expected: 全部通过。

**Step 7: Commit**

```bash
git add models.py database.py dao/account_dao.py account_service.py tests/test_microsoft_access_schema.py
git commit -m "feat: add microsoft access account metadata"
```

---

### Task 3: 建立 `microsoft_access` 服务包与 TokenBroker

**Files:**
- Create: `microsoft_access/__init__.py`
- Create: `microsoft_access/token_broker.py`
- Modify: `oauth_service.py`
- Create: `tests/test_token_broker.py`

**Step 1: 先写 TokenBroker 失败测试**

在 `tests/test_token_broker.py` 里覆盖：

```python
def test_choose_primary_scope_for_auto_defaults_to_imap():
    broker = TokenBroker(...)
    decision = broker.build_scope_plan(strategy_mode="auto", requested_provider=None)
    assert decision.primary_scope == OAUTH_SCOPE


def test_fallback_to_graph_scope_updates_provider_hint(...):
    ...


def test_probe_mode_does_not_persist_access_token(...):
    ...
```

**Step 2: 在新包里实现 TokenBroker**

`microsoft_access/token_broker.py` 至少提供：

- `build_scope_plan(...)`
- `fetch_access_token(..., persist: bool)`
- `get_cached_access_token(...)`
- `refresh_access_token(...)`
- `clear_cached_access_token(...)`

关键约束：

- `probe`/`dry_run` 允许 `persist=False`
- scope fallback 逻辑集中到这里
- 兼容旧 `api_method`

**Step 3: 让 `oauth_service.py` 退化为兼容 facade**

保留旧函数名：

- `get_access_token`
- `refresh_account_token`
- `get_cached_access_token`
- `clear_cached_access_token`

但内部改为调用 `TokenBroker`，避免两套 token 逻辑继续分叉。

**Step 4: 跑针对性测试**

Run:

```bash
python3 -m pytest -q tests/test_token_broker.py tests/test_token_cache.py tests/test_token_refresh.py
```

Expected: 新旧 token 测试都通过。

**Step 5: Commit**

```bash
git add microsoft_access/__init__.py microsoft_access/token_broker.py oauth_service.py tests/test_token_broker.py
git commit -m "feat: add token broker"
```

---

### Task 4: 实现 CapabilityResolver 与账户健康快照

**Files:**
- Create: `microsoft_access/capability_resolver.py`
- Modify: `graph_api_service.py`
- Modify: `dao/account_dao.py`
- Create: `tests/test_capability_resolver.py`

**Step 1: 先写 capability 测试**

```python
def test_detect_capability_prefers_graph_when_mail_scope_available(...):
    ...


def test_detect_capability_falls_back_to_imap_when_graph_unavailable(...):
    ...


def test_capability_snapshot_persisted_to_account_record(...):
    ...
```

**Step 2: 实现 `CapabilityResolver`**

职责：

- 调用 Graph probe
- 记录：
  - `graph_available`
  - `imap_available`
  - `recommended_provider`
  - `last_probe_at`
  - `last_probe_source`
- 输出统一 snapshot dict

**Step 3: 精简旧 Graph 检测入口**

`graph_api_service.check_graph_api_availability()` 可以保留，但应退化成 provider 级原语；
`detect_and_update_api_method()` 后续改调 resolver，而不是直接写 `api_method`。

**Step 4: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_capability_resolver.py tests/test_token_broker.py
```

**Step 5: Commit**

```bash
git add microsoft_access/capability_resolver.py graph_api_service.py dao/account_dao.py tests/test_capability_resolver.py
git commit -m "feat: add capability resolver"
```

---

### Task 5: 建立 Graph / IMAP provider 适配层与 MailGateway 只读链路

**Files:**
- Create: `microsoft_access/providers/__init__.py`
- Create: `microsoft_access/providers/graph_provider.py`
- Create: `microsoft_access/providers/imap_provider.py`
- Create: `microsoft_access/mail_gateway.py`
- Modify: `email_service.py`
- Create: `tests/test_mail_gateway.py`

**Step 1: 先写 MailGateway 失败测试**

```python
def test_mail_gateway_uses_override_provider_first(...):
    ...


def test_mail_gateway_auto_mode_falls_back_from_graph_to_imap(...):
    ...


def test_mail_gateway_list_returns_email_list_response_shape(...):
    ...
```

**Step 2: 抽 provider 只读原语**

Graph provider 暴露：

- `list_messages(...)`
- `get_message_detail(...)`

IMAP provider 暴露：

- `list_messages(...)`
- `get_message_detail(...)`

不要在 provider 层处理路由权限、HTTPException 文案拼装、分享页筛选。

**Step 3: 实现 MailGateway 只读链路**

至少先实现：

- `list_messages(...)`
- `get_message_detail(...)`

输入统一接受：

- `strategy_mode`
- `override_provider`
- `skip_cache`
- 搜索 / 排序 / 时间过滤参数

输出仍然复用 `EmailListResponse` / `EmailDetailsResponse`。

**Step 4: 让 `email_service.py` 先代理只读调用**

把：

- `list_emails()`
- `get_email_details()`

逐步改为调用 `MailGateway`，但先保留函数签名不变。

**Step 5: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_mail_gateway.py tests/test_email_list_optimization.py tests/test_cache_optimization.py
```

**Step 6: Commit**

```bash
git add microsoft_access/providers/__init__.py microsoft_access/providers/graph_provider.py microsoft_access/providers/imap_provider.py microsoft_access/mail_gateway.py email_service.py tests/test_mail_gateway.py
git commit -m "feat: add mail gateway read path"
```

---

### Task 6: 实现 AccountLifecycleService 与 v2 只读/预检接口

**Files:**
- Create: `microsoft_access/account_lifecycle_service.py`
- Create: `routes/v2/__init__.py`
- Create: `routes/v2/account_routes.py`
- Create: `routes/v2/message_routes.py`
- Modify: `routes/__init__.py`
- Modify: `main.py`
- Create: `tests/test_api_v2_accounts.py`
- Create: `tests/test_api_v2_messages.py`

**Step 1: 先写 v2 API 失败测试**

`tests/test_api_v2_accounts.py` 覆盖：

```python
def test_probe_account_returns_capability_without_persisting(...):
    ...


def test_get_account_health_returns_strategy_capability_and_last_error(...):
    ...
```

`tests/test_api_v2_messages.py` 覆盖：

```python
def test_v2_list_messages_supports_provider_override(...):
    ...


def test_v2_get_message_detail_reuses_mail_gateway(...):
    ...
```

**Step 2: 实现 `AccountLifecycleService` 的只读 / 轻写能力**

至少实现：

- `probe_account(...)`
- `detect_capability(...)`
- `get_account_health(...)`
- `resolve_delivery_strategy(...)`

此阶段先不接完整 import / refresh / send。

**Step 3: 新增 `routes/v2`**

建议路径：

- `POST /api/v2/accounts/probe`
- `GET /api/v2/accounts/{email}/health`
- `POST /api/v2/accounts/{email}/capability-detection`
- `GET /api/v2/accounts/{email}/messages`
- `GET /api/v2/accounts/{email}/messages/{message_id}`
- `GET /api/v2/accounts/{email}/delivery-strategy`
- `POST /api/v2/accounts/{email}/delivery-strategy/override`

`routes/__init__.py` 中新增 `v2_router`，`main.py` 保持 Swagger 自动暴露。

**Step 4: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_api_v2_accounts.py tests/test_api_v2_messages.py tests/test_mail_gateway.py
```

**Step 5: Commit**

```bash
git add microsoft_access/account_lifecycle_service.py routes/v2/__init__.py routes/v2/account_routes.py routes/v2/message_routes.py routes/__init__.py main.py tests/test_api_v2_accounts.py tests/test_api_v2_messages.py
git commit -m "feat: add v2 probe and read APIs"
```

---

### Task 7: 让 v1 账户/邮件/分享入口转发到统一服务层

**Files:**
- Modify: `routes/account_routes.py`
- Modify: `routes/email_routes.py`
- Modify: `routes/share_routes.py`
- Modify: `account_service.py`
- Create: `tests/test_v1_adapter_compat.py`

**Step 1: 先写兼容层测试**

```python
def test_v1_accounts_post_uses_lifecycle_register(...):
    ...


def test_v1_emails_get_uses_mail_gateway(...):
    ...


def test_share_route_uses_mail_gateway_detail_path(...):
    ...
```

**Step 2: 账户 v1 adapter**

优先改：

- `POST /accounts`
- `POST /accounts/{email_id}/detect-api-method`
- `POST /accounts/{email_id}/refresh-token`

让它们调 `AccountLifecycleService`，但保持原响应结构。

**Step 3: 邮件 v1 adapter**

优先改：

- `GET /emails/{email_id}`
- `GET /emails/{email_id}/{message_id}`
- `DELETE /emails/{email_id}/{message_id}`
- `DELETE /emails/{email_id}/batch`
- `POST /emails/{email_id}/send`

统一走 `MailGateway` / `AccountLifecycleService`。

**Step 4: 分享页 adapter**

`routes/share_routes.py` 不要继续直接拼 `graph_api_service.list_emails_with_body_graph`，而是逐步切到统一读取入口；
本阶段允许保留分享页的特殊过滤，但 provider 选路必须复用统一层。

**Step 5: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_v1_adapter_compat.py tests/test_admin_panel_apis.py tests/test_new_features.py
```

**Step 6: Commit**

```bash
git add routes/account_routes.py routes/email_routes.py routes/share_routes.py account_service.py tests/test_v1_adapter_compat.py
git commit -m "refactor: route v1 APIs through microsoft access layer"
```

---

### Task 8: 接入 v2 写操作（register / import / refresh / delete / send）

**Files:**
- Modify: `microsoft_access/account_lifecycle_service.py`
- Modify: `microsoft_access/mail_gateway.py`
- Modify: `routes/v2/account_routes.py`
- Modify: `routes/v2/message_routes.py`
- Modify: `routes/account_routes.py`
- Modify: `routes/email_routes.py`
- Modify: `dao/batch_import_task_dao.py`
- Create: `tests/test_api_v2_write_ops.py`

**Step 1: 先写写操作失败测试**

```python
def test_v2_register_persists_strategy_and_health(...):
    ...


def test_v2_import_dry_run_does_not_create_accounts(...):
    ...


def test_v2_import_commit_creates_accounts(...):
    ...


def test_v2_delete_and_send_reuse_mail_gateway(...):
    ...
```

**Step 2: 实现 lifecycle 写操作**

补齐：

- `register_account(...)`
- `import_accounts(mode="dry_run"|"commit")`
- `refresh_token(...)`

**Step 3: 实现 MailGateway 写操作**

补齐：

- `delete_message(...)`
- `batch_delete_messages(...)`
- `send_message(...)`

**Step 4: 批量导入任务切统一服务**

不要再在 `routes/account_routes.py` 内部线程里直接拼 `get_access_token + save_account_credentials`，统一改调 lifecycle service。

**Step 5: 跑测试**

Run:

```bash
python3 -m pytest -q tests/test_api_v2_write_ops.py tests/test_api_v2_accounts.py tests/test_api_v2_messages.py
```

**Step 6: Commit**

```bash
git add microsoft_access/account_lifecycle_service.py microsoft_access/mail_gateway.py routes/v2/account_routes.py routes/v2/message_routes.py routes/account_routes.py routes/email_routes.py dao/batch_import_task_dao.py tests/test_api_v2_write_ops.py
git commit -m "feat: add v2 write operations"
```

---

### Task 9: 前端接入 v2 能力与调试信息

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/hooks/useAccounts.ts`
- Modify: `frontend/src/hooks/useEmails.ts`
- Create: `frontend/src/hooks/useAccountHealth.ts`
- Create: `frontend/src/hooks/useDeliveryStrategy.ts`
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/app/dashboard/accounts/batch/page.tsx`
- Modify: `frontend/src/app/dashboard/emails/page.tsx`
- Modify: `frontend/src/app/dashboard/api-docs/page.tsx`
- Create: `frontend/src/lib/microsoftAccess.test.ts`

**Step 1: 先写纯函数/映射测试**

由于当前前端没有组件测试基础设施，这一步只补纯函数测试：

```ts
import test from "node:test";
import assert from "node:assert/strict";

test("mapStrategyLabel auto", () => {
  assert.equal(mapStrategyLabel("auto"), "自动选择");
});
```

**Step 2: 扩展前端类型**

在 `frontend/src/types/index.ts` 增加：

- `AccountHealth`
- `CapabilitySnapshot`
- `DeliveryStrategy`
- `AccountProbeResult`
- `V2MessageQuery`

**Step 3: hooks 接 v2**

- `useAccounts.ts` 先保留 v1 列表
- 新增 `useAccountHealth()`
- 新增 `useDeliveryStrategy()`
- `useEmails.ts` 允许通过开关改走 `/api/v2/accounts/{email}/messages`

**Step 4: 页面最小接入**

- 账户页显示 health / strategy 摘要
- 批量导入页支持 dry-run probe
- 邮件页支持 provider override / skip cache 调试参数
- API docs 页增加 `/api/v2` 使用说明链接或说明块（iframe 仍可保留）

**Step 5: 跑前端验证**

Run:

```bash
npm --prefix frontend test
cd frontend && npx tsc --noEmit
```

**Step 6: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/hooks/useAccounts.ts frontend/src/hooks/useEmails.ts frontend/src/hooks/useAccountHealth.ts frontend/src/hooks/useDeliveryStrategy.ts frontend/src/app/dashboard/page.tsx frontend/src/app/dashboard/accounts/batch/page.tsx frontend/src/app/dashboard/emails/page.tsx frontend/src/app/dashboard/api-docs/page.tsx frontend/src/lib/microsoftAccess.test.ts
git commit -m "feat: expose microsoft access v2 in frontend"
```

---

### Task 10: 文档、弃用提示与最终全量验证

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-04-30-outlookmanager2-microsoft-access-v2-design.md`
- Create: `docs/runbooks/2026-04-30-microsoft-access-v2-migration.md`
- Modify: `routes/account_routes.py`
- Modify: `routes/email_routes.py`

**Step 1: 更新 README 与 runbook**

README 至少补：

- `api/v2` 入口
- `probe` / `health` / `delivery-strategy` 示例
- 兼容期说明

runbook 至少补：

- `v1` 与 `v2` 差异
- 如何做 dry run 导入
- 如何用 override 排障

**Step 2: 给 v1 增加弃用提示头**

在 `routes/account_routes.py` / `routes/email_routes.py` 的兼容入口响应中加：

- `Deprecation: true`
- `Sunset: <date>`

只在 adapter 层做，不要改 `v2`。

**Step 3: 全量验证**

Run:

```bash
python3 -m pytest -q
npm --prefix frontend test
cd frontend && npx tsc --noEmit
```

如本地服务可起，再追加：

```bash
python3 main.py
# 或项目当前推荐的启动方式
```

并手动验证：

- `/docs`
- `/api/v2/accounts/probe`
- `/api/v2/accounts/{email}/health`
- 仪表盘账户页/邮件页

**Step 4: Commit**

```bash
git add README.md docs/plans/2026-04-30-outlookmanager2-microsoft-access-v2-design.md docs/runbooks/2026-04-30-microsoft-access-v2-migration.md routes/account_routes.py routes/email_routes.py
git commit -m "docs: document microsoft access v2 migration"
```

---

## 实施提醒

- 每完成一个 Task 就重新跑该 Task 的验证命令，不要攒到最后一起跑。
- `api_method` 在整个实现期都保留，直到 `v1` adapter 完全稳定。
- 任何时候都不要让分享页、批量导入、邮件页分别维护自己的 provider 决策。
- 如果中途发现 scope / provider 命名需要调整，优先修改 `microsoft_access` 新层，不要再回头扩散旧模块。
