# 验证码规则结构升级 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把现有单字段验证码规则升级为“多 matcher + 多 extractor”结构，并补齐测试页手输 `message_id` 与邮件页邮件 ID 展示。

**Architecture:** 后端以 `verification_rules` 主表配合 `verification_rule_matchers`、`verification_rule_extractors` 两张子表承载新语义，运行时先做“任意 matcher 命中”，再按 extractor 顺序提取。管理端 API 保持原 URL 不变，但请求/响应体升级为嵌套结构；前端继续复用现有验证码规则 Tab 和邮件页，不引入新的页面或复杂拖拽，列表顺序直接映射为 `sort_order`。

**Tech Stack:** FastAPI, SQLite/PostgreSQL dual support, DAO layer, React/Next.js, TanStack Query, TypeScript, pytest, ESLint

### Task 1: 建立新规则存储结构并兼容旧数据迁移

**Files:**
- Create: `tests/test_verification_rule_storage.py`
- Modify: `database.py`
- Modify: `database/postgresql_schema.sql`
- Modify: `database/postgresql_indexes.sql`
- Modify: `dao/verification_rule_dao.py`

**Step 1: Write the failing test**

在 `tests/test_verification_rule_storage.py` 里新增最小覆盖：

```python
def test_create_rule_with_matchers_and_extractors_roundtrip():
    rule = db.create_verification_rule(
        {
            "name": "Microsoft 登录验证码",
            "priority": 100,
            "enabled": True,
            "description": "subject first",
            "matchers": [
                {"source_type": "sender", "keyword": "microsoft", "sort_order": 1},
                {"source_type": "subject", "keyword": "security code", "sort_order": 2},
            ],
            "extractors": [
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        }
    )

    listed = db.list_verification_rules()
    assert listed[0]["matchers"][0]["source_type"] == "sender"
    assert listed[0]["extractors"][1]["source_type"] == "body"
```

再补一个迁移测试：旧列写入的规则在迁移后会生成 matcher / extractor。

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_verification_rule_storage.py -q`

Expected: FAIL，提示当前 `verification_rules` 不支持 `matchers` / `extractors` 结构。

**Step 3: Write minimal implementation**

- 在 `database.py` 初始化：
  - 新增 `verification_rule_matchers`
  - 新增 `verification_rule_extractors`
- 在 `dao/verification_rule_dao.py`：
  - 重构 `list_rules/create_rule/update_rule/delete_rule`
  - 让规则 CRUD 自动读写子表
- 在 `database.py` 向后兼容层：
  - `list_verification_rules`
  - `create_verification_rule`
  - `update_verification_rule`
  - `delete_verification_rule`
- 对已有 SQLite 数据做轻量迁移：
  - 从旧 `sender_pattern/subject_pattern/body_pattern/extract_pattern` 生成子项
  - 迁移后新代码只读写 `matchers/extractors`
- 在 PostgreSQL schema/index 文件里补两张子表和索引。

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_verification_rule_storage.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_verification_rule_storage.py database.py database/postgresql_schema.sql database/postgresql_indexes.sql dao/verification_rule_dao.py
git commit -m "feat: store verification rule matchers and extractors"
```

### Task 2: 重构规则引擎语义为“任意 matcher 命中 + 顺序 extractor 提取”

**Files:**
- Modify: `verification_rule_service.py`
- Modify: `tests/test_verification_rule_service.py`
- Modify: `email_service.py`
- Modify: `graph_api_service.py`

**Step 1: Write the failing test**

把 `tests/test_verification_rule_service.py` 改成新结构断言，至少包含：

```python
def test_any_matcher_hit_enters_extractor_pipeline():
    rule = create_verification_rule(
        {
            "name": "GitHub OTP",
            "priority": 10,
            "enabled": True,
            "matchers": [
                {"source_type": "sender", "keyword": "github", "sort_order": 1},
                {"source_type": "body", "keyword": "temporary code", "sort_order": 2},
            ],
            "extractors": [
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        }
    )

    result = detect_verification_code_with_rules(
        email_account="demo@example.com",
        message_id="msg-1",
        from_email="noreply@github.com",
        subject="login notice",
        body_plain="Your temporary code is 112233",
        persist_record=False,
    )

    assert result["code"] == "112233"
    assert result["matched_rule"]["id"] == rule["id"]
    assert result["resolved_code_source"] == "body"
```

再补：
- subject extractor 优先于 body extractor
- matcher 命中但 extractor 全失败时进入 fallback
- 测试结果返回 `matched_matchers` / `extractor_attempts`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_verification_rule_service.py -q`

Expected: FAIL，当前 service 仍依赖旧字段和旧 `rule_evaluations` 结构。

**Step 3: Write minimal implementation**

- `verification_rule_service.py`：
  - 用 `matchers` 判断是否进入提取阶段
  - 按 `extractors.sort_order` 顺序提取
  - 返回结构化调试信息：
    - `matched_matchers`
    - `extractor_attempts`
    - `resolved_code_source`
- `email_service.py` / `graph_api_service.py`：
  - 保持调用入口不变
  - 接住新返回结构并继续回写 `verification_code`
- 仍保留 fallback 到 `verification_code_detector.py`。

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_verification_rule_service.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add verification_rule_service.py tests/test_verification_rule_service.py email_service.py graph_api_service.py
git commit -m "feat: update verification rule engine semantics"
```

### Task 3: 升级管理端 API 为嵌套规则结构和更丰富的测试结果

**Files:**
- Modify: `admin_api.py`
- Modify: `tests/test_verification_rule_admin_api.py`

**Step 1: Write the failing test**

把 `tests/test_verification_rule_admin_api.py` 改为新 payload：

```python
created = await admin_api.create_verification_rule_route(
    admin_api.VerificationRuleUpsertRequest(
        name="Admin 规则",
        priority=20,
        enabled=True,
        matchers=[
            admin_api.VerificationRuleMatcherInput(source_type="sender", keyword="github", sort_order=1),
            admin_api.VerificationRuleMatcherInput(source_type="subject", keyword="verification", sort_order=2),
        ],
        extractors=[
            admin_api.VerificationRuleExtractorInput(source_type="subject", extract_pattern=r"(\d{6})", sort_order=1),
            admin_api.VerificationRuleExtractorInput(source_type="body", extract_pattern=r"(\d{6})", sort_order=2),
        ],
    ),
    admin=_admin(),
)
assert len(created.matchers) == 2
```

再补测试：
- `POST /admin/verification-rules/test` 返回 `matched_matchers` / `extractor_attempts`
- 手动指定 `message_id` 时能正确命中缓存详情

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_verification_rule_admin_api.py -q`

Expected: FAIL，当前 Pydantic schema 仍是 `sender_pattern` 等旧字段。

**Step 3: Write minimal implementation**

- 在 `admin_api.py` 新增/改造：
  - `VerificationRuleMatcherInput`
  - `VerificationRuleExtractorInput`
  - `VerificationRuleItem`
  - `VerificationRuleTestResponse`
- CRUD 路径不变，只升级请求/响应结构。
- `_serialize_rule(...)` 输出嵌套数组。
- 测试接口继续接收：
  - `email_account`
  - `message_id`
  - `rule_id`
  前端手输覆盖逻辑留给 UI 层处理。

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_verification_rule_admin_api.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add admin_api.py tests/test_verification_rule_admin_api.py
git commit -m "feat: add nested verification rule admin api"
```

### Task 4: 重构规则编辑器为 matcher / extractor 列表表单

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/hooks/useAdmin.ts`
- Modify: `frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx`

**Step 1: Define the failing contract in types**

先把前端类型改为目标结构，确保编译阶段能把旧字段引用全部暴露出来：

```ts
export interface VerificationRuleMatcher {
  id?: number;
  source_type: "sender" | "subject" | "body";
  keyword: string;
  sort_order: number;
}

export interface VerificationRuleExtractor {
  id?: number;
  source_type: "subject" | "body";
  extract_pattern: string;
  sort_order: number;
}
```

并把 `VerificationRule` 改为 `matchers[]` / `extractors[]`。

**Step 2: Run lint to verify it fails**

Run: `cd frontend && npm run lint -- --max-warnings=0`

Expected: FAIL，现有 `VerificationRuleDialog.tsx` / `useAdmin.ts` 仍引用旧字段。

**Step 3: Write minimal implementation**

- `frontend/src/hooks/useAdmin.ts`
  - 改 payload/response 类型
- `VerificationRuleDialog.tsx`
  - 基础区保留：名称、优先级、启用、描述
  - 新增“匹配规则列表”编辑区
  - 新增“提取规则列表”编辑区
  - 默认按数组顺序写入 `sort_order`
  - 本轮只做新增/删除，不做拖拽排序
- 保存前前端先做最小校验：
  - 至少 1 条 matcher
  - 至少 1 条 extractor
  - keyword / extract_pattern 非空

**Step 4: Run lint to verify it passes**

Run: `cd frontend && npm run lint -- --max-warnings=0`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/hooks/useAdmin.ts frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx
git commit -m "feat: rebuild verification rule editor"
```

### Task 5: 升级测试面板与邮件页邮件 ID 展示

**Files:**
- Modify: `frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx`
- Modify: `frontend/src/app/dashboard/emails/page.tsx`

**Step 1: Define the failing UI behavior**

先把测试入口和结果目标写成最小检查清单：

```text
- 账号选中后，仍可下拉选邮件
- 新增 message_id 输入框
- 输入框有值时，运行测试优先使用手输 message_id
- 下拉项展示 subject / from_email / message_id / verification_code
- 测试结果展示 matched_matchers / extractor_attempts / resolved_code_source
- 邮件列表桌面端和移动端都能看到 ID
- 邮件详情里的 message_id 可复制
```

**Step 2: Run lint to verify it fails**

Run: `cd frontend && npm run lint -- --max-warnings=0`

Expected: FAIL 或功能未满足，现有 UI 没有手输 `message_id`、也没有新测试结果结构。

**Step 3: Write minimal implementation**

- `VerificationRulesTab.tsx`
  - 新增 `manualMessageId` 状态
  - 调整 `handleRunTest`：优先取手输值，否则用下拉值
  - 下拉项和选中摘要里展示 `message_id`
  - 展示 `matched_matchers` / `extractor_attempts` / `resolved_code_source`
- `emails/page.tsx`
  - 桌面列表：在主题/预览区追加 `ID: <message_id>`
  - 移动卡片：补一行 `ID: <message_id>`
  - 详情弹窗：在现有邮件 ID 旁边补复制按钮

**Step 4: Run lint to verify it passes**

Run: `cd frontend && npm run lint -- --max-warnings=0`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx frontend/src/app/dashboard/emails/page.tsx
git commit -m "feat: add manual message id verification testing"
```

### Task 6: 端到端回归验证并整理最终交付

**Files:**
- Modify: `docs/plans/2026-04-29-verification-code-rule-structure-upgrade-design.md` (only if behavior diverges and needs design note)
- Verify: `tests/test_verification_rule_storage.py`
- Verify: `tests/test_verification_rule_service.py`
- Verify: `tests/test_verification_rule_admin_api.py`
- Verify: `frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx`
- Verify: `frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx`
- Verify: `frontend/src/app/dashboard/emails/page.tsx`

**Step 1: Run focused backend suite**

Run: `python3 -m pytest tests/test_verification_rule_storage.py tests/test_verification_rule_service.py tests/test_verification_rule_admin_api.py -q`

Expected: PASS

**Step 2: Run full backend suite**

Run: `python3 -m pytest -q`

Expected: PASS

**Step 3: Run frontend lint**

Run: `cd frontend && npm run lint -- --max-warnings=0`

Expected: PASS

**Step 4: Manual smoke checklist**

- 管理端规则页可新建多 matcher / 多 extractor 规则
- 测试页可手输 `message_id` 覆盖下拉选择
- 邮件列表、邮件详情可见邮件 ID
- 测试结果能看到命中的 matcher 和 extractor 尝试顺序

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: upgrade verification rule structure"
```
