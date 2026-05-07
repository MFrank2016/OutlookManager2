import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const toolbarPath = resolve(process.cwd(), "src/components/emails/EmailToolbar.tsx");
const emailsPagePath = resolve(process.cwd(), "src/app/dashboard/emails/page.tsx");
const emailListPanelPath = resolve(process.cwd(), "src/components/emails/EmailListPanel.tsx");
const emailDetailPanelPath = resolve(process.cwd(), "src/components/emails/EmailDetailPanel.tsx");
const dashboardLayoutPath = resolve(process.cwd(), "src/app/dashboard/layout.tsx");

test("emails toolbar should let expanded controls stretch across the available row instead of clamping to narrow max widths", () => {
  const source = readFileSync(toolbarPath, "utf-8");

  assert.ok(source.includes('className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_auto]"'));
  assert.ok(source.includes('className="w-full"'));
  assert.ok(source.includes('className="grid gap-3 xl:grid-cols-[minmax(0,2.8fr)_180px_auto]"'));
});

test("emails page debug controls should use the shared Select component instead of raw native select elements", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes('import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";'));
  assert.ok(!source.includes("<select"));
  assert.ok(source.includes("<SelectTrigger"));
  assert.ok(source.includes("<SelectContent>"));
});

test("emails page should default to v2 and keep the read-path debug bar collapsed until manually expanded", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes("const [useV2ReadPath, setUseV2ReadPath] = useState(true);"));
  assert.ok(source.includes("const [isReadPathPanelCollapsed, setIsReadPathPanelCollapsed] = useState(true);"));
  assert.ok(source.includes("展开读取路径栏"));
  assert.ok(source.includes("收起读取路径栏"));
  assert.ok(source.includes("{!isReadPathPanelCollapsed ? ("));
});

test("emails page should keep the main toolbar collapsed by default and wire the expand toggle through the page state", () => {
  const toolbarSource = readFileSync(toolbarPath, "utf-8");
  const pageSource = readFileSync(emailsPagePath, "utf-8");

  assert.ok(toolbarSource.includes("isExpanded: boolean;"));
  assert.ok(toolbarSource.includes("onToggleExpanded: () => void;"));
  assert.ok(toolbarSource.includes("当前邮箱"));
  assert.ok(toolbarSource.includes("展开更多筛选"));
  assert.ok(toolbarSource.includes("收起更多筛选"));
  assert.ok(toolbarSource.includes("{!isExpanded ? null : ("));

  assert.ok(pageSource.includes("const [isToolbarExpanded, setIsToolbarExpanded] = useState(false);"));
  assert.ok(pageSource.includes("isExpanded={isToolbarExpanded}"));
  assert.ok(pageSource.includes("onToggleExpanded={() => setIsToolbarExpanded((current) => !current)}"));
});

test("emails page should switch to a two-column workspace on desktop while keeping the dialog flow for narrower widths", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes('window.matchMedia("(min-width: 1536px)")'));
  assert.ok(source.includes('className="grid min-h-0 flex-1 gap-4 2xl:grid-cols-[minmax(340px,0.72fr)_minmax(0,1.28fr)]"'));
  assert.ok(source.includes('className="panel-surface flex min-h-0 min-w-0 flex-col overflow-hidden p-3 md:p-4"'));
  assert.ok(source.includes('className="hidden min-h-0 min-w-0 2xl:block"'));
  assert.ok(source.includes("setEmailDetailOpen(true);"));
  assert.ok(source.includes("setEmailDetailOpen(false);"));
  assert.ok(source.includes('if (isDesktopDetailLayout) {'));
  assert.ok(source.includes('<Dialog open={emailDetailOpen && !isDesktopDetailLayout} onOpenChange={setEmailDetailOpen}>'));
});

test("emails page should request hydrated v2 list details so verification buttons and previews are ready before opening source view", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes("hydrateDetails: true"));
});

test("email list panel should keep the card layout as the stable presentation across viewport changes so maximize does not swap to a table", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('className="grid gap-3"'));
  assert.ok(!source.includes('<Table className="table-fixed">'));
  assert.ok(!source.includes("TableHead className"));
  assert.ok(source.includes("复制验证码"));
});

test("email list panel should highlight verification emails in the shared card layout", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('email.verification_code && "border-amber-300/70 bg-amber-50/70 shadow-[0_12px_24px_rgba(251,191,36,0.10)]"'));
});

test("email list panel should keep the stacked card layout across desktop widths so copy-code actions stay reachable without horizontal scrolling", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('className="grid gap-3"'));
  assert.ok(!source.includes('min-[2200px]:block'));
  assert.ok(!source.includes('min-[2200px]:hidden'));
});

test("email list cards should prioritize verification-code copy actions ahead of the preview block", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('className="w-full justify-center border-amber-300 bg-amber-50/90 text-amber-700 hover:bg-amber-100"'));
  assert.ok(source.includes("复制验证码"));
  assert.ok(source.includes('className="line-clamp-2 text-xs leading-relaxed text-[color:var(--text-soft)]"'));
});

test("dashboard shell and email workspace should opt into min-h-0 flex sizing so list and detail regions can actually scroll", () => {
  const layoutSource = readFileSync(dashboardLayoutPath, "utf-8");
  const pageSource = readFileSync(emailsPagePath, "utf-8");
  const listSource = readFileSync(emailListPanelPath, "utf-8");
  const detailSource = readFileSync(emailDetailPanelPath, "utf-8");

  assert.ok(layoutSource.includes('className="flex min-w-0 min-h-0 flex-1 flex-col"'));
  assert.ok(layoutSource.includes("hideDesktopTopbar ? ("));
  assert.ok(layoutSource.includes('className="flex min-h-0 flex-1 flex-col p-3 md:p-6"'));
  assert.ok(layoutSource.includes('className="panel-surface soft-grid-bg flex h-full min-h-0 flex-1 flex-col overflow-hidden p-3 md:p-4"'));
  assert.ok(layoutSource.includes('<ScrollArea className="min-h-0 flex-1">'));

  assert.ok(pageSource.includes('className="page-enter flex min-h-0 flex-1 flex-col gap-3 md:gap-4"'));
  assert.ok(pageSource.includes('className="grid min-h-0 flex-1 gap-4 2xl:grid-cols-[minmax(340px,0.72fr)_minmax(0,1.28fr)]"'));
  assert.ok(pageSource.includes('className="panel-surface flex min-h-0 min-w-0 flex-col overflow-hidden p-3 md:p-4"'));
  assert.ok(pageSource.includes('DialogContent className="flex h-[min(92dvh,960px)] w-full max-w-[95vw] flex-col overflow-hidden p-0 lg:max-w-6xl"'));
  assert.ok(pageSource.includes('className="hidden min-h-0 min-w-0 2xl:block"'));
  assert.ok(pageSource.includes('<div className="min-h-0 flex-1 overflow-hidden">{detailPanel}</div>'));

  assert.ok(listSource.includes('import { ScrollArea } from "@/components/ui/scroll-area";'));
  assert.ok(listSource.includes('className="flex h-full min-h-0 flex-col gap-4"'));
  assert.ok(listSource.includes('<ScrollArea className="min-h-0 flex-1 pr-1">'));

  assert.ok(detailSource.includes('className="panel-surface flex h-full min-h-0 flex-col overflow-hidden"'));
  assert.ok(detailSource.includes('<ScrollArea className="min-h-0 flex-1 px-4 py-5 md:px-5">'));
});

test("email detail dialog should include an accessible title and description even when the chrome stays visually hidden", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes("DialogDescription"));
  assert.ok(source.includes("DialogTitle"));
  assert.ok(source.includes('<DialogTitle className="sr-only">邮件详情</DialogTitle>'));
  assert.ok(source.includes('<DialogDescription className="sr-only">查看当前所选邮件的验证码、正文与原始来源。</DialogDescription>'));
});

test("email detail panel should wrap long metadata values and keep html content constrained within the available pane width", () => {
  const source = readFileSync(emailDetailPanelPath, "utf-8");

  assert.ok(source.includes('className="grid gap-3 text-sm"'));
  assert.ok(source.includes('className="break-all text-foreground"'));
  assert.ok(source.includes('className="prose prose-slate max-w-none break-words text-sm leading-relaxed [overflow-wrap:anywhere] [&_img]:max-w-full [&_table]:w-full dark:prose-invert"'));
});
