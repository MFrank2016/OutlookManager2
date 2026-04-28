import test from "node:test";
import assert from "node:assert/strict";

import { filterVerificationTestEmails } from "./emailFilter.ts";

const emails = [
  {
    message_id: "m1",
    subject: "Verification 123456",
    from_email: "noreply@microsoft.com",
  },
  {
    message_id: "m2",
    subject: "Weekly report",
    from_email: "ops@example.com",
  },
  {
    message_id: "m3",
    subject: "GitHub OTP",
    from_email: "noreply@github.com",
  },
];

test("filters verification test emails by subject, sender and message id", () => {
  assert.equal(filterVerificationTestEmails(emails, "verification").length, 1);
  assert.equal(filterVerificationTestEmails(emails, "github")[0]?.message_id, "m3");
  assert.equal(filterVerificationTestEmails(emails, "m2")[0]?.subject, "Weekly report");
});

test("returns all emails when search query is empty", () => {
  assert.equal(filterVerificationTestEmails(emails, "").length, 3);
});
