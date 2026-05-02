import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const sharePagePath = resolve(process.cwd(), "src/app/dashboard/share/page.tsx");
const shareTablePath = resolve(process.cwd(), "src/components/share/ShareTokenTable.tsx");

test("share management should use in-app alert dialogs instead of native confirm prompts for destructive actions", () => {
  const pageSource = readFileSync(sharePagePath, "utf-8");
  const tableSource = readFileSync(shareTablePath, "utf-8");

  assert.ok(pageSource.includes("AlertDialog"));
  assert.ok(pageSource.includes("pendingBatchAction"));
  assert.ok(pageSource.includes("pendingDeleteToken"));
  assert.ok(!pageSource.includes("window.confirm"));
  assert.ok(!tableSource.includes("window.confirm"));
});

test("share token table should delegate delete intent to page state instead of deleting immediately", () => {
  const tableSource = readFileSync(shareTablePath, "utf-8");

  assert.ok(tableSource.includes("onRequestDelete: (token: ShareToken) => void;"));
  assert.ok(tableSource.includes("onClick={() => onRequestDelete(token)}"));
});
