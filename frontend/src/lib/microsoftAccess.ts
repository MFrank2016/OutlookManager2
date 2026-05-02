import type {
  Account,
  CapabilitySnapshot,
  DeliveryStrategy,
  ProviderOverride,
  StrategyMode,
  V2MessageQuery,
} from "@/types";

export function buildV2AccountPath(email: string, suffix = ""): string {
  return `/api/v2/accounts/${encodeURIComponent(email)}${suffix}`;
}

export function buildV2MessagesPath(email: string): string {
  return buildV2AccountPath(email, "/messages");
}

export function buildV2MessagePath(email: string, messageId: string): string {
  return buildV2AccountPath(email, `/messages/${encodeURIComponent(messageId)}`);
}

export function buildV2MessageSendPath(email: string): string {
  return buildV2AccountPath(email, "/messages/send");
}

export function mapStrategyLabel(mode?: StrategyMode | null): string {
  switch (mode) {
    case "graph_preferred":
      return "Graph 优先";
    case "graph_only":
      return "仅 Graph";
    case "imap_only":
      return "仅 IMAP";
    case "auto":
    default:
      return "自动选择";
  }
}

export function mapProviderLabel(provider?: string | null): string {
  if (!provider || provider === "auto") {
    return "自动";
  }
  if (provider === "graph" || provider === "graph_api") {
    return "Graph API";
  }
  if (provider === "imap") {
    return "IMAP";
  }
  return provider;
}

export function buildV2MessageQueryParams(query: V2MessageQuery): Record<string, unknown> {
  const params: Record<string, unknown> = {};

  const entries: Array<[keyof V2MessageQuery, string]> = [
    ["folder", "folder"],
    ["page", "page"],
    ["page_size", "page_size"],
    ["sender_search", "sender_search"],
    ["subject_search", "subject_search"],
    ["sort_by", "sort_by"],
    ["sort_order", "sort_order"],
    ["start_time", "start_time"],
    ["end_time", "end_time"],
  ];

  for (const [sourceKey, targetKey] of entries) {
    const value = query[sourceKey];
    if (value !== undefined && value !== null && value !== "") {
      params[targetKey] = value;
    }
  }

  if (query.override_provider && query.override_provider !== "auto") {
    params.override_provider = query.override_provider;
  }
  if (query.strategy_mode && query.strategy_mode !== "auto") {
    params.strategy_mode = query.strategy_mode;
  }
  if (query.skip_cache) {
    params.skip_cache = true;
  }

  return params;
}

export function getCapabilityHighlights(snapshot?: CapabilitySnapshot | null): string[] {
  if (!snapshot) {
    return [];
  }

  const result: string[] = [];
  if (snapshot.graph_read_available) {
    result.push("Graph 可读");
  }
  if (snapshot.graph_send_available) {
    result.push("Graph 可发信");
  }
  if (snapshot.graph_write_available) {
    result.push("Graph 可写");
  }
  if (snapshot.imap_available) {
    result.push("IMAP 可用");
  }
  if (snapshot.graph_probe_status === "probe_error") {
    result.push("探测异常");
  }
  if (snapshot.graph_probe_status === "insufficient_evidence") {
    result.push("证据不足");
  }
  return result;
}

export function parseCapabilitySnapshot(
  raw?: string | null
): CapabilitySnapshot | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    return parsed as CapabilitySnapshot;
  } catch {
    return null;
  }
}

export function getAccountSendSupport(
  account?: Pick<Account, "api_method" | "capability_snapshot_json"> | null
): {
  canSend: boolean;
  reason: string;
  badge: string;
} {
  const snapshot = parseCapabilitySnapshot(account?.capability_snapshot_json);
  if (snapshot?.graph_send_available) {
    return {
      canSend: true,
      reason: "当前账户已开通 Graph 发信能力。",
      badge: "Graph 可发信",
    };
  }

  const apiMethod = account?.api_method?.toLowerCase();
  if (apiMethod === "graph" || apiMethod === "graph_api") {
    return {
      canSend: true,
      reason: "当前账户使用 Graph 通道，可直接发信。",
      badge: "Graph 可发信",
    };
  }

  return {
    canSend: false,
    reason: "当前账户为 IMAP 模式，仅 Graph 账户支持发信。",
    badge: "仅支持 Graph 发信",
  };
}

export function summarizeDeliveryStrategy(strategy?: DeliveryStrategy | null): string {
  if (!strategy) {
    return "暂无策略信息";
  }

  const providerChain = strategy.provider_order
    .map((provider) => mapProviderLabel(provider))
    .join(" → ");

  return [
    mapStrategyLabel(strategy.strategy_mode),
    strategy.resolved_provider ? `当前 ${mapProviderLabel(strategy.resolved_provider)}` : null,
    providerChain ? `链路 ${providerChain}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function normalizeProviderOverride(
  provider?: ProviderOverride | null
): ProviderOverride {
  return provider ?? "auto";
}
