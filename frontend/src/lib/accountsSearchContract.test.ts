import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const dashboardPagePath = resolve(process.cwd(), "src/app/dashboard/page.tsx");

test("accounts dashboard search should refetch when the applied filters are unchanged", () => {
  const source = readFileSync(dashboardPagePath, "utf-8");

  assert.ok(source.includes("const isSameQuery ="));
  assert.ok(source.includes("if (isSameQuery) {"));
  assert.ok(source.includes("void refetch();"));
});

test("accounts dashboard should no longer render the Microsoft Access summary section", () => {
  const source = readFileSync(dashboardPagePath, "utf-8");

  assert.ok(!source.includes("Microsoft Access 摘要"));
  assert.ok(!source.includes("聚焦"));
});
