import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const toolbarPath = resolve(process.cwd(), "src/components/emails/EmailToolbar.tsx");
const emailsPagePath = resolve(process.cwd(), "src/app/dashboard/emails/page.tsx");

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
