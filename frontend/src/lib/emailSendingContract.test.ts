import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const sendDialogPath = resolve(process.cwd(), "src/components/emails/SendEmailDialog.tsx");
const toolbarPath = resolve(process.cwd(), "src/components/emails/EmailToolbar.tsx");
const emailsHookPath = resolve(process.cwd(), "src/hooks/useEmails.ts");

test("send email dialog should consume full account capability info instead of only email string", () => {
  const source = readFileSync(sendDialogPath, "utf-8");

  assert.ok(source.includes('import { getAccountSendSupport } from "@/lib/microsoftAccess";'));
  assert.ok(source.includes("account: Account | null"));
  assert.ok(source.includes("const sendCapability = getAccountSendSupport(account);"));
});

test("send email dialog should disable compose for unsupported accounts and expose a clear Graph-only hint", () => {
  const source = readFileSync(sendDialogPath, "utf-8");

  assert.ok(source.includes("disabled={!account?.email_id || !sendCapability.canSend}"));
  assert.ok(source.includes("sendCapability.reason"));
  assert.ok(source.includes("title={sendCapability.reason}"));
});

test("email toolbar should pass the selected account record into the compose dialog", () => {
  const source = readFileSync(toolbarPath, "utf-8");

  assert.ok(source.includes("selectedAccountInfo: Account | null;"));
  assert.ok(source.includes("<SendEmailDialog account={selectedAccountInfo} />"));
});

test("send email mutation should treat success=false payloads as failures", () => {
  const source = readFileSync(emailsHookPath, "utf-8");

  assert.ok(source.includes("if (response.data?.success === false)"));
  assert.ok(source.includes('throw new Error(response.data.message || "发送邮件失败");'));
});
