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

test("api docs page should include favorites, request history and collapsible json response tools", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("收藏接口"));
  assert.ok(source.includes("已收藏"));
  assert.ok(source.includes("请求历史"));
  assert.ok(source.includes("恢复请求"));
  assert.ok(source.includes("JSON 结构视图"));
});

test("api docs page should expose global vars, visual body editor, message helper and scroll-safe layout", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("全局变量"));
  assert.ok(source.includes("全局 Token"));
  assert.ok(source.includes("键值对模式"));
  assert.ok(source.includes("message_id 查看页"));
  assert.ok(source.includes("查询邮件列表"));
  assert.ok(source.includes("简化调试"));
  assert.ok(source.includes("一键填充"));
  assert.ok(source.includes("响应搜索"));
  assert.ok(source.includes("overflow-y-auto"));
  assert.ok(source.includes("min-h-0"));
});

test("api docs page should place global variables in a top collapsed section", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("全局变量设置"));
  assert.ok(source.includes("展开全局变量"));
  assert.ok(source.includes("收起全局变量"));
  assert.ok(source.includes("const [isGlobalVariablesExpanded, setIsGlobalVariablesExpanded] = useState(false)"));
});

test("api docs page should render request body as key-value rows with type, value, default and description", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("值类型"));
  assert.ok(source.includes("默认值"));
  assert.ok(source.includes("说明"));
  assert.ok(source.includes("当前值"));
  assert.ok(source.includes("键值对填充模式"));
  assert.ok(source.includes("字段概览"));
  assert.ok(source.includes("回填全部默认值"));
  assert.ok(source.includes("生成的 JSON 草稿"));
});

test("api docs page should adapt the request body editor into a stacked mobile-friendly layout", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("sm:flex-row sm:items-center sm:justify-between"));
  assert.ok(source.includes("grid w-full grid-cols-2"));
  assert.ok(source.includes("hidden border-b border-border/70 px-3 py-2 md:grid"));
  assert.ok(source.includes("space-y-3 rounded-xl border border-border/60 bg-background/70 p-3 md:grid"));
});

test("api docs page should expose thumb-friendly mobile action groups across request, helper and response areas", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("grid w-full gap-2 rounded-2xl border border-border/70 bg-[color:var(--surface-2)]/55 p-1.5 shadow-sm sm:flex sm:w-auto sm:flex-wrap"));
  assert.ok(source.includes("grid gap-2 sm:grid-cols-2 xl:flex xl:flex-wrap"));
  assert.ok(source.includes("w-full justify-center sm:w-auto"));
  assert.ok(source.includes("grid grid-cols-2 gap-2 sm:flex sm:flex-wrap"));
  assert.ok(source.includes("sm:grid-cols-[minmax(0,1fr)_repeat(2,minmax(0,120px))]"));
});

test("api docs page should reserve more breathing room for desktop body editing and history review", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("const REQUEST_WORKSPACE_DESKTOP_GRID ="));
  assert.ok(source.includes("const RESPONSE_WORKSPACE_DESKTOP_GRID ="));
  assert.ok(source.includes("rounded-2xl border border-border/70 bg-[color:var(--surface-2)]/55 p-1.5 shadow-sm"));
  assert.ok(source.includes("xl:min-w-[112px]"));
  assert.ok(source.includes("xl:w-auto xl:min-w-[112px]"));
  assert.ok(source.includes("xl:self-start xl:sticky xl:top-4"));
});

test("api docs page should use consistent section helper copy for debugging, curl, response and history blocks", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("快捷聚焦常用接口，减少来回检索。"));
  assert.ok(source.includes("跟随当前参数、鉴权与请求体实时生成。"));
  assert.ok(source.includes("按邮箱查找邮件后，可直接把 message_id 带回当前请求。"));
  assert.ok(source.includes("支持状态码、响应头、结构视图与原始响应联合查看。"));
  assert.ok(source.includes("保留最近一次的调试上下文，便于快速恢复和对比。"));
});

test("api docs page should extend the same helper-copy rhythm to params, auth and body cards", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("自动识别 path、query 与 header 参数，并按接口定义渲染。"));
  assert.ok(source.includes("保留当前请求级别的鉴权开关与额外请求头配置。"));
  assert.ok(source.includes("支持键值对填充与 JSON 双模式切换。"));
});

test("api docs page should keep the parameter panel fully localized in Chinese", () => {
  const source = readFileSync(apiDocsPagePath, "utf-8");

  assert.ok(source.includes("路径参数"));
  assert.ok(source.includes("查询参数"));
  assert.ok(source.includes("请求头参数"));
  assert.ok(source.includes("当前接口未声明 path / query / header 参数。"));
});
