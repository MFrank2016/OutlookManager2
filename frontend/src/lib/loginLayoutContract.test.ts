import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const rootLayoutPath = resolve(process.cwd(), "src/app/layout.tsx");
const dashboardLayoutPath = resolve(process.cwd(), "src/app/dashboard/layout.tsx");
const loginPagePath = resolve(process.cwd(), "src/app/login/page.tsx");

test("theme-console should not be mounted on the global body shell", () => {
  const source = readFileSync(rootLayoutPath, "utf-8");

  assert.ok(!source.includes('<body className="theme-console">'));
});

test("theme-console should be scoped to dashboard layout", () => {
  const source = readFileSync(dashboardLayoutPath, "utf-8");

  assert.ok(source.includes("theme-console"));
});

test("login page keeps the explicit minimalist light palette", () => {
  const source = readFileSync(loginPagePath, "utf-8");

  assert.ok(source.includes("bg-[linear-gradient(180deg,#f7f9fc_0%,#eef3f9_100%)]"));
  assert.ok(source.includes("bg-white/92"));
  assert.ok(source.includes("text-slate-900"));
});

test("login page should use a professional mail glyph instead of a security lock icon", () => {
  const source = readFileSync(loginPagePath, "utf-8");

  assert.ok(source.includes('import { ArrowRight, Mail } from "lucide-react"'));
  assert.ok(!source.includes("LockKeyhole"));
  assert.ok(source.includes('className="relative flex h-[76px] w-[76px] items-center justify-center'));
  assert.ok(
    source.includes(
      "bg-[linear-gradient(180deg,rgba(219,234,254,0.98),rgba(186,230,253,0.95))]",
    ),
  );
  assert.ok(source.includes('className="relative z-10 flex h-[42px] w-[48px] overflow-hidden rounded-[14px]'));
  assert.ok(source.includes('className="flex w-[18px] items-center justify-center bg-[linear-gradient(180deg,#0ea5e9,#2563eb)]'));
  assert.ok(source.includes("text-[11px] font-semibold tracking-[-0.04em] text-white"));
  assert.ok(source.includes('<Mail className="h-[16px] w-[16px] text-sky-700"'));
});

test("login form panel should be width-constrained and centered inside the hero card", () => {
  const source = readFileSync(loginPagePath, "utf-8");

  assert.ok(source.includes("flex flex-1 items-center justify-center"));
  assert.ok(source.includes("max-w-[840px]"));
  assert.ok(source.includes("mx-auto w-full max-w-[500px]"));
});

test("login inputs and primary button should share a narrower centered column", () => {
  const source = readFileSync(loginPagePath, "utf-8");

  assert.ok(source.includes("mx-auto flex w-full max-w-[420px] flex-col items-center"));
  assert.ok(source.includes("mx-auto w-full max-w-[420px]"));
  assert.ok(source.includes("block w-full text-left text-[13px]"));
  assert.ok(source.includes("bg-white px-4 text-[15px]"));
  assert.ok(source.includes("focus-visible:ring-2 focus-visible:ring-sky-500/20"));
  assert.ok(source.includes("mx-auto mt-1 flex h-12 w-full max-w-[420px]"));
  assert.ok(source.includes("rounded-[15px] bg-[linear-gradient(135deg,#2383e2,#2563eb)]"));
});
