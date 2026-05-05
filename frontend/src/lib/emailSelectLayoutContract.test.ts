import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const toolbarPath = resolve(process.cwd(), "src/components/emails/EmailToolbar.tsx");
const emailsPagePath = resolve(process.cwd(), "src/app/dashboard/emails/page.tsx");
const emailListPanelPath = resolve(process.cwd(), "src/components/emails/EmailListPanel.tsx");

test("emails toolbar should constrain wide select triggers so dropdown menus do not expand across the whole panel", () => {
  const source = readFileSync(toolbarPath, "utf-8");

  assert.ok(source.includes("max-w-[560px]"));
  assert.ok(source.includes("max-w-[260px]"));
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

test("emails page should request hydrated v2 list details so verification buttons and previews are ready before opening source view", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes("hydrateDetails: true"));
});

test("email list panel should use a fixed table layout with constrained subject and preview widths so action buttons stay visible", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('<Table className="table-fixed">'));
  assert.ok(source.includes('TableHead className="w-[220px]"'));
  assert.ok(source.includes('TableHead className="w-[188px] text-right"'));
  assert.ok(source.includes('className="min-w-0 max-w-[560px] space-y-1"'));
  assert.ok(source.includes('className="truncate text-xs leading-5 text-[color:var(--text-soft)]"'));
  assert.ok(source.includes("复制验证码"));
});

test("email list panel should highlight verification emails on both desktop rows and mobile cards", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('email.verification_code && "bg-amber-50/60 hover:bg-amber-100/80 data-[state=selected]:bg-amber-100/95"'));
  assert.ok(source.includes('email.verification_code && "border-amber-300/70 bg-amber-50/70 shadow-[0_12px_24px_rgba(251,191,36,0.10)]"'));
});

test("email list panel should fall back to the stacked card layout below 2xl so copy-code actions stay reachable without horizontal scrolling", () => {
  const source = readFileSync(emailListPanelPath, "utf-8");

  assert.ok(source.includes('className="hidden min-w-0 2xl:block"'));
  assert.ok(source.includes('className="grid gap-3 2xl:hidden"'));
});
