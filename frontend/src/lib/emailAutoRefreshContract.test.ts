import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const toolbarPath = resolve(process.cwd(), "src/components/emails/EmailToolbar.tsx");
const emailsPagePath = resolve(process.cwd(), "src/app/dashboard/emails/page.tsx");

test("emails toolbar should expose an auto refresh toggle with visible status", () => {
  const source = readFileSync(toolbarPath, "utf-8");

  assert.ok(source.includes("onToggleAutoRefresh: () => void;"));
  assert.ok(source.includes("自动刷新"));
  assert.ok(source.includes("已关闭"));
});

test("emails page should keep auto refresh toggle state and wire it into the toolbar", () => {
  const source = readFileSync(emailsPagePath, "utf-8");

  assert.ok(source.includes("const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);"));
  assert.ok(source.includes("onToggleAutoRefresh={() => setIsAutoRefreshEnabled((current) => !current)}"));
});


test("emails toolbar should anchor the auto refresh badge in the far-left toolbar slot with a stronger highlight style", () => {
  const source = readFileSync(toolbarPath, "utf-8");

  assert.ok(source.includes("const autoRefreshControl = ("));
  assert.ok(source.includes("border-emerald-300/80"));
  assert.ok(source.includes("shadow-[0_10px_24px_rgba(16,185,129,0.16)]"));
  assert.ok(source.includes("leading={autoRefreshControl}"));
  assert.ok(source.includes("self-start"));
  assert.ok(source.includes("trailing={"));
});
