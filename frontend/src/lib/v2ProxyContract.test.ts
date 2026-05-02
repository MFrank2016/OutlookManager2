import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const nextConfigPath = resolve(process.cwd(), "next.config.ts");

test("next config should preserve /api/v2 when proxying to backend", () => {
  const source = readFileSync(nextConfigPath, "utf-8");

  assert.ok(source.includes('source: "/api/v2/:path*"'));
  assert.ok(source.includes('destination: `${backendUrl}/api/v2/:path*`'));
});

test("next config should keep the exact /api health route mapped to backend /api", () => {
  const source = readFileSync(nextConfigPath, "utf-8");

  assert.ok(source.includes('source: "/api"'));
  assert.ok(source.includes('destination: `${backendUrl}/api`'));
});
