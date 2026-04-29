# Admin Console UI / UX Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the OutlookManager2 管理后台为一套主题稳定、结构统一、操作更顺手的现代专业型控制台，同时修复明暗主题切换与页面风格割裂问题。

**Architecture:** 保持现有 FastAPI API 与 Next.js 路由不变，前端围绕“语义化主题 token + 统一 App Shell + 可复用数据工作区组件”重构。先收敛主题与骨架，再迁移高频页面（账户、邮件、管理面板），最后做全站收口与 live 验证。

**Tech Stack:** Next.js App Router, TypeScript, Tailwind CSS v4, shadcn/ui, next-themes, TanStack Query, Zustand, Lucide React, Playwright CLI。

## 约束与验证基线

- 当前实施工作区：`.worktrees/admin-console-ui-ux-optimization`
- 当前基线已验证：
  - `python3 -m pytest -q` → `46 passed, 12 skipped`
  - `cd frontend && npm run lint -- --max-warnings=0` → 通过
  - `cd frontend && npm run build` → 通过
- frontend 目前没有正式的 `test` script；本轮不先引入新测试框架。
- 因此前端任务的强制验证手段统一为：
  - `npm run lint -- --max-warnings=0`
  - `npm run build`
  - Playwright live smoke（登录、主题切换、核心页面操作）
- 只有在提取出纯函数 / 纯映射逻辑时，才补轻量级单测；否则避免为本轮 UI 改造额外扩 scope。

---

### Task 1: 稳定主题系统与全局设计 token

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/providers/ThemeProvider.tsx`
- Modify: `frontend/src/components/layout/ThemeToggle.tsx`
- Modify: `frontend/src/components/ui/sonner.tsx`
- Create: `frontend/src/lib/theme.ts`

**Step 1: 固化主题切换规则**

在 `frontend/src/lib/theme.ts` 新建纯工具：

- `getNextTheme(resolvedTheme: string | undefined): "light" | "dark"`
- `getThemeToggleLabel(resolvedTheme: string | undefined): string`

要求：
- 不读 DOM class
- 所有主题切换文案统一走这个文件

**Step 2: 重构 ThemeToggle**

把 `ThemeToggle.tsx` 改成：

- 使用 `useTheme()` 里的 `resolvedTheme`
- 点击时只调用 `setTheme(getNextTheme(resolvedTheme))`
- tooltip / `title` / `aria-label` 统一输出“切换到浅色主题”或“切换到深色主题”
- 保留图标动画，但加 `motion-reduce` 退化样式

**Step 3: 收敛 ThemeProvider 与根布局**

在 `ThemeProvider.tsx` / `app/layout.tsx` 中确认：

- `attribute="class"`
- `defaultTheme="system"`
- `enableSystem`
- `disableTransitionOnChange`

并在 `body` 上只保留必要的控制台语义 class，移除不利于 token 化的强耦合 class 用法。

**Step 4: 重写 globals 里的主题层**

在 `globals.css` 中：

- 把当前大量 `.dark body.theme-console ...` patch 收敛成 `:root` / `.dark` token 映射
- 定义 `surface-0/1/2/3`、`text-soft`、`text-faint`、`panel`、`danger` 等语义变量
- 让按钮、输入框、表格、卡片依赖语义色，而不是继续直接绑灰阶 class

**Step 5: 对齐 Toaster 主题**

更新 `components/ui/sonner.tsx`，确保 toast 在 light / dark 下：

- 背景、边框、文字、图标一致
- 成功 / 警告 / 错误色调不刺眼

**Step 6: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

Expected:
- lint 退出 0
- build 成功

**Step 7: 做 live 主题 smoke**

Run（示例，按本机已运行的 3000 端口执行）：
```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"
"$PWCLI" open http://127.0.0.1:3000/login
"$PWCLI" snapshot
"$PWCLI" click eX
"$PWCLI" eval '() => ({ html: document.documentElement.className, scheme: getComputedStyle(document.body).colorScheme })'
```

Expected:
- 登录页可在 light / dark 间稳定切换
- `html` class 与 `colorScheme` 同步变化

**Step 8: Commit**

```bash
git add frontend/src/app/globals.css frontend/src/app/layout.tsx frontend/src/providers/ThemeProvider.tsx frontend/src/components/layout/ThemeToggle.tsx frontend/src/components/ui/sonner.tsx frontend/src/lib/theme.ts
git commit -m "feat(frontend): stabilize admin console theme system"
```

---

### Task 2: 建立统一 App Shell 与页面级骨架组件

**Files:**
- Create: `frontend/src/components/layout/PageHeader.tsx`
- Create: `frontend/src/components/layout/PageSection.tsx`
- Create: `frontend/src/components/layout/PageIntro.tsx`
- Modify: `frontend/src/app/dashboard/layout.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/app/dashboard/api-docs/page.tsx`
- Modify: `frontend/src/app/dashboard/share/page.tsx`

**Step 1: 新建页面骨架组件**

新增 3 个轻量组件：

- `PageHeader.tsx`：页面标题、描述、右侧主操作
- `PageIntro.tsx`：小型统计 / 上下文说明区
- `PageSection.tsx`：统一 section 包裹层（标题、正文、额外操作）

要求：
- 所有组件只接受少量明确 props
- 不夹杂业务查询逻辑

**Step 2: 重构 dashboard/layout.tsx**

目标：
- 桌面 / 移动端共用同一套 App Shell 语义
- 统一顶部栏、侧边栏、内容容器、滚动区
- 主内容区留出稳定 padding / panel surface

不要做的事：
- 不在 layout 里塞页面私有按钮
- 不继续堆砌局部 `bg-*` patch

**Step 3: 重构 Sidebar**

更新 `Sidebar.tsx`：

- 品牌区增加更稳重的系统定位
- 收起 / 展开态一致
- 当前激活态更清晰
- 用户区与主题切换、退出按钮层级更合理
- 所有图标只用 Lucide，不新增 emoji

**Step 4: 让次级页面先接入新骨架**

先把结构相对简单的页面接到新骨架上：

- `dashboard/api-docs/page.tsx`
- `dashboard/share/page.tsx`

要求：
- 用 `PageHeader` 替代当前裸 `h1`
- 内容区统一使用 `PageSection` / 标准 panel 包裹

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

Expected:
- layout / sidebar 相关 TS 与样式无报错

**Step 6: live 验证壳层**

重点检查：
- `/dashboard`
- `/dashboard/share`
- `/dashboard/api-docs`

Expected:
- 侧边栏、顶部、内容区、滚动区一致
- 明暗主题下边界清晰
- 移动端菜单可打开 / 关闭

**Step 7: Commit**

```bash
git add frontend/src/components/layout/PageHeader.tsx frontend/src/components/layout/PageSection.tsx frontend/src/components/layout/PageIntro.tsx frontend/src/app/dashboard/layout.tsx frontend/src/components/layout/Sidebar.tsx frontend/src/app/dashboard/api-docs/page.tsx frontend/src/app/dashboard/share/page.tsx
git commit -m "feat(frontend): add unified admin app shell"
```

---

### Task 3: 建立可复用的数据工作区组件

**Files:**
- Create: `frontend/src/components/ui/filter-toolbar.tsx`
- Create: `frontend/src/components/ui/selection-bar.tsx`
- Create: `frontend/src/components/ui/data-empty-state.tsx`
- Create: `frontend/src/components/ui/data-loading-state.tsx`
- Modify: `frontend/src/components/ui/card.tsx`
- Modify: `frontend/src/components/ui/table.tsx`
- Modify: `frontend/src/components/ui/input.tsx`
- Modify: `frontend/src/components/ui/select.tsx`
- Modify: `frontend/src/components/ui/dialog.tsx`
- Modify: `frontend/src/components/ui/button.tsx`

**Step 1: 抽象筛选工具栏**

新增 `filter-toolbar.tsx`，支持：

- 左区：搜索 / 主筛选项
- 中区：补充筛选项
- 右区：查询 / 重置 / 刷新动作
- 响应式自动换行

**Step 2: 抽象批量操作条**

新增 `selection-bar.tsx`，用于统一显示：

- 已选数量
- 主批量操作
- 次批量操作
- 清空选择

**Step 3: 抽象数据状态组件**

新增：

- `data-empty-state.tsx`
- `data-loading-state.tsx`

要求：
- 支持标题、说明、可选 CTA
- 样式适配 light / dark

**Step 4: 收敛基础 shadcn 包装层**

统一 `button`、`card`、`table`、`input`、`select`、`dialog`：

- 圆角、描边、hover、focus、disabled 逻辑一致
- 表格容器支持窄屏横向滚动
- dialog 页头 / 页脚间距更稳

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

Expected:
- 组件库层无回归

**Step 6: Commit**

```bash
git add frontend/src/components/ui/filter-toolbar.tsx frontend/src/components/ui/selection-bar.tsx frontend/src/components/ui/data-empty-state.tsx frontend/src/components/ui/data-loading-state.tsx frontend/src/components/ui/card.tsx frontend/src/components/ui/table.tsx frontend/src/components/ui/input.tsx frontend/src/components/ui/select.tsx frontend/src/components/ui/dialog.tsx frontend/src/components/ui/button.tsx
git commit -m "feat(frontend): add reusable data workspace primitives"
```

---

### Task 4: 重做账户管理页任务流

**Files:**
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/components/accounts/AccountsTable.tsx`
- Modify: `frontend/src/components/accounts/AddAccountDialog.tsx`
- Modify: `frontend/src/components/accounts/TagsDialog.tsx`
- Modify: `frontend/src/store/useAccountsFilterStore.ts`
- Modify: `frontend/src/hooks/useAccounts.ts`
- Reuse: `frontend/src/components/layout/PageHeader.tsx`
- Reuse: `frontend/src/components/ui/filter-toolbar.tsx`
- Reuse: `frontend/src/components/ui/selection-bar.tsx`
- Reuse: `frontend/src/components/ui/data-empty-state.tsx`
- Reuse: `frontend/src/components/ui/data-loading-state.tsx`

**Step 1: 重写页面结构**

把 `dashboard/page.tsx` 改成 4 层：

- 页头（标题、说明、添加、批量添加）
- 筛选工具栏
- 批量操作条
- 结果区 + 分页区

**Step 2: 收敛筛选交互**

统一搜索、标签、状态筛选逻辑：

- 回车查询
- 重置按钮恢复默认条件
- 刷新按钮只刷新当前结果集
- 持久化筛选 store 只保存必要字段

**Step 3: 升级 AccountsTable**

目标：
- 行 hover / selected 更明显
- 复选框、批量选择、空态更清晰
- 高风险操作按钮样式更谨慎
- 表格窄屏下不挤爆布局

**Step 4: 对齐新增 / 标签弹窗**

`AddAccountDialog.tsx` 与 `TagsDialog.tsx` 要接入统一 dialog 风格：

- 标题、副标题、按钮位置统一
- 错误尽量就地提示，不只靠 toast

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

**Step 6: live 验证账户页**

重点验证：
- 登录后进入 `/dashboard`
- 搜索条件输入与查询
- 标签筛选
- 勾选后批量操作条出现
- 空数据场景文案与 CTA
- light / dark 主题一致

**Step 7: Commit**

```bash
git add frontend/src/app/dashboard/page.tsx frontend/src/components/accounts/AccountsTable.tsx frontend/src/components/accounts/AddAccountDialog.tsx frontend/src/components/accounts/TagsDialog.tsx frontend/src/store/useAccountsFilterStore.ts frontend/src/hooks/useAccounts.ts
git commit -m "feat(frontend): redesign accounts workspace"
```

---

### Task 5: 重做邮件页为列表 + 详情工作区

**Files:**
- Modify: `frontend/src/app/dashboard/emails/page.tsx`
- Modify: `frontend/src/hooks/useEmails.ts`
- Modify: `frontend/src/components/emails/SendEmailDialog.tsx`
- Modify: `frontend/src/components/share/ShareTokenDialog.tsx`
- Create: `frontend/src/components/emails/EmailListPanel.tsx`
- Create: `frontend/src/components/emails/EmailDetailPanel.tsx`
- Create: `frontend/src/components/emails/EmailToolbar.tsx`

**Step 1: 拆分邮件页巨型组件**

先把 `emails/page.tsx` 的大块 JSX 拆成 3 个组件：

- `EmailToolbar.tsx`
- `EmailListPanel.tsx`
- `EmailDetailPanel.tsx`

要求：
- 页内状态仍由 page 持有
- 子组件以 props 驱动，不自己偷偷发请求

**Step 2: 调整页面布局**

布局改成：

- 顶部页头 / 工具栏
- 左侧邮件列表
- 右侧详情预览

移动端退化为：
- 上方列表
- 下方详情 / modal 详情

**Step 3: 强化业务上下文**

在详情面板中集中展示：

- 发件人 / 主题 / 时间
- 验证码 / 关键片段
- 分享、复制、删除、发送等操作

不要把这些动作继续散落在多个角落。

**Step 4: 收敛发送 / 分享弹窗风格**

`SendEmailDialog.tsx`、`ShareTokenDialog.tsx` 对齐统一 dialog 规范。

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

**Step 6: live 验证邮件页**

重点验证：
- 选账户后列表加载
- 搜索 / 排序 / 手动刷新
- 选择邮件后详情同步
- 删除 / 清空收件箱确认流程
- 主题切换后列表 / 详情 / dialog 不错色

**Step 7: Commit**

```bash
git add frontend/src/app/dashboard/emails/page.tsx frontend/src/hooks/useEmails.ts frontend/src/components/emails/SendEmailDialog.tsx frontend/src/components/share/ShareTokenDialog.tsx frontend/src/components/emails/EmailListPanel.tsx frontend/src/components/emails/EmailDetailPanel.tsx frontend/src/components/emails/EmailToolbar.tsx
git commit -m "feat(frontend): redesign email workspace"
```

---

### Task 6: 专业化管理面板与其子模块入口

**Files:**
- Modify: `frontend/src/app/dashboard/admin/page.tsx`
- Modify: `frontend/src/components/admin/tables/TablesManager.tsx`
- Modify: `frontend/src/components/admin/tables/SqlQueryPanel.tsx`
- Modify: `frontend/src/components/admin/tables/TableRecordDialog.tsx`
- Modify: `frontend/src/components/admin/UsersTable.tsx`
- Modify: `frontend/src/components/admin/UserDialog.tsx`
- Modify: `frontend/src/components/admin/ConfigTable.tsx`
- Modify: `frontend/src/components/admin/ConfigDialog.tsx`
- Modify: `frontend/src/components/admin/cache/CacheManager.tsx`
- Modify: `frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx`
- Modify: `frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx`
- Create: `frontend/src/components/admin/AdminModuleTabs.tsx`

**Step 1: 替换 emoji tab**

`admin/page.tsx` 改为使用 `AdminModuleTabs.tsx`：

- 图标统一使用 Lucide
- 文字保持中文
- active / hover / focus 样式统一

**Step 2: 对齐子模块页头与工具区**

`TablesManager`、`UsersTable`、`ConfigTable`、`CacheManager`、`VerificationRulesTab`：

- 用统一 section 标题与说明
- 把新增、搜索、刷新等入口组织到顶部工具区

**Step 3: 统一管理员工作区弹窗**

`UserDialog`、`ConfigDialog`、`TableRecordDialog`、`VerificationRuleDialog`：

- 标题、副标题、按钮区统一
- 危险操作标识更明确
- 表单错误就地显示

**Step 4: 优化 SQL / 数据表体验**

`SqlQueryPanel.tsx` 与 `TablesManager.tsx` 重点检查：

- 字体层级
- 代码区 / 结果区边界
- 危险 SQL 提示
- 表名卡片的可读性与点击层级

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

**Step 6: live 验证管理面板**

重点验证：
- tab 切换
- 数据表卡片 / 数据表详情
- 用户、新建 / 编辑 / 删除
- 配置编辑
- 验证码规则编辑器
- light / dark 主题一致性

**Step 7: Commit**

```bash
git add frontend/src/app/dashboard/admin/page.tsx frontend/src/components/admin/tables/TablesManager.tsx frontend/src/components/admin/tables/SqlQueryPanel.tsx frontend/src/components/admin/tables/TableRecordDialog.tsx frontend/src/components/admin/UsersTable.tsx frontend/src/components/admin/UserDialog.tsx frontend/src/components/admin/ConfigTable.tsx frontend/src/components/admin/ConfigDialog.tsx frontend/src/components/admin/cache/CacheManager.tsx frontend/src/components/admin/verification-rules/VerificationRulesTab.tsx frontend/src/components/admin/verification-rules/VerificationRuleDialog.tsx frontend/src/components/admin/AdminModuleTabs.tsx
git commit -m "feat(frontend): professionalize admin control panel"
```

---

### Task 7: 登录页与次级页面收口

**Files:**
- Modify: `frontend/src/app/login/page.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/dashboard/share/page.tsx`
- Modify: `frontend/src/components/share/ShareTokenSearch.tsx`
- Modify: `frontend/src/components/share/ShareTokenTable.tsx`
- Modify: `frontend/src/components/share/BatchShareDialog.tsx`
- Modify: `frontend/src/components/share/BatchCopyDialog.tsx`
- Modify: `frontend/src/components/share/ExtendShareDialog.tsx`

**Step 1: 登录页主题与视觉收口**

登录页确保：
- light / dark 都清晰可读
- 切换按钮风格与后台一致
- 表单、卡片、背景层级统一

**Step 2: 分享页接入新数据工作区模式**

让 `share/page.tsx`、`ShareTokenSearch.tsx`、`ShareTokenTable.tsx` 对齐：
- 页头
- 工具栏
- 批量选择条
- 空态 / loading / error

**Step 3: 分享相关弹窗对齐 dialog 规范**

调整：
- `BatchShareDialog.tsx`
- `BatchCopyDialog.tsx`
- `ExtendShareDialog.tsx`

**Step 4: 根首页收口**

检查 `app/page.tsx` 的跳转 / loading 过渡，避免跟新壳层风格冲突。

**Step 5: 运行验证**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

**Step 6: Commit**

```bash
git add frontend/src/app/login/page.tsx frontend/src/app/page.tsx frontend/src/app/dashboard/share/page.tsx frontend/src/components/share/ShareTokenSearch.tsx frontend/src/components/share/ShareTokenTable.tsx frontend/src/components/share/BatchShareDialog.tsx frontend/src/components/share/BatchCopyDialog.tsx frontend/src/components/share/ExtendShareDialog.tsx
git commit -m "feat(frontend): polish login and secondary admin pages"
```

---

### Task 8: 全量回归、live 验收、文档收尾

**Files:**
- Modify (if needed): `README.md`
- Modify (if needed): `frontend/README.md`
- Create (if needed): `output/playwright/admin-console-ui-ux/` artifacts
- Review: `docs/plans/2026-04-29-admin-console-ui-ux-optimization-design.md`

**Step 1: 跑后端 / Python 基线**

Run:
```bash
python3 -m pytest -q
python3 -W error::DeprecationWarning -c 'import models; import routes.email_routes'
```

Expected:
- pytest 继续通过
- 无 import 级 deprecation regression

**Step 2: 跑前端基线**

Run:
```bash
cd frontend && npm run lint -- --max-warnings=0
cd frontend && npm run build
```

Expected:
- lint / build 都通过

**Step 3: 做 live smoke**

至少覆盖以下路径：

- `/login`
- `/dashboard`
- `/dashboard/emails`
- `/dashboard/admin`
- `/dashboard/share`
- `/dashboard/api-docs`

建议用 Playwright 保存关键截图到：

```bash
output/playwright/admin-console-ui-ux/
```

**Step 4: 写验收摘要**

把最终验证结果整理成简短摘要，记录：
- 主题切换结果
- 核心页面变化
- 仍待后续优化的边角项（若有）

**Step 5: 只在必要时补 README**

如果本轮没有引入新的启动方式或用户可配置项，则不要为了“看起来完整”而无意义改 README。

**Step 6: Final Commit**

```bash
git add frontend README.md frontend/README.md output/playwright/admin-console-ui-ux 2>/dev/null || true
git add frontend docs/plans/2026-04-29-admin-console-ui-ux-optimization-design.md
git commit -m "feat(frontend): deliver admin console ui ux overhaul"
```

---

## 建议执行顺序

1. Task 1 — 主题系统
2. Task 2 — App Shell
3. Task 3 — 复用组件
4. Task 4 — 账户管理
5. Task 5 — 邮件页
6. Task 6 — 管理面板
7. Task 7 — 登录页 / 分享页 / 次级页面
8. Task 8 — 全量验证与收尾

## 风险提醒

- 不要在同一提交里同时改主题底层、页面结构、业务逻辑。
- 不要在没有 live proof 的前提下宣称“主题问题已修好”。
- 不要因为当前 frontend 没有 test runner，就随手引入整套测试基础设施把任务做大。
- 每个任务结束都先验证，再 commit，再进入下一个任务。
