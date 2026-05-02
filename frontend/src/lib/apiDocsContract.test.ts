import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const apiDocsPagePath = resolve(process.cwd(), "src/app/dashboard/api-docs/page.tsx");

test("api docs page should expose an in-page API explorer instead of only embedding swagger iframe", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("openapi.json"));
  assert.ok(source.includes("接口列表"));
  assert.ok(source.includes("请求参数"));
  assert.ok(source.includes("发送请求"));
  assert.ok(source.includes("响应结果"));
  assert.ok(!source.includes("<iframe"));
});
