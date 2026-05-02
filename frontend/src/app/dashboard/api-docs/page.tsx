"use client";

import { useEffect, useMemo, useState } from "react";
import { Copy, Loader2, Play, RefreshCw, Search, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageSection } from "@/components/layout/PageSection";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiDocScope,
  ApiDocOperation,
  buildRequestUrl,
  matchesOperationScope,
  parseOpenApiSpec,
  pickDefaultOperation,
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

function prettyJson(value: unknown): string {
  if (value == null) {
    return "";
  }
  return JSON.stringify(value, null, 2);
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
  const [manualToken, setManualToken] = useState("");
  const [extraHeadersJson, setExtraHeadersJson] = useState("{}");
  const [useStoredToken, setUseStoredToken] = useState(true);
  const [responseState, setResponseState] = useState<ResponseState | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [openApiError, setOpenApiError] = useState<string | null>(null);
  const [hasStoredToken, setHasStoredToken] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setHasStoredToken(Boolean(localStorage.getItem("auth_token")));
    }
  }, []);

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
    setResponseState(null);
    setRequestError(null);
  }, [selectedOperation]);

  const curlPreview = useMemo(() => {
    if (!selectedOperation) {
      return "";
    }

    const url = buildRequestUrl(selectedOperation.path, pathValues, queryValues);
    const lines = [`curl -X ${selectedOperation.method} '${url}'`];

    const authToken = useStoredToken ? "<localStorage auth_token>" : manualToken.trim();
    if (selectedOperation.requiresAuth && authToken) {
      lines.push(`  -H 'Authorization: Bearer ${authToken}'`);
    }

    for (const [key, value] of Object.entries(headerValues)) {
      if (value.trim()) {
        lines.push(`  -H '${key}: ${value}'`);
      }
    }

    if (bodyValue.trim()) {
      lines.push("  -H 'Content-Type: application/json'");
      lines.push(`  -d '${bodyValue.replace(/\n/g, "")}'`);
    }

    return lines.join(" \\\n");
  }, [selectedOperation, pathValues, queryValues, headerValues, bodyValue, manualToken, useStoredToken]);

  const handleRequest = async () => {
    if (!selectedOperation) {
      return;
    }

    setIsSubmitting(true);
    setRequestError(null);

    try {
      const url = buildRequestUrl(selectedOperation.path, pathValues, queryValues);
      const headers = new Headers();

      const authToken =
        useStoredToken
          ? typeof window !== "undefined"
            ? localStorage.getItem("auth_token") || ""
            : ""
          : manualToken.trim();

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
      if (bodyValue.trim()) {
        body = JSON.stringify(JSON.parse(bodyValue));
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
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : "请求失败");
      setResponseState(null);
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

  return (
    <div className="page-enter flex h-full min-h-[70dvh] flex-col gap-3 md:gap-4">
      <PageHeader
        title="API 文档"
        description="在页面内直接浏览 OpenAPI、填写参数并执行接口调试。"
        actions={
          <Button variant="outline" size="sm" onClick={() => window.open("/docs", "_blank")}>
            打开 Swagger
          </Button>
        }
      />

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

      <div className="grid min-h-[66dvh] gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="panel-surface flex min-h-[66dvh] flex-col overflow-hidden p-3">
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

        <section className="panel-surface flex min-h-[66dvh] flex-col gap-4 p-4">
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
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setPathValues({});
                      setQueryValues({});
                      setHeaderValues({});
                      setBodyValue(selectedOperation.bodyTemplate ? prettyJson(selectedOperation.bodyTemplate) : "");
                      setExtraHeadersJson("{}");
                      setResponseState(null);
                      setRequestError(null);
                    }}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    重置
                  </Button>
                  <Button onClick={() => void handleRequest()} disabled={isSubmitting}>
                    {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                    发送请求
                  </Button>
                </div>
              </div>

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
                <div className="space-y-4">
                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 text-sm font-semibold">请求参数</div>
                    <div className="space-y-4">
                      {selectedOperation.parameters.filter((item) => item.in === "path").length > 0 ? (
                        <div className="space-y-3">
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">Path Params</div>
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
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">Query Params</div>
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
                          <div className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">Header Params</div>
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
                          当前接口没有显式 path / query / header 参数。
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 text-sm font-semibold">鉴权与请求头</div>
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
                          ? "已检测到本地 auth_token，可直接调试需要鉴权的接口。"
                          : "当前未检测到本地 auth_token，如需调试鉴权接口，请切换为手动输入。"}
                      </div>
                      {!useStoredToken ? (
                        <Input
                          value={manualToken}
                          onChange={(event) => setManualToken(event.target.value)}
                          placeholder="手动填写 Bearer Token"
                        />
                      ) : null}
                      <Textarea
                        value={extraHeadersJson}
                        onChange={(event) => setExtraHeadersJson(event.target.value)}
                        className="min-h-[120px] font-mono text-xs"
                        placeholder='额外请求头 JSON，例如 {"X-API-Key":"demo"}'
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <div className="text-sm font-semibold">请求体</div>
                      <div className="flex items-center gap-2">
                        {selectedOperation.bodyRequired ? (
                          <Badge variant="outline">必填 JSON</Badge>
                        ) : (
                          <Badge variant="secondary">可选</Badge>
                        )}
                        <Button variant="outline" size="sm" onClick={handleFormatBody}>
                          <Sparkles className="mr-2 h-4 w-4" />
                          格式化 JSON
                        </Button>
                      </div>
                    </div>
                    <Textarea
                      value={bodyValue}
                      onChange={(event) => setBodyValue(event.target.value)}
                      className="min-h-[280px] font-mono text-xs"
                      placeholder="当前接口无 JSON body，可留空。"
                    />
                  </div>

                  <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="text-sm font-semibold">cURL 预览</div>
                      <Button
                        variant="outline"
                        size="sm"
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
                </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/70 p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold">响应结果</div>
                  <div className="flex items-center gap-2">
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
