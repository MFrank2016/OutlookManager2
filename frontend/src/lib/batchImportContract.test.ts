import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const batchPagePath = resolve(process.cwd(), "src/app/dashboard/accounts/batch/page.tsx");

test("batch import page should invalidate accounts query after task completion", () => {
  const source = readFileSync(batchPagePath, "utf-8");

  assert.ok(source.includes('import { useQuery, useQueryClient } from "@tanstack/react-query"'));
  assert.ok(source.includes('queryClient.invalidateQueries({ queryKey: ["accounts"] })'));
  assert.ok(source.includes('if (status === "completed")'));
});
