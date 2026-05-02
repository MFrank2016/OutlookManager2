import test from "node:test";
import assert from "node:assert/strict";

import {
  buildV2MessageQueryParams,
  getAccountSendSupport,
  mapProviderLabel,
  mapStrategyLabel,
  parseCapabilitySnapshot,
} from "./microsoftAccess";

test("mapStrategyLabel auto", () => {
  assert.equal(mapStrategyLabel("auto"), "自动选择");
});

test("mapProviderLabel graph_api", () => {
  assert.equal(mapProviderLabel("graph_api"), "Graph API");
});

test("buildV2MessageQueryParams strips empty debug values", () => {
  assert.deepEqual(
    buildV2MessageQueryParams({
      folder: "junk",
      page: 2,
      page_size: 50,
      subject_search: "code",
      override_provider: "auto",
      strategy_mode: "auto",
      skip_cache: false,
    }),
    {
      folder: "junk",
      page: 2,
      page_size: 50,
      subject_search: "code",
    }
  );
});

test("parseCapabilitySnapshot returns null on invalid payload", () => {
  assert.equal(parseCapabilitySnapshot("not-json"), null);
});

test("getAccountSendSupport marks IMAP-only accounts as unsupported for compose", () => {
  const result = getAccountSendSupport({
    api_method: "imap",
    capability_snapshot_json: null,
  });

  assert.equal(result.canSend, false);
  assert.match(result.reason, /仅 Graph 账户支持发信/);
});

test("getAccountSendSupport prefers explicit graph_send_available capability", () => {
  const result = getAccountSendSupport({
    api_method: "imap",
    capability_snapshot_json: JSON.stringify({
      graph_send_available: true,
    }),
  });

  assert.equal(result.canSend, true);
});
