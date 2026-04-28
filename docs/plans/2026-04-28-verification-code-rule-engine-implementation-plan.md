# Verification Code Rule Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a configurable verification-code rule engine with persistence, admin CRUD/test APIs, and shared auto-copy reminders for dashboard and shared email pages.

**Architecture:** Add two database tables plus DAO/service layers for rules and successful detections, route runtime email parsing through the new service with fallback to the legacy detector, then surface CRUD/testing in the admin UI and share a frontend hook for first-seen code auto-copy.

**Tech Stack:** FastAPI, SQLite/PostgreSQL dual support, React/Next.js, TanStack Query, Shadcn UI, pytest

### Task 1: 规则与记录表基础设施

**Files:**
- Create: `dao/verification_rule_dao.py`
- Create: `dao/verification_detection_record_dao.py`
- Modify: `database.py`
- Modify: `database/postgresql_schema.sql`
- Modify: `database/postgresql_indexes.sql`
- Test: `tests/test_verification_rule_service.py`

**Step 1: Write the failing test**

- 增加数据库初始化后可看到 `verification_rules`、`verification_detection_records`
- 增加规则 CRUD 和成功记录写入测试

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_verification_rule_service.py -q`

**Step 3: Write minimal implementation**

- 新增 SQLite / PostgreSQL 表结构
- 增加 DAO 与 `database.py` 包装函数

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_verification_rule_service.py -q`

**Step 5: Commit**

```bash
git add tests/test_verification_rule_service.py dao/verification_rule_dao.py dao/verification_detection_record_dao.py database.py database/postgresql_schema.sql database/postgresql_indexes.sql
git commit -m "feat: add verification rule storage"
```

### Task 2: 后端规则引擎与运行时落库

**Files:**
- Create: `verification_rule_service.py`
- Modify: `verification_code_detector.py`
- Modify: `email_service.py`
- Modify: `graph_api_service.py`
- Test: `tests/test_verification_rule_service.py`

**Step 1: Write the failing test**

- 定向规则优先于通用规则
- `AND / OR` 命中逻辑正确
- 无规则命中时 fallback 到旧 detector
- 成功识别后写入 `verification_detection_records`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_verification_rule_service.py -q`

**Step 3: Write minimal implementation**

- 新增统一规则引擎 service
- 运行时邮件识别改走新 service
- 成功识别写检测记录，并把最终 `verification_code` 回写邮件缓存对象

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_verification_rule_service.py -q`

**Step 5: Commit**

```bash
git add verification_rule_service.py verification_code_detector.py email_service.py graph_api_service.py tests/test_verification_rule_service.py
git commit -m "feat: add verification rule runtime detection"
```

### Task 3: 管理端 API 与实时测试接口

**Files:**
- Modify: `admin_api.py`
- Modify: `models.py`
- Test: `tests/test_verification_rule_admin_api.py`

**Step 1: Write the failing test**

- 规则列表 / 创建 / 更新 / 删除
- 指定账号 + 指定邮件测试接口
- 单条规则测试 / 全量规则测试

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_verification_rule_admin_api.py -q`

**Step 3: Write minimal implementation**

- 在 `admin_api.py` 增加 CRUD 与测试接口
- 返回结构化命中过程

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_verification_rule_admin_api.py -q`

**Step 5: Commit**

```bash
git add admin_api.py models.py tests/test_verification_rule_admin_api.py
git commit -m "feat: add verification rule admin api"
```

### Task 4: 管理面板规则页

**Files:**
- Create: `frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx`
- Create: `frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx`
- Modify: `frontend/src/app/dashboard/admin/page.tsx`
- Modify: `frontend/src/hooks/useAdmin.ts`
- Modify: `frontend/src/types/index.ts`

**Step 1: Write the failing test**

- 这一步以 lint / 手动交互为准，无现成前端测试框架

**Step 2: Run test to verify it fails**

Run: `npm run lint`

**Step 3: Write minimal implementation**

- 新增验证码规则 Tab
- 实现 CRUD 表格
- 实现账号 / 邮件选择和实时测试面板

**Step 4: Run test to verify it passes**

Run: `npm run lint`

**Step 5: Commit**

```bash
git add frontend/src/components/admin/verification-rules frontend/src/app/dashboard/admin/page.tsx frontend/src/hooks/useAdmin.ts frontend/src/types/index.ts
git commit -m "feat: add verification rule admin ui"
```

### Task 5: 主站页 / 分享页自动复制提醒

**Files:**
- Create: `frontend/src/hooks/useVerificationCodeAutoCopy.ts`
- Modify: `frontend/src/app/dashboard/emails/page.tsx`
- Modify: `frontend/src/app/shared/[token]/page.tsx`
- Modify: `frontend/src/lib/clipboard.ts`

**Step 1: Write the failing test**

- 这一步以 lint / 手动交互为准，无现成前端测试框架

**Step 2: Run test to verify it fails**

Run: `npm run lint`

**Step 3: Write minimal implementation**

- 抽共享 hook
- 首次发现新验证码时自动复制并 toast
- 主站页 / 分享页统一行为

**Step 4: Run test to verify it passes**

Run: `npm run lint`

**Step 5: Commit**

```bash
git add frontend/src/hooks/useVerificationCodeAutoCopy.ts frontend/src/app/dashboard/emails/page.tsx frontend/src/app/shared/[token]/page.tsx frontend/src/lib/clipboard.ts
git commit -m "feat: auto copy new verification codes"
```
