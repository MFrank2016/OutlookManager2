import test from "node:test";
import assert from "node:assert/strict";

import {
  buildV2MessageQueryParams,
  mapProviderLabel,
  mapStrategyLabel,
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
