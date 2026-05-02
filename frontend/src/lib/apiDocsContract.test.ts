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

test("api docs page should include quick scopes and request debugging actions for polish", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("全部接口"));
  assert.ok(source.includes("仅 V2"));
  assert.ok(source.includes("仅鉴权"));
  assert.ok(source.includes("仅公共"));
  assert.ok(source.includes("复制 cURL"));
  assert.ok(source.includes("复制响应"));
  assert.ok(source.includes("格式化 JSON"));
});
