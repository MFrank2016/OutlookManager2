"use client";

import { useEffect, useMemo, useState } from "react";
import { Braces, ChevronDown, ChevronUp, Copy, History, Loader2, Play, RefreshCw, Search, Sparkles, Star } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageSection } from "@/components/layout/PageSection";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiDocBodyFieldDefinition,
  ApiDocHistoryEntry,
  ApiDocMessageCandidate,
  ApiDocRequestStateSnapshot,
  ApiDocScope,
  ApiDocOperation,
  appendRequestHistory,
  buildBodyPayloadFromFieldValues,
  buildResponsePreview,
  buildRequestUrl,
  extractMessageCandidates,
  filterJsonValue,
  matchesOperationScope,
  parseOpenApiSpec,
  pickDefaultOperation,
  toggleFavoriteOperation,
  tryParseJson,
} from "@/lib/apiDocs";
import { cn } from "@/lib/utils";

interface ResponseState {
  ok: boolean;
  status: number;
  durationMs: number;
  headers: Record<string, string>;
  body: string;
}

const SCOPE_OPTIONS: Array<{ value: ApiDocScope; label: string }> = [
  { value: "all", label: "全部接口" },
  { value: "v2", label: "仅 V2" },
  { value: "auth", label: "仅鉴权" },
  { value: "public", label: "仅公共" },
];

const FAVORITES_STORAGE_KEY = "api-docs-favorite-operations";
const HISTORY_STORAGE_KEY = "api-docs-request-history";
const GLOBALS_STORAGE_KEY = "api-docs-global-variables";
const MAX_HISTORY_ITEMS = 10;
const BODY_FIELD_DESKTOP_GRID = "md:grid-cols-[minmax(0,1.1fr)_112px_minmax(0,1.4fr)_minmax(0,0.9fr)_minmax(0,1fr)]";
const REQUEST_WORKSPACE_DESKTOP_GRID = "xl:grid-cols-[minmax(320px,0.82fr)_minmax(520px,1.18fr)]";
const RESPONSE_WORKSPACE_DESKTOP_GRID = "xl:grid-cols-[minmax(0,1fr)_360px]";

interface ApiDocGlobalVariables {
  token: string;
  email: string;
}

function prettyJson(value: unknown): string {
  if (value == null) {
    return "";
  }
  return JSON.stringify(value, null, 2);
}

function formatJsonLeaf(value: unknown): string {
  if (typeof value === "string") {
    return `"${value}"`;
  }
  if (value === null) {
    return "null";
  }
  if (typeof value === "undefined") {
    return "undefined";
  }
  return String(value);
}

function formatBodyFieldInput(field: ApiDocBodyFieldDefinition): string | boolean {
  if (field.editor === "boolean") {
    return typeof field.defaultValue === "boolean" ? field.defaultValue : false;
  }
  if (field.editor === "json") {
    if (field.defaultValue == null || field.defaultValue === "") {
      return "";
    }
    return JSON.stringify(field.defaultValue, null, 2);
  }
  if (field.defaultValue == null) {
    return "";
  }
  return String(field.defaultValue);
}

function formatBodyFieldTypeLabel(field: ApiDocBodyFieldDefinition): string {
  switch (field.editor) {
    case "number":
      return field.type === "integer" ? "integer" : "number";
    case "boolean":
      return "boolean";
    case "json":
      return field.type === "array" ? "array/json" : "object/json";
    case "text":
    default:
      return field.type || "string";
  }
}

function formatBodyFieldDefaultValue(value: unknown): string {
  if (value === null || typeof value === "undefined" || value === "") {
    return "—";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function normalizeBodyFieldComparisonValue(field: ApiDocBodyFieldDefinition, value: unknown): string {
  if (field.editor === "boolean") {
    return String(Boolean(value));
  }

  if (field.editor === "json") {
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (!trimmed) {
        return "";
      }
      try {
        return JSON.stringify(JSON.parse(trimmed));
      } catch {
        return trimmed;
      }
    }

    if (value == null || value === "") {
      return "";
    }

    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }

  if (value == null) {
    return "";
  }

  return String(value);
}

function isBodyFieldValueModified(field: ApiDocBodyFieldDefinition, value: unknown): boolean {
  return normalizeBodyFieldComparisonValue(field, value) !== normalizeBodyFieldComparisonValue(field, formatBodyFieldInput(field));
}

function JsonTreeNode({
  label,
  value,
  depth = 0,
  expandSignal,
  collapseSignal,
  searchActive,
}: {
  label?: string;
  value: unknown;
  depth?: number;
  expandSignal: number;
  collapseSignal: number;
  searchActive: boolean;
}) {
  const paddingClass = depth === 0 ? "" : "ml-4";
  const [isOpen, setIsOpen] = useState(depth < 1);

  useEffect(() => {
    setIsOpen(true);
  }, [expandSignal, searchActive]);

  useEffect(() => {
    if (!searchActive) {
      setIsOpen(false);
    }
  }, [collapseSignal, searchActive]);

  if (Array.isArray(value)) {
    return (
      <div className={cn("rounded-lg border border-border/60 bg-[color:var(--surface-2)]/55", paddingClass)}>
        <button
          type="button"
          onClick={() => setIsOpen((current) => !current)}
          className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-medium"
        >
          <span className="text-foreground">{label ?? "array"}</span>
          <span className="ml-2 text-xs text-muted-foreground">[{value.length}]</span>
        </button>
        {isOpen ? (
          <div className="space-y-2 px-3 pb-3">
            {value.map((item, index) => (
              <JsonTreeNode
                key={`${label ?? "array"}-${index}`}
                label={`[${index}]`}
                value={item}
                depth={depth + 1}
                expandSignal={expandSignal}
                collapseSignal={collapseSignal}
                searchActive={searchActive}
              />
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    return (
      <div className={cn("rounded-lg border border-border/60 bg-[color:var(--surface-2)]/55", paddingClass)}>
        <button
          type="button"
          onClick={() => setIsOpen((current) => !current)}
          className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-medium"
        >
          <span className="text-foreground">{label ?? "object"}</span>
          <span className="ml-2 text-xs text-muted-foreground">{`{${entries.length}}`}</span>
        </button>
        {isOpen ? (
          <div className="space-y-2 px-3 pb-3">
            {entries.map(([key, nestedValue]) => (
              <JsonTreeNode
                key={`${label ?? "object"}-${key}`}
                label={key}
                value={nestedValue}
                depth={depth + 1}
                expandSignal={expandSignal}
                collapseSignal={collapseSignal}
                searchActive={searchActive}
              />
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className={cn("flex items-start gap-2 rounded-lg border border-border/60 bg-[color:var(--surface-2)]/55 px-3 py-2 text-sm", paddingClass)}>
      <span className="min-w-0 shrink-0 font-medium text-foreground">{label ?? "value"}</span>
      <code className="break-all text-xs text-muted-foreground">{formatJsonLeaf(value)}</code>
    </div>
  );
}

export default function ApiDocsPage() {
  const [operations, setOperations] = useState<ApiDocOperation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [scope, setScope] = useState<ApiDocScope>("all");
  const [selectedOperationId, setSelectedOperationId] = useState<string>("");
  const [pathValues, setPathValues] = useState<Record<string, string>>({});
  const [queryValues, setQueryValues] = useState<Record<string, string>>({});
  const [headerValues, setHeaderValues] = useState<Record<string, string>>({});
  const [bodyValue, setBodyValue] = useState("");
  const [extraHeadersJson, setExtraHeadersJson] = useState("{}");
  const [useStoredToken, setUseStoredToken] = useState(true);
  const [responseState, setResponseState] = useState<ResponseState | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [openApiError, setOpenApiError] = useState<string | null>(null);
  const [hasStoredToken, setHasStoredToken] = useState(false);
  const [isGlobalVariablesExpanded, setIsGlobalVariablesExpanded] = useState(false);
  const [favoriteOperationIds, setFavoriteOperationIds] = useState<string[]>([]);
  const [requestHistory, setRequestHistory] = useState<ApiDocHistoryEntry[]>([]);
  const [pendingRestoreSnapshot, setPendingRestoreSnapshot] = useState<ApiDocRequestStateSnapshot | null>(null);
  const [bodyEditorMode, setBodyEditorMode] = useState<"json" | "visual">("json");
  const [bodyFieldValues, setBodyFieldValues] = useState<Record<string, string | boolean>>({});
  const [globalVariables, setGlobalVariables] = useState<ApiDocGlobalVariables>({ token: "", email: "" });
  const [jsonSearch, setJsonSearch] = useState("");
  const [jsonExpandSignal, setJsonExpandSignal] = useState(0);
  const [jsonCollapseSignal, setJsonCollapseSignal] = useState(0);
  const [messageHelperEmail, setMessageHelperEmail] = useState("");
  const [messageHelperMode, setMessageHelperMode] = useState<"v2" | "legacy">("v2");
  const [messageCandidates, setMessageCandidates] = useState<ApiDocMessageCandidate[]>([]);
  const [isLoadingMessageCandidates, setIsLoadingMessageCandidates] = useState(false);
  const [messageHelperError, setMessageHelperError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setHasStoredToken(Boolean(localStorage.getItem("auth_token")));

      try {
        const favorites = JSON.parse(localStorage.getItem(FAVORITES_STORAGE_KEY) ?? "[]") as string[];
        setFavoriteOperationIds(Array.isArray(favorites) ? favorites : []);
      } catch {
        setFavoriteOperationIds([]);
      }

      try {
        const history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) ?? "[]") as ApiDocHistoryEntry[];
        setRequestHistory(Array.isArray(history) ? history : []);
      } catch {
        setRequestHistory([]);
      }

      try {
        const globals = JSON.parse(localStorage.getItem(GLOBALS_STORAGE_KEY) ?? "{}") as Partial<ApiDocGlobalVariables>;
        setGlobalVariables({
          token: typeof globals.token === "string" ? globals.token : "",
          email: typeof globals.email === "string" ? globals.email : "",
        });
        setMessageHelperEmail(typeof globals.email === "string" ? globals.email : "");
      } catch {
        setGlobalVariables({ token: "", email: "" });
        setMessageHelperEmail("");
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favoriteOperationIds));
    }
  }, [favoriteOperationIds]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(requestHistory));
    }
  }, [requestHistory]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(GLOBALS_STORAGE_KEY, JSON.stringify(globalVariables));
    }
  }, [globalVariables]);

  useEffect(() => {
    let cancelled = false;

    const loadSpec = async () => {
      setIsLoading(true);
      setOpenApiError(null);

      try {
        const res = await fetch("/openapi.json");
        if (!res.ok) {
          throw new Error(`加载 OpenAPI 失败: ${res.status}`);
        }
        const spec = await res.json();
        const parsed = parseOpenApiSpec(spec);
        if (!cancelled) {
          setOperations(parsed);
          setSelectedOperationId((current) => current || pickDefaultOperation(parsed)?.id || "");
        }
      } catch (error) {
        if (!cancelled) {
          setOpenApiError(error instanceof Error ? error.message : "加载 OpenAPI 失败");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadSpec();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredOperations = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return operations.filter((item) => {
      if (!matchesOperationScope(item, scope)) {
        return false;
      }

      if (!keyword) {
        return true;
      }

      return [item.method, item.path, item.summary, item.description, item.tag]
        .filter(Boolean)
        .some((part) => part.toLowerCase().includes(keyword));
    });
  }, [operations, scope, search]);

  const scopeCounts = useMemo(() => {
    return SCOPE_OPTIONS.reduce<Record<ApiDocScope, number>>((acc, option) => {
      acc[option.value] = operations.filter((item) => matchesOperationScope(item, option.value)).length;
      return acc;
    }, {
      all: 0,
      v2: 0,
      auth: 0,
      public: 0,
    });
  }, [operations]);

  const selectedOperation = useMemo(
    () => operations.find((item) => item.id === selectedOperationId) ?? filteredOperations[0] ?? null,
    [operations, selectedOperationId, filteredOperations]
  );

  const favoriteOperations = useMemo(
    () =>
      favoriteOperationIds
        .map((operationId) => operations.find((item) => item.id === operationId) ?? null)
        .filter((item): item is ApiDocOperation => item !== null),
    [favoriteOperationIds, operations]
  );

  const selectedOperationIsFavorite = selectedOperation ? favoriteOperationIds.includes(selectedOperation.id) : false;

  const parsedResponseJson = useMemo(
    () => (responseState?.body ? tryParseJson(responseState.body) : null),
    [responseState?.body]
  );
  const filteredResponseJson = useMemo(
    () => (parsedResponseJson !== null ? filterJsonValue(parsedResponseJson, jsonSearch) : null),
    [parsedResponseJson, jsonSearch]
  );
  const visualBodyFields = useMemo(() => selectedOperation?.bodyFields ?? [], [selectedOperation]);
  const supportsVisualBodyEditor = visualBodyFields.length > 0;

  const visualBodyDraft = useMemo(() => {
    if (!supportsVisualBodyEditor) {
      return { payload: null, errors: [] as string[] };
    }
    return buildBodyPayloadFromFieldValues(visualBodyFields, bodyFieldValues);
  }, [bodyFieldValues, supportsVisualBodyEditor, visualBodyFields]);

  const effectiveBodyPreview = useMemo(() => {
    if (bodyEditorMode === "visual" && supportsVisualBodyEditor) {
      if (visualBodyDraft.payload && Object.keys(visualBodyDraft.payload).length > 0) {
        return prettyJson(visualBodyDraft.payload);
      }
      return "";
    }
    return bodyValue;
  }, [bodyEditorMode, bodyValue, supportsVisualBodyEditor, visualBodyDraft.payload]);

  const visualBodyStats = useMemo(() => {
    const requiredCount = visualBodyFields.filter((field) => field.required).length;
    const modifiedCount = visualBodyFields.filter((field) => isBodyFieldValueModified(field, bodyFieldValues[field.key])).length;

    return {
      totalCount: visualBodyFields.length,
      requiredCount,
      modifiedCount,
    };
  }, [bodyFieldValues, visualBodyFields]);

  const groupedOperations = useMemo(() => {
    return filteredOperations.reduce<Record<string, ApiDocOperation[]>>((acc, item) => {
      acc[item.tag] ||= [];
      acc[item.tag].push(item);
      return acc;
    }, {});
  }, [filteredOperations]);

  useEffect(() => {
    if (filteredOperations.length === 0) {
      return;
    }
    const isSelectedVisible = filteredOperations.some((item) => item.id === selectedOperationId);
    if (!isSelectedVisible) {
      setSelectedOperationId(pickDefaultOperation(filteredOperations)?.id || filteredOperations[0]!.id);
    }
  }, [filteredOperations, selectedOperationId]);

  useEffect(() => {
    if (!selectedOperation) {
      return;
    }

    if (pendingRestoreSnapshot) {
      setPathValues({ ...pendingRestoreSnapshot.pathValues });
      setQueryValues({ ...pendingRestoreSnapshot.queryValues });
      setHeaderValues({ ...pendingRestoreSnapshot.headerValues });
      setBodyValue(pendingRestoreSnapshot.bodyValue);
      setBodyEditorMode(pendingRestoreSnapshot.bodyEditorMode ?? (selectedOperation.bodyFields.length > 0 ? "visual" : "json"));
      setBodyFieldValues({ ...(pendingRestoreSnapshot.bodyFieldValues ?? {}) });
      setExtraHeadersJson(pendingRestoreSnapshot.extraHeadersJson);
      setGlobalVariables((current) => ({ ...current, token: pendingRestoreSnapshot.manualToken }));
      setUseStoredToken(pendingRestoreSnapshot.useStoredToken);
      setResponseState(null);
      setRequestError(null);
      setPendingRestoreSnapshot(null);
      return;
    }

    const nextPathValues: Record<string, string> = {};
    const nextQueryValues: Record<string, string> = {};
    const nextHeaderValues: Record<string, string> = {};

    for (const parameter of selectedOperation.parameters) {
      const defaultValue =
        parameter.example != null
          ? String(parameter.example)
          : parameter.schema && typeof parameter.schema.default !== "undefined"
            ? String(parameter.schema.default)
            : "";

      if (parameter.in === "path") {
        nextPathValues[parameter.name] = defaultValue;
      } else if (parameter.in === "query") {
        nextQueryValues[parameter.name] = defaultValue;
      } else if (parameter.in === "header") {
        nextHeaderValues[parameter.name] = defaultValue;
      }
    }

    setPathValues(nextPathValues);
    setQueryValues(nextQueryValues);
    setHeaderValues(nextHeaderValues);
    setBodyValue(selectedOperation.bodyTemplate ? prettyJson(selectedOperation.bodyTemplate) : "");
    setBodyEditorMode(selectedOperation.bodyFields.length > 0 ? "visual" : "json");
    setBodyFieldValues(
      Object.fromEntries(
        selectedOperation.bodyFields.map((field) => [field.key, formatBodyFieldInput(field)])
      )
    );
    setExtraHeadersJson("{}");
    setJsonSearch("");
    setResponseState(null);
    setRequestError(null);
  }, [pendingRestoreSnapshot, selectedOperation]);

  const curlPreview = useMemo(() => {
    if (!selectedOperation) {
      return "";
    }

    const url = buildRequestUrl(selectedOperation.path, pathValues, queryValues);
    const lines = [`curl -X ${selectedOperation.method} '${url}'`];

    const authToken = useStoredToken ? "<localStorage auth_token>" : globalVariables.token.trim();
    if (selectedOperation.requiresAuth && authToken) {
      lines.push(`  -H 'Authorization: Bearer ${authToken}'`);
    }

    for (const [key, value] of Object.entries(headerValues)) {
      if (value.trim()) {
        lines.push(`  -H '${key}: ${value}'`);
      }
    }

    if (effectiveBodyPreview.trim()) {
      lines.push("  -H 'Content-Type: application/json'");
      lines.push(`  -d '${effectiveBodyPreview.replace(/\n/g, "")}'`);
    }

    return lines.join(" \\\n");
  }, [selectedOperation, pathValues, queryValues, headerValues, effectiveBodyPreview, globalVariables.token, useStoredToken]);

  useEffect(() => {
    if (!messageHelperEmail && globalVariables.email) {
      setMessageHelperEmail(globalVariables.email);
    }
  }, [globalVariables.email, messageHelperEmail]);

  const resolveAuthToken = () => {
    if (useStoredToken && typeof window !== "undefined") {
      return localStorage.getItem("auth_token") || "";
    }
    return globalVariables.token.trim();
  };

  const applyGlobalVariablesToRequest = (messageId?: string) => {
    if (!selectedOperation) {
      return;
    }

    if (globalVariables.email) {
      setPathValues((current) => {
        const next = { ...current };
        for (const parameter of selectedOperation.parameters) {
          if (parameter.in === "path" && /(^email$|email_id)/i.test(parameter.name)) {
            next[parameter.name] = globalVariables.email;
          }
        }
        return next;
      });
      setQueryValues((current) => {
        const next = { ...current };
        for (const parameter of selectedOperation.parameters) {
          if (parameter.in === "query" && /(^email$|email_id)/i.test(parameter.name)) {
            next[parameter.name] = globalVariables.email;
          }
        }
        return next;
      });
    }

    if (messageId) {
      setPathValues((current) => {
        const next = { ...current };
        for (const parameter of selectedOperation.parameters) {
          if (parameter.in === "path" && /message_id/i.test(parameter.name)) {
            next[parameter.name] = messageId;
          }
        }
        return next;
      });
    }

    toast.success("已一键填充全局变量");
  };

  const focusOperation = (operationIds: string[]) => {
    const matched = operationIds
      .map((id) => operations.find((item) => item.id === id) ?? null)
      .find((item): item is ApiDocOperation => item !== null);

    if (!matched) {
      toast.error("未找到对应接口");
      return;
    }

    setSearch("");
    setScope("all");
    setSelectedOperationId(matched.id);
  };

  const loadMessageCandidates = async (emailOverride?: string) => {
    const targetEmail = (emailOverride ?? messageHelperEmail).trim();
    if (!targetEmail) {
      setMessageHelperError("请先输入邮箱 / 账户");
      return;
    }

    setIsLoadingMessageCandidates(true);
    setMessageHelperError(null);

    try {
      const requestUrl =
        messageHelperMode === "v2"
          ? `/api/v2/accounts/${encodeURIComponent(targetEmail)}/messages?page=1&page_size=20`
          : `/emails/${encodeURIComponent(targetEmail)}?page=1&page_size=20`;

      const headers = new Headers();
      const token = resolveAuthToken();
      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }

      const res = await fetch(requestUrl, { headers });
      if (!res.ok) {
        throw new Error(`查询邮件列表失败: ${res.status}`);
      }

      const payload = await res.json();
      const candidates = extractMessageCandidates(payload);
      setMessageCandidates(candidates);
      setGlobalVariables((current) => ({ ...current, email: targetEmail }));
      if (candidates.length === 0) {
        setMessageHelperError("当前邮箱暂无可用 message_id");
      }
    } catch (error) {
      setMessageCandidates([]);
      setMessageHelperError(error instanceof Error ? error.message : "查询邮件列表失败");
    } finally {
      setIsLoadingMessageCandidates(false);
    }
  };

  const handleRequest = async () => {
    if (!selectedOperation) {
      return;
    }

    const missingPathFields = selectedOperation.parameters
      .filter((item) => item.in === "path" && item.required)
      .filter((item) => !(pathValues[item.name] ?? "").trim())
      .map((item) => item.name);

    const bodyValidationErrors =
      bodyEditorMode === "visual" && supportsVisualBodyEditor
        ? visualBodyDraft.errors
        : (() => {
            if (!selectedOperation.bodyRequired && !bodyValue.trim()) {
              return [] as string[];
            }
            if (selectedOperation.bodyRequired && !bodyValue.trim()) {
              return ["请求体为必填 JSON"];
            }
            if (!bodyValue.trim()) {
              return [] as string[];
            }

            const parsedBody = tryParseJson(bodyValue);
            if (parsedBody === null) {
              return ["请求体不是合法 JSON"];
            }

            if (!supportsVisualBodyEditor || !selectedOperation.bodyFields.length || typeof parsedBody !== "object" || Array.isArray(parsedBody)) {
              return [] as string[];
            }

            return selectedOperation.bodyFields
              .filter((field) => field.required)
              .filter((field) => !String((parsedBody as Record<string, unknown>)[field.key] ?? "").trim())
              .map((field) => `${field.label} 为必填字段`);
          })();

    const bodyTextToSend =
      bodyEditorMode === "visual" && supportsVisualBodyEditor
        ? effectiveBodyPreview
        : bodyValue;

    if (missingPathFields.length > 0 || bodyValidationErrors.length > 0) {
      setRequestError([
        ...missingPathFields.map((item) => `缺少必填 path 参数：${item}`),
        ...bodyValidationErrors,
      ].join("；"));
      return;
    }

    setIsSubmitting(true);
    setRequestError(null);
    const requestSnapshot: ApiDocRequestStateSnapshot = {
      pathValues: { ...pathValues },
      queryValues: { ...queryValues },
      headerValues: { ...headerValues },
      bodyValue,
      bodyEditorMode,
      bodyFieldValues: { ...bodyFieldValues },
      extraHeadersJson,
      manualToken: globalVariables.token,
      useStoredToken,
    };

    try {
      const url = buildRequestUrl(selectedOperation.path, pathValues, queryValues);
      const headers = new Headers();

      const authToken = resolveAuthToken();

      if (selectedOperation.requiresAuth && authToken) {
        headers.set("Authorization", `Bearer ${authToken}`);
      }

      for (const [key, value] of Object.entries(headerValues)) {
        if (value.trim()) {
          headers.set(key, value.trim());
        }
      }

      if (extraHeadersJson.trim() && extraHeadersJson.trim() !== "{}") {
        const extraHeaders = JSON.parse(extraHeadersJson) as Record<string, string>;
        for (const [key, value] of Object.entries(extraHeaders)) {
          headers.set(key, value);
        }
      }

      let body: string | undefined;
      if (bodyTextToSend.trim()) {
        body = JSON.stringify(JSON.parse(bodyTextToSend));
        headers.set("Content-Type", "application/json");
      }

      const startedAt = performance.now();
      const res = await fetch(url, {
        method: selectedOperation.method,
        headers,
        body,
      });
      const durationMs = Math.round(performance.now() - startedAt);
      const text = await res.text();
      let formattedBody = text;
      try {
        formattedBody = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        // 保持原文本
      }

      setResponseState({
        ok: res.ok,
        status: res.status,
        durationMs,
        headers: Object.fromEntries(res.headers.entries()),
        body: formattedBody,
      });
      setRequestHistory((current) =>
        appendRequestHistory(
          current,
          {
            id: `${selectedOperation.id}:${Date.now()}`,
            operationId: selectedOperation.id,
            method: selectedOperation.method,
            path: selectedOperation.path,
            requestUrl: url,
            status: res.status,
            ok: res.ok,
            durationMs,
            requestedAt: new Date().toISOString(),
            responsePreview: buildResponsePreview(formattedBody),
            stateSnapshot: requestSnapshot,
          },
          MAX_HISTORY_ITEMS
        )
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "请求失败";
      setRequestError(errorMessage);
      setResponseState(null);
      const url = buildRequestUrl(selectedOperation.path, pathValues, queryValues);
      setRequestHistory((current) =>
        appendRequestHistory(
          current,
          {
            id: `${selectedOperation.id}:${Date.now()}`,
            operationId: selectedOperation.id,
            method: selectedOperation.method,
            path: selectedOperation.path,
            requestUrl: url,
            status: 0,
            ok: false,
            durationMs: 0,
            requestedAt: new Date().toISOString(),
            responsePreview: errorMessage,
            stateSnapshot: requestSnapshot,
          },
          MAX_HISTORY_ITEMS
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyText = async (content: string, successMessage: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success(successMessage);
    } catch (error) {
      console.error(error);
      toast.error("复制失败，请检查浏览器剪贴板权限");
    }
  };

  const handleFormatBody = () => {
    if (!bodyValue.trim()) {
      return;
    }

    try {
      setBodyValue(JSON.stringify(JSON.parse(bodyValue), null, 2));
      toast.success("请求体已格式化");
    } catch (error) {
      console.error(error);
      toast.error("请求体不是合法 JSON，无法格式化");
    }
  };

  const handleToggleFavorite = () => {
    if (!selectedOperation) {
      return;
    }

    setFavoriteOperationIds((current) => toggleFavoriteOperation(current, selectedOperation.id));
    toast.success(selectedOperationIsFavorite ? "已取消收藏接口" : "已收藏接口");
  };

  const restoreAllBodyFieldDefaults = () => {
    setBodyFieldValues(
      Object.fromEntries(
        visualBodyFields.map((field) => [field.key, formatBodyFieldInput(field)])
      )
    );
    toast.success("已回填全部默认值");
  };

  const restoreSingleBodyFieldDefault = (field: ApiDocBodyFieldDefinition) => {
    setBodyFieldValues((current) => ({
      ...current,
      [field.key]: formatBodyFieldInput(field),
    }));
  };

  const restoreHistoryEntry = (entry: ApiDocHistoryEntry) => {
    setSearch("");
    setScope("all");
    setSelectedOperationId(entry.operationId);
    setPendingRestoreSnapshot({
      pathValues: { ...entry.stateSnapshot.pathValues },
      queryValues: { ...entry.stateSnapshot.queryValues },
      headerValues: { ...entry.stateSnapshot.headerValues },
      bodyValue: entry.stateSnapshot.bodyValue,
      extraHeadersJson: entry.stateSnapshot.extraHeadersJson,
      manualToken: entry.stateSnapshot.manualToken,
      useStoredToken: entry.stateSnapshot.useStoredToken,
    });
    toast.success("已恢复请求");
  };

  return (
    <div className="page-enter flex h-[calc(100dvh-9rem)] min-h-0 flex-1 flex-col gap-3 md:h-[calc(100dvh-10rem)] md:gap-4">
      <PageHeader
        title="API 文档"
        description="在页面内直接浏览 OpenAPI、填写参数并执行接口调试。"
        actions={
          <Button variant="outline" size="sm" onClick={() => window.open("/docs", "_blank")}>
            打开 Swagger
          </Button>
        }
      />

      <div className="panel-surface overflow-hidden border border-border/70 bg-[color:var(--surface-1)]/75">
        <button
          type="button"
          onClick={() => setIsGlobalVariablesExpanded((current) => !current)}
          className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-[color:var(--surface-2)]/55"
        >
          <div className="min-w-0">
            <div className="text-sm font-semibold">全局变量设置</div>
            <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
              <span>Token：{globalVariables.token ? "已配置" : "未配置"}</span>
              <span>邮箱：{globalVariables.email || "未设置"}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{isGlobalVariablesExpanded ? "收起全局变量" : "展开全局变量"}</span>
            {isGlobalVariablesExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </button>

        {isGlobalVariablesExpanded ? (
          <div className="border-t border-border/70 px-4 py-4">
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <div className="space-y-3">
                <label className="flex items-center gap-3 rounded-lg border border-border/70 px-3 py-2 text-sm">
                  <Checkbox
                    checked={useStoredToken}
                    onCheckedChange={(checked) => setUseStoredToken(Boolean(checked))}
                  />
                  <span>优先使用当前登录 token</span>
                </label>
                <div className="rounded-lg border border-dashed border-border/70 px-3 py-2 text-xs text-muted-foreground">
                  {hasStoredToken
                    ? "已检测到本地 auth_token；勾选时默认使用当前登录 token，取消勾选后改用下面的全局 Token。"
                    : "当前未检测到本地 auth_token，建议在下面配置全局 Token，后续所有接口都会复用。"}
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">全局 Token</label>
                  <Input
                    value={globalVariables.token}
                    onChange={(event) =>
                      setGlobalVariables((current) => ({ ...current, token: event.target.value }))
                    }
                    placeholder="填写后可在所有接口复用"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-sm font-medium">邮箱 / 账户</label>
                  <Input
                    value={globalVariables.email}
                    onChange={(event) =>
                      setGlobalVariables((current) => ({ ...current, email: event.target.value }))
                    }
                    placeholder="用于 email、email_id 与 message_id 助手"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">额外请求头 JSON</label>
                  <Textarea
                    value={extraHeadersJson}
                    onChange={(event) => setExtraHeadersJson(event.target.value)}
                    className="min-h-[120px] font-mono text-xs"
                    placeholder='额外请求头 JSON，例如 {"X-API-Key":"demo"}'
                  />
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <PageSection
        title="V2 快速入口"
        description="重点关注 Microsoft Access Layer 新增的 `/api/v2` 能力。"
        contentClassName="flex flex-wrap gap-2"
      >
        <Badge variant="secondary">POST /api/v2/accounts/probe</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/health"}</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/delivery-strategy"}</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/messages"}</Badge>
        <Badge variant="secondary">POST /api/v2/accounts/import?mode=dry_run</Badge>
      </PageSection>

      <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="panel-surface flex min-h-0 flex-col overflow-hidden p-3">
          <div className="mb-3 flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-semibold">接口列表</div>
              <div className="text-xs text-muted-foreground">{filteredOperations.length} 个可调试接口</div>
            </div>
          </div>
          <Input
            placeholder="搜索 method / path / summary"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="mb-3"
          />

          <div className="mb-3 flex flex-wrap gap-2">
            {SCOPE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setScope(option.value)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all",
                  scope === option.value
                    ? "border-primary/50 bg-primary/12 text-primary shadow-sm"
                    : "border-border/70 bg-[color:var(--surface-1)]/80 text-muted-foreground hover:border-primary/25 hover:text-foreground",
                )}
              >
                <span>{option.label}</span>
                <span className="rounded-full bg-black/5 px-1.5 py-0.5 text-[11px] dark:bg-white/10">
                  {scopeCounts[option.value]}
                </span>
              </button>
            ))}
          </div>

          {favoriteOperations.length > 0 ? (
            <div className="mb-4 space-y-2 rounded-2xl border border-border/70 bg-[color:var(--surface-1)]/75 p-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">已收藏</div>
                <Badge variant="secondary">{favoriteOperations.length}</Badge>
              </div>
              <div className="space-y-2">
                {favoriteOperations.slice(0, 4).map((item) => (
                  <button
                    key={`favorite-${item.id}`}
                    type="button"
                    onClick={() => {
                      setSearch("");
                      setScope("all");
                      setSelectedOperationId(item.id);
                    }}
                    className={cn(
                      "w-full rounded-xl border px-3 py-2 text-left transition-all",
                      selectedOperation?.id === item.id
                        ? "border-amber-400/50 bg-amber-500/10"
                        : "border-border/70 bg-[color:var(--surface-2)]/65 hover:border-amber-400/30 hover:bg-[color:var(--surface-2)]/85",
                    )}
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <Star className="h-3.5 w-3.5 fill-current text-amber-500" />
                      <Badge variant="outline">{item.method}</Badge>
                    </div>
                    <div className="truncate text-sm font-medium">{item.path}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div className="space-y-4 overflow-y-auto pr-1">
            {filteredOperations.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border/70 px-3 py-6 text-sm text-muted-foreground">
                当前筛选条件下没有可展示接口，试试切换到“全部接口”或清空搜索词。
              </div>
            ) : null}

            {Object.entries(groupedOperations).map(([tag, items]) => (
              <div key={tag} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">{tag}</div>
                  <Badge variant="outline">{items.length}</Badge>
                </div>
                <div className="space-y-2">
                  {items.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedOperationId(item.id)}
                      className={cn(
                        "w-full rounded-xl border px-3 py-2 text-left transition-all",
                        selectedOperation?.id === item.id
                          ? "border-primary/40 bg-primary/10 shadow-sm"
                          : "border-border/70 bg-[color:var(--surface-1)]/75 hover:border-primary/25 hover:bg-[color:var(--surface-2)]/80",
                      )}
                    >
                      <div className="mb-1 flex items-center gap-2">
                        <Badge variant={item.method === "GET" ? "secondary" : "default"}>{item.method}</Badge>
                        {item.requiresAuth ? <Badge variant="outline">鉴权</Badge> : null}
                      </div>
                      <div className="truncate text-sm font-medium">{item.path}</div>
                      <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.summary}</div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </aside>

        <section className="panel-surface flex min-h-0 flex-col gap-4 overflow-y-auto p-4">
          {selectedOperation ? (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border/70 pb-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{selectedOperation.method}</Badge>
                    <code className="rounded bg-[color:var(--surface-2)] px-2 py-1 text-xs">{selectedOperation.path}</code>
                    <Badge variant="secondary">{selectedOperation.tag}</Badge>
                    {selectedOperation.requiresAuth ? <Badge variant="outline">需要鉴权</Badge> : null}
                  </div>
                  <div className="text-lg font-semibold">{selectedOperation.summary}</div>
                  <div className="text-sm text-muted-foreground">
                    {selectedOperation.description || "暂无详细描述，可直接在下方填写参数并发起调试。"}
                  </div>
                </div>
                <div className="grid w-full gap-2 rounded-2xl border border-border/70 bg-[color:var(--surface-2)]/55 p-1.5 shadow-sm sm:flex sm:w-auto sm:flex-wrap">
                  <Button
                    variant={selectedOperationIsFavorite ? "default" : "outline"}
                    onClick={handleToggleFavorite}
                    className="w-full justify-center sm:w-auto xl:min-w-[112px]"
                  >
                    <Star className={cn("mr-2 h-4 w-4", selectedOperationIsFavorite ? "fill-current" : "")} />
                    {selectedOperationIsFavorite ? "已收藏" : "收藏接口"}
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-center sm:w-auto xl:min-w-[112px]"
                    onClick={() => {
                      setPathValues({});
                      setQueryValues({});
                      setHeaderValues({});
                      setBodyValue(selectedOperation.bodyTemplate ? prettyJson(selectedOperation.bodyTemplate) : "");
                      setBodyEditorMode(selectedOperation.bodyFields.length > 0 ? "visual" : "json");
                      setBodyFieldValues(
                        Object.fromEntries(
                          selectedOperation.bodyFields.map((field) => [field.key, formatBodyFieldInput(field)])
                        )
                      );
                      setExtraHeadersJson("{}");
                      setJsonSearch("");
                      setResponseState(null);
                      setRequestError(null);
                    }}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    重置
                  </Button>
                  <Button onClick={() => void handleRequest()} disabled={isSubmitting} className="w-full justify-center sm:w-auto xl:min-w-[112px]">
                    {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                    发送请求
                  </Button>
                </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                <div className="mb-3 space-y-1">
                  <div className="text-sm font-semibold">简化调试</div>
                  <div className="text-xs text-muted-foreground">快捷聚焦常用接口，减少来回检索。</div>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 xl:flex xl:flex-wrap">
                  <Button variant="outline" size="sm" className="w-full justify-center xl:w-auto xl:min-w-[112px]" onClick={() => focusOperation(["GET /api"])}>
                    健康检查
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-center xl:w-auto xl:min-w-[112px]" onClick={() => focusOperation(["POST /auth/login", "GET /auth/me"])}>
                    鉴权接口
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-center xl:w-auto xl:min-w-[112px]" onClick={() => focusOperation(["GET /api/v2/accounts/{email}/messages"])}>
                    查看邮件列表
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-center xl:w-auto xl:min-w-[112px]" onClick={() => applyGlobalVariablesToRequest()}>
                    一键填充
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-center xl:w-auto xl:min-w-[112px]" onClick={() => void loadMessageCandidates()}>
                    查询邮件列表
                  </Button>
                </div>
              </div>

              <div className={cn("grid gap-4", REQUEST_WORKSPACE_DESKTOP_GRID)}>
                <div className="space-y-4">
                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 space-y-1">
                      <div className="text-sm font-semibold">请求参数</div>
                      <div className="text-xs text-muted-foreground">自动识别 path、query 与 header 参数，并按接口定义渲染。</div>
                    </div>
                    <div className="space-y-4">
                      {selectedOperation.parameters.filter((item) => item.in === "path").length > 0 ? (
                        <div className="space-y-3">
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">路径参数</div>
                          {selectedOperation.parameters
                            .filter((item) => item.in === "path")
                            .map((item) => (
                              <div key={`path-${item.name}`} className="space-y-1">
                                <label className="text-sm font-medium">
                                  {item.name}
                                  {item.required ? <span className="ml-1 text-red-500">*</span> : null}
                                </label>
                                <Input
                                  value={pathValues[item.name] ?? ""}
                                  onChange={(event) =>
                                    setPathValues((current) => ({ ...current, [item.name]: event.target.value }))
                                  }
                                  placeholder={item.description || item.name}
                                />
                              </div>
                            ))}
                        </div>
                      ) : null}

                      {selectedOperation.parameters.filter((item) => item.in === "query").length > 0 ? (
                        <div className="space-y-3">
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">查询参数</div>
                          {selectedOperation.parameters
                            .filter((item) => item.in === "query")
                            .map((item) => (
                              <div key={`query-${item.name}`} className="space-y-1">
                                <label className="text-sm font-medium">{item.name}</label>
                                <Input
                                  value={queryValues[item.name] ?? ""}
                                  onChange={(event) =>
                                    setQueryValues((current) => ({ ...current, [item.name]: event.target.value }))
                                  }
                                  placeholder={item.description || item.name}
                                />
                              </div>
                            ))}
                        </div>
                      ) : null}

                      {selectedOperation.parameters.filter((item) => item.in === "header").length > 0 ? (
                        <div className="space-y-3">
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">请求头参数</div>
                          {selectedOperation.parameters
                            .filter((item) => item.in === "header")
                            .map((item) => (
                              <div key={`header-${item.name}`} className="space-y-1">
                                <label className="text-sm font-medium">{item.name}</label>
                                <Input
                                  value={headerValues[item.name] ?? ""}
                                  onChange={(event) =>
                                    setHeaderValues((current) => ({ ...current, [item.name]: event.target.value }))
                                  }
                                  placeholder={item.description || item.name}
                                />
                              </div>
                            ))}
                        </div>
                      ) : null}

                      {selectedOperation.parameters.length === 0 ? (
                        <div className="rounded-lg border border-dashed border-border/70 px-3 py-4 text-sm text-muted-foreground">
                          当前接口未声明 path / query / header 参数。
                        </div>
                      ) : null}

                      {selectedOperation.parameters.some((item) => /(^email$|email_id|message_id)/i.test(item.name)) ? (
                        <div className="rounded-lg border border-dashed border-primary/25 bg-primary/5 px-3 py-3 text-xs text-muted-foreground">
                          检测到当前接口依赖邮箱或 message_id。可先在右侧配置全局变量，再使用“一键填充”或
                          “message_id 查看页”快速带入参数。
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 space-y-1">
                      <div className="text-sm font-semibold">鉴权与请求头</div>
                      <div className="text-xs text-muted-foreground">保留当前请求级别的鉴权开关与额外请求头配置。</div>
                    </div>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 rounded-lg border border-border/70 px-3 py-2 text-sm">
                        <Checkbox
                          checked={useStoredToken}
                          onCheckedChange={(checked) => setUseStoredToken(Boolean(checked))}
                        />
                        <span>优先使用当前登录 token</span>
                      </label>
                      <div className="rounded-lg border border-dashed border-border/70 px-3 py-2 text-xs text-muted-foreground">
                        {hasStoredToken
                          ? "已检测到本地 auth_token；勾选时默认使用当前登录 token，取消勾选后改用下面的全局 Token。"
                          : "当前未检测到本地 auth_token，建议在下面配置全局 Token，后续所有接口都会复用。"}
                      </div>
                      <div className="rounded-lg border border-dashed border-primary/20 bg-primary/5 px-3 py-2 text-xs text-muted-foreground">
                        全局 Token / 邮箱已移动到页面顶部的“全局变量设置”，这里保留当前请求的鉴权开关与额外请求头。
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="text-sm font-semibold">请求体</div>
                        <div className="text-xs text-muted-foreground">支持键值对填充与 JSON 双模式切换。</div>
                      </div>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex flex-wrap items-center gap-2">
                          {selectedOperation.bodyRequired ? (
                            <Badge variant="outline">必填 JSON</Badge>
                          ) : (
                            <Badge variant="secondary">可选</Badge>
                          )}
                        </div>
                        {supportsVisualBodyEditor ? (
                          <div className="grid w-full grid-cols-2 rounded-lg border border-border/70 bg-[color:var(--surface-2)]/60 p-1 sm:inline-flex sm:w-auto">
                            <button
                              type="button"
                              onClick={() => setBodyEditorMode("visual")}
                              className={cn(
                                "w-full rounded-md px-2 py-1 text-xs transition-colors",
                                bodyEditorMode === "visual" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground"
                              )}
                            >
                              键值对模式
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setBodyValue(effectiveBodyPreview || bodyValue);
                                setBodyEditorMode("json");
                              }}
                              className={cn(
                                "w-full rounded-md px-2 py-1 text-xs transition-colors",
                                bodyEditorMode === "json" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground"
                              )}
                            >
                              JSON 模式
                            </button>
                          </div>
                        ) : null}
                        <Button variant="outline" size="sm" onClick={handleFormatBody} className="w-full justify-center sm:w-auto">
                          <Sparkles className="mr-2 h-4 w-4" />
                          格式化 JSON
                        </Button>
                      </div>
                    </div>

                    {supportsVisualBodyEditor && bodyEditorMode === "visual" ? (
                      <div className="space-y-3">
                        <div className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-border/70 bg-[color:var(--surface-2)]/45 px-4 py-3">
                          <div className="space-y-2">
                            <div className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">字段概览</div>
                            <div className="flex flex-wrap gap-2">
                              <Badge variant="secondary">{visualBodyStats.totalCount} 个字段</Badge>
                              <Badge variant="outline">{visualBodyStats.requiredCount} 个必填</Badge>
                              <Badge variant={visualBodyStats.modifiedCount > 0 ? "default" : "secondary"}>
                                {visualBodyStats.modifiedCount > 0 ? `已修改 ${visualBodyStats.modifiedCount}` : "未修改"}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              适合先按字段填值，再切到 JSON 模式做最终检查。
                            </div>
                          </div>

                          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
                            <Button variant="outline" size="sm" onClick={restoreAllBodyFieldDefaults} className="w-full justify-center sm:w-auto">
                              回填全部默认值
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full justify-center sm:w-auto"
                              onClick={() => {
                                setBodyValue(effectiveBodyPreview || "");
                                setBodyEditorMode("json");
                              }}
                            >
                              查看 JSON 模式
                            </Button>
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-[color:var(--surface-2)]/45">
                          <div className={cn(
                            "hidden border-b border-border/70 px-3 py-2 md:grid",
                            BODY_FIELD_DESKTOP_GRID,
                            "gap-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground"
                          )}>
                            <div>键</div>
                            <div>值类型</div>
                            <div>当前值</div>
                            <div>默认值</div>
                            <div>说明</div>
                          </div>

                          <div className="space-y-3 p-3 md:space-y-0 md:divide-y md:divide-border/60 md:p-0">
                            {visualBodyFields.map((field) => (
                              <div
                                key={field.key}
                                className={cn(
                                  "space-y-3 rounded-xl border border-border/60 bg-background/70 p-3 md:grid md:gap-3 md:space-y-0 md:rounded-none md:border-0 md:bg-transparent md:px-3 md:py-3",
                                  BODY_FIELD_DESKTOP_GRID,
                                  isBodyFieldValueModified(field, bodyFieldValues[field.key])
                                    ? "bg-primary/5 ring-1 ring-primary/15 md:ring-0"
                                    : ""
                                )}
                              >
                                <div className="min-w-0">
                                  <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground md:hidden">
                                    键
                                  </div>
                                  <div className="flex flex-wrap items-center gap-2">
                                    <div className="truncate text-sm font-medium">
                                      {field.label}
                                      {field.required ? <span className="ml-1 text-red-500">*</span> : null}
                                    </div>
                                    {field.required ? <Badge variant="outline">必填</Badge> : null}
                                    {isBodyFieldValueModified(field, bodyFieldValues[field.key]) ? (
                                      <Badge variant="default">已修改</Badge>
                                    ) : (
                                      <Badge variant="secondary">默认值</Badge>
                                    )}
                                  </div>
                                  <div className="mt-1 text-xs text-muted-foreground">键值对填充模式</div>
                                </div>

                                <div className="min-w-0 space-y-2">
                                  <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground md:hidden">
                                    值类型
                                  </div>
                                  <Badge variant="outline" className="max-w-full truncate">
                                    {formatBodyFieldTypeLabel(field)}
                                  </Badge>
                                </div>

                                <div className="min-w-0 space-y-2">
                                  <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground md:hidden">
                                    当前值
                                  </div>
                                  {field.editor === "boolean" ? (
                                    <label className="flex h-10 items-center gap-2 rounded-lg border border-border/70 px-3 text-sm">
                                      <Checkbox
                                        checked={Boolean(bodyFieldValues[field.key])}
                                        onCheckedChange={(checked) =>
                                          setBodyFieldValues((current) => ({ ...current, [field.key]: Boolean(checked) }))
                                        }
                                      />
                                      <span>{Boolean(bodyFieldValues[field.key]) ? "true" : "false"}</span>
                                    </label>
                                  ) : field.editor === "json" ? (
                                    <Textarea
                                      value={String(bodyFieldValues[field.key] ?? "")}
                                      onChange={(event) =>
                                        setBodyFieldValues((current) => ({ ...current, [field.key]: event.target.value }))
                                      }
                                      className="min-h-[104px] font-mono text-xs"
                                      placeholder={field.description || `${field.key} 的 JSON 值`}
                                    />
                                  ) : (
                                    <Input
                                      type={field.editor === "number" ? "number" : "text"}
                                      value={String(bodyFieldValues[field.key] ?? "")}
                                      onChange={(event) =>
                                        setBodyFieldValues((current) => ({ ...current, [field.key]: event.target.value }))
                                      }
                                      placeholder={field.description || field.key}
                                    />
                                  )}
                                </div>

                                <div className="min-w-0 space-y-2">
                                  <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground md:hidden">
                                    默认值
                                  </div>
                                  <div className="space-y-2">
                                    <div className="break-all rounded-lg border border-dashed border-border/70 bg-[color:var(--surface-1)]/80 px-2 py-2 text-xs text-muted-foreground">
                                      {formatBodyFieldDefaultValue(field.defaultValue)}
                                    </div>
                                    {isBodyFieldValueModified(field, bodyFieldValues[field.key]) ? (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-7 px-2 text-xs"
                                        onClick={() => restoreSingleBodyFieldDefault(field)}
                                      >
                                        恢复默认值
                                      </Button>
                                    ) : null}
                                  </div>
                                </div>

                                <div className="min-w-0 space-y-2">
                                  <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground md:hidden">
                                    说明
                                  </div>
                                  <div className="break-words text-xs leading-5 text-muted-foreground">
                                    {field.description || "—"}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {visualBodyDraft.errors.length > 0 ? (
                          <div className="rounded-lg border border-amber-300/60 bg-amber-50 px-3 py-3 text-xs text-amber-700">
                            {visualBodyDraft.errors.join("；")}
                          </div>
                        ) : null}

                        <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                            <div>
                              <div className="text-sm font-semibold">生成的 JSON 草稿</div>
                              <div className="text-xs text-muted-foreground">可直接复制或切到 JSON 模式继续微调。</div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => void copyText(effectiveBodyPreview, "已复制 JSON 草稿")}
                              disabled={!effectiveBodyPreview.trim()}
                            >
                              <Copy className="mr-2 h-4 w-4" />
                              复制草稿
                            </Button>
                          </div>

                          {effectiveBodyPreview.trim() ? (
                            <pre className="overflow-x-auto rounded-xl border border-border/70 bg-background/80 p-3 font-mono text-xs leading-6 text-foreground">
                              {effectiveBodyPreview}
                            </pre>
                          ) : (
                            <div className="rounded-xl border border-dashed border-border/70 px-3 py-5 text-sm text-muted-foreground">
                              当前还没有可发送的 JSON 字段，填写至少一个字段后这里会实时生成请求草稿。
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Textarea
                        value={bodyValue}
                        onChange={(event) => setBodyValue(event.target.value)}
                        className="min-h-[280px] font-mono text-xs"
                        placeholder="当前接口无 JSON body，可留空。"
                      />
                    )}
                  </div>

                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="text-sm font-semibold">cURL 预览</div>
                        <div className="text-xs text-muted-foreground">跟随当前参数、鉴权与请求体实时生成。</div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-center sm:w-auto"
                        onClick={() => void copyText(curlPreview || "当前接口尚未生成请求预览", "cURL 已复制")}
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        复制 cURL
                      </Button>
                    </div>
                    <pre className="overflow-x-auto rounded-lg bg-slate-950 px-3 py-3 text-xs leading-6 text-slate-100">
                      {curlPreview || "当前接口尚未生成请求预览"}
                    </pre>
                  </div>

                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 space-y-1">
                      <div className="text-sm font-semibold">message_id 查看页</div>
                      <div className="text-xs text-muted-foreground">按邮箱查找邮件后，可直接把 message_id 带回当前请求。</div>
                    </div>
                    <div className="space-y-3">
                      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_repeat(2,minmax(0,120px))]">
                        <Input
                          value={messageHelperEmail}
                          onChange={(event) => setMessageHelperEmail(event.target.value)}
                          placeholder="根据邮箱查询对应邮件和 message_id"
                        />
                        <Button
                          variant={messageHelperMode === "v2" ? "default" : "outline"}
                          size="sm"
                          className="w-full justify-center"
                          onClick={() => setMessageHelperMode("v2")}
                        >
                          V2
                        </Button>
                        <Button
                          variant={messageHelperMode === "legacy" ? "default" : "outline"}
                          size="sm"
                          className="w-full justify-center"
                          onClick={() => setMessageHelperMode("legacy")}
                        >
                          V1
                        </Button>
                      </div>

                      <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full justify-center sm:w-auto"
                          onClick={() => void loadMessageCandidates()}
                          disabled={isLoadingMessageCandidates}
                        >
                          {isLoadingMessageCandidates ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                          查询邮件列表
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full justify-center sm:w-auto"
                          onClick={() => {
                            setMessageHelperEmail(globalVariables.email);
                            void loadMessageCandidates(globalVariables.email);
                          }}
                        >
                          使用全局邮箱
                        </Button>
                      </div>

                      {messageHelperError ? (
                        <div className="rounded-lg border border-amber-300/60 bg-amber-50 px-3 py-3 text-xs text-amber-700">
                          {messageHelperError}
                        </div>
                      ) : null}

                      {messageCandidates.length > 0 ? (
                        <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
                          {messageCandidates.map((candidate) => (
                            <div key={candidate.messageId} className="rounded-xl border border-border/70 bg-[color:var(--surface-2)]/60 p-3">
                              <div className="mb-1 text-sm font-medium">{candidate.subject}</div>
                              <div className="text-xs text-muted-foreground">
                                {candidate.fromEmail || "未知发件人"} · {candidate.date || "未知时间"}
                              </div>
                              <div className="mt-2 break-all rounded-md bg-[color:var(--surface-1)] px-2 py-1 font-mono text-[11px] text-muted-foreground">
                                {candidate.messageId}
                              </div>
                              <div className="mt-3 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="w-full justify-center sm:w-auto"
                                  onClick={() => applyGlobalVariablesToRequest(candidate.messageId)}
                                >
                                  应用到当前请求
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="w-full justify-center sm:w-auto"
                                  onClick={() => void copyText(candidate.messageId, "message_id 已复制")}
                                >
                                  复制 ID
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-lg border border-dashed border-border/70 px-3 py-4 text-xs text-muted-foreground">
                          查询后会在这里展示邮件列表及对应的 message_id，可直接带入当前接口调试。
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className={cn("grid gap-4", RESPONSE_WORKSPACE_DESKTOP_GRID)}>
                <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                  <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                      <div className="text-sm font-semibold">响应结果</div>
                      <div className="text-xs text-muted-foreground">支持状态码、响应头、结构视图与原始响应联合查看。</div>
                    </div>
                    <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
                      {responseState ? (
                        <>
                          <Badge variant={responseState.ok ? "default" : "destructive"}>
                            HTTP {responseState.status}
                          </Badge>
                          <Badge variant="secondary">{responseState.durationMs} ms</Badge>
                        </>
                      ) : null}
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-center sm:w-auto"
                        disabled={!responseState}
                        onClick={() => void copyText(responseState?.body || "", "响应已复制")}
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        复制响应
                      </Button>
                    </div>
                  </div>

                  {requestError ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">
                      {requestError}
                    </div>
                  ) : null}

                  {responseState ? (
                    <div className="space-y-3">
                      <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-3">
                        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">响应头</div>
                        <pre className="overflow-x-auto text-xs leading-6 text-muted-foreground">
                          {prettyJson(responseState.headers)}
                        </pre>
                      </div>

                      {parsedResponseJson !== null ? (
                        <div className="space-y-2 rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-3">
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                              <Braces className="h-4 w-4" />
                              JSON 结构视图
                            </div>
                            <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full justify-center sm:w-auto"
                                onClick={() => setJsonExpandSignal((current) => current + 1)}
                              >
                                全部展开
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full justify-center sm:w-auto"
                                onClick={() => setJsonCollapseSignal((current) => current + 1)}
                              >
                                全部折叠
                              </Button>
                            </div>
                          </div>
                          <Input
                            value={jsonSearch}
                            onChange={(event) => setJsonSearch(event.target.value)}
                            placeholder="响应搜索"
                          />
                          {filteredResponseJson !== null ? (
                            <JsonTreeNode
                              value={filteredResponseJson}
                              expandSignal={jsonExpandSignal}
                              collapseSignal={jsonCollapseSignal}
                              searchActive={Boolean(jsonSearch.trim())}
                            />
                          ) : (
                            <div className="rounded-lg border border-dashed border-border/70 px-3 py-4 text-xs text-muted-foreground">
                              当前搜索词没有命中任何 JSON 字段。
                            </div>
                          )}
                        </div>
                      ) : null}

                      <pre className="overflow-x-auto rounded-lg bg-slate-950 px-3 py-3 text-xs leading-6 text-slate-100">
                        {responseState.body || "(empty response body)"}
                      </pre>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border/70 px-3 py-8 text-sm text-muted-foreground">
                      发送请求后，这里会显示状态码、耗时、响应头和响应内容。
                    </div>
                  )}
                </div>

                <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4 xl:self-start xl:sticky xl:top-4">
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm font-semibold">
                        <History className="h-4 w-4 text-primary" />
                        请求历史
                      </div>
                      <div className="text-xs text-muted-foreground">保留最近一次的调试上下文，便于快速恢复和对比。</div>
                    </div>
                    <Badge variant="outline">{requestHistory.length}</Badge>
                  </div>

                  {requestHistory.length > 0 ? (
                    <div className="space-y-3">
                      {requestHistory.map((entry) => (
                        <div key={entry.id} className="rounded-xl border border-border/70 bg-[color:var(--surface-2)]/60 p-3">
                          <div className="mb-2 flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge variant={entry.ok ? "secondary" : "destructive"}>{entry.method}</Badge>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(entry.requestedAt).toLocaleTimeString("zh-CN", {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                    second: "2-digit",
                                  })}
                                </span>
                              </div>
                              <div className="mt-1 break-all text-sm font-medium">{entry.path}</div>
                            </div>
                            <Badge variant={entry.ok ? "default" : "destructive"}>
                              {entry.status || "ERR"}
                            </Badge>
                          </div>
                          <div className="mb-3 text-xs leading-5 text-muted-foreground">{entry.responsePreview}</div>
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <span className="text-xs text-muted-foreground">{entry.durationMs} ms</span>
                            <Button variant="outline" size="sm" className="w-full justify-center sm:w-auto" onClick={() => restoreHistoryEntry(entry)}>
                              恢复请求
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border/70 px-3 py-8 text-sm text-muted-foreground">
                      发送请求后，这里会记录最近的调试轨迹，便于快速恢复请求。
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex min-h-[50dvh] items-center justify-center rounded-xl border border-dashed border-border/70 text-sm text-muted-foreground">
              {isLoading
                ? "正在加载 OpenAPI..."
                : openApiError || "没有可用接口，请检查 openapi.json 是否可访问。"}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
