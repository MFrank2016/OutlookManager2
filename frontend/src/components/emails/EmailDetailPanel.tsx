"use client";

import { memo, useEffect, useRef, useState } from "react";
import { format } from "date-fns";
import { Check, Copy, RefreshCw, Trash } from "lucide-react";
import { toast } from "sonner";

import { DataEmptyState } from "@/components/ui/data-empty-state";
import { DataLoadingState } from "@/components/ui/data-loading-state";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useEmailDetail } from "@/hooks/useEmails";
import { copyToClipboard } from "@/lib/clipboard";
import { cn } from "@/lib/utils";
import { Email, ProviderOverride, StrategyMode } from "@/types";

const CountdownDisplay = memo(({ countdown }: { countdown: number }) => (
  <span className="text-xs font-mono text-[color:var(--text-soft)]">{countdown}s</span>
));
CountdownDisplay.displayName = "CountdownDisplay";

const EmailContent = memo(
  ({ content, viewMode, contentKey }: { content: string; viewMode: "html" | "text" | "source"; contentKey: string }) => {
    if (viewMode === "html") {
      return (
        <div
          key={contentKey}
          className="prose prose-slate max-w-none text-sm leading-relaxed dark:prose-invert"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      );
    }

    return (
      <pre key={contentKey} className="whitespace-pre-wrap rounded-xl bg-[color:var(--surface-1)]/75 p-4 text-sm font-mono">
        {content}
      </pre>
    );
  }
);
EmailContent.displayName = "EmailContent";

interface EmailDetailPanelProps {
  account: string;
  messageId: string;
  emailData?: Email | null;
  onDelete?: () => void;
  useV2?: boolean;
  overrideProvider?: ProviderOverride;
  strategyMode?: StrategyMode;
  skipCache?: boolean;
}

export function EmailDetailPanel({
  account,
  messageId,
  emailData,
  onDelete,
  useV2 = false,
  overrideProvider = "auto",
  strategyMode = "auto",
  skipCache = false,
}: EmailDetailPanelProps) {
  const hasFullContent = Boolean(emailData && (emailData.body_plain || emailData.body_html));
  const { data: emailDetail, isLoading, error, refetch, isRefetching } = useEmailDetail(
    account,
    messageId,
    {
      enabled: !hasFullContent,
      useV2,
      overrideProvider,
      strategyMode,
      skipCache,
    }
  );

  const email = hasFullContent ? emailData : emailDetail;
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<"html" | "text" | "source">("html");
  const [refreshCountdown, setRefreshCountdown] = useState(30);
  const [isAutoRefreshEnabled] = useState(true);
  const [stableEmailBody, setStableEmailBody] = useState("");
  const [stableEmailBodyKey, setStableEmailBodyKey] = useState("");

  const countdownRef = useRef(30);
  const refetchRef = useRef(refetch);

  useEffect(() => {
    refetchRef.current = refetch;
  }, [refetch]);

  useEffect(() => {
    if (!email) {
      return;
    }

    const currentKey = `${messageId}-${viewMode}`;
    if (currentKey !== stableEmailBodyKey) {
      let body = "";
      switch (viewMode) {
        case "html":
          body = email.body_html || email.body_plain || "";
          break;
        case "text":
          body = email.body_plain || "";
          break;
        case "source":
          body = email.body_html || email.body_plain || "";
          break;
        default:
          body = email.body_html || email.body_plain || "";
      }

      queueMicrotask(() => {
        setStableEmailBody(body);
        setStableEmailBodyKey(currentKey);
        setRefreshCountdown(30);
      });
      countdownRef.current = 30;
    }
  }, [email, messageId, stableEmailBodyKey, viewMode]);

  useEffect(() => {
    countdownRef.current = 30;
    queueMicrotask(() => setRefreshCountdown(30));
  }, [messageId]);

  useEffect(() => {
    if (hasFullContent || !isAutoRefreshEnabled || isLoading || !email) {
      return;
    }

    const interval = setInterval(() => {
      countdownRef.current -= 1;

      if (countdownRef.current <= 0) {
        refetchRef.current()
          .then(() => {
            countdownRef.current = 30;
            setRefreshCountdown(30);
          })
          .catch(() => {
            countdownRef.current = 30;
            setRefreshCountdown(30);
          });
      } else if (countdownRef.current % 5 === 0 || countdownRef.current <= 10) {
        setRefreshCountdown(countdownRef.current);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [email, hasFullContent, isAutoRefreshEnabled, isLoading, messageId]);

  const handleManualRefresh = async () => {
    if (hasFullContent) {
      toast.info("请刷新邮件列表以获取最新内容");
      return;
    }

    countdownRef.current = 30;
    setRefreshCountdown(30);
    await refetch();
    toast.success("邮件已刷新");
  };

  if (!hasFullContent && isLoading && !email) {
    return (
      <DataLoadingState
        title="正在加载邮件详情"
        description="邮件正文、验证码与元数据正在同步。"
        rows={2}
      />
    );
  }

  if (!hasFullContent && error) {
    return (
      <DataEmptyState
        title="加载失败"
        description="邮件详情暂时不可用，请稍后重试。"
      />
    );
  }

  if (!email) {
    return (
      <DataEmptyState
        title="请选择一封邮件"
        description="从左侧列表中选择一封邮件，即可在这里查看正文、验证码与操作。"
      />
    );
  }

  const handleCopyCode = async (code: string) => {
    const success = await copyToClipboard(code);
    if (success) {
      setCopied(true);
      toast.success("验证码已复制到剪贴板");
      setTimeout(() => setCopied(false), 2000);
    } else {
      toast.error("复制失败，请手动复制");
    }
  };

  const emailContentKey = `${messageId}-${viewMode}`;

  return (
    <div className="panel-surface flex h-full min-h-0 flex-col overflow-hidden">
      <div className="border-b border-border/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.78),rgba(248,250,252,0.92))] px-4 py-4 md:px-5">
        <div className="flex flex-wrap items-start gap-3">
          <div className="min-w-0 flex-1 space-y-1">
            <h2 className="break-words pr-4 text-lg font-semibold text-foreground">{email.subject}</h2>
            <p className="text-sm text-[color:var(--text-soft)]">
              在这里查看正文、验证码、原始来源与快速动作。
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isAutoRefreshEnabled && !hasFullContent ? <CountdownDisplay countdown={refreshCountdown} /> : null}
            {onDelete ? (
              <Button
                variant="ghost"
                size="sm"
                className="text-red-600 hover:bg-red-50 hover:text-red-700"
                onClick={onDelete}
              >
                <Trash className="mr-1 h-4 w-4" /> 删除
              </Button>
            ) : null}
            <Button variant="ghost" size="icon" onClick={handleManualRefresh} disabled={isRefetching} title="刷新邮件">
              <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
            </Button>
          </div>
        </div>
      </div>

      <div className="border-b border-border/70 bg-[color:var(--surface-1)]/45 px-4 py-4 md:px-5">
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div>
            <span className="font-medium text-[color:var(--text-soft)]">发件人：</span>
            <span className="text-foreground">{email.from_email}</span>
          </div>
          <div>
            <span className="font-medium text-[color:var(--text-soft)]">收件人：</span>
            <span className="text-foreground">{email.to_email || "无"}</span>
          </div>
          <div>
            <span className="font-medium text-[color:var(--text-soft)]">日期：</span>
            <span className="text-foreground">{format(new Date(email.date), "yyyy-MM-dd HH:mm:ss")}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-[color:var(--text-soft)]">邮件 ID：</span>
            <code className="break-all rounded bg-[color:var(--surface-1)]/75 px-2 py-1 text-xs text-foreground">
              {email.message_id}
            </code>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={async () => {
                const success = await copyToClipboard(email.message_id);
                if (success) {
                  toast.success("邮件 ID 已复制");
                } else {
                  toast.error("复制失败，请手动复制");
                }
              }}
            >
              <Copy className="mr-1 h-3.5 w-3.5" /> 复制
            </Button>
          </div>
        </div>
      </div>

      <div className="border-b border-border/70 bg-[color:var(--surface-1)]/35 px-4 py-3 md:px-5">
        <div className="flex flex-wrap gap-2">
          <Button variant={viewMode === "html" ? "default" : "outline"} size="sm" onClick={() => setViewMode("html")}>HTML 视图</Button>
          <Button variant={viewMode === "text" ? "default" : "outline"} size="sm" onClick={() => setViewMode("text")}>纯文本</Button>
          <Button variant={viewMode === "source" ? "default" : "outline"} size="sm" onClick={() => setViewMode("source")}>源码</Button>
        </div>
      </div>

      {email.verification_code ? (
        <div className="border-b border-green-200 bg-green-50 px-4 py-4 md:px-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-green-800">检测到验证码</span>
              <code className="rounded bg-white px-2 py-1 text-base font-bold text-green-900">{email.verification_code}</code>
            </div>
            <Button variant="outline" size="sm" className="border-green-300 text-green-700 hover:bg-green-100" onClick={() => handleCopyCode(email.verification_code!)}>
              {copied ? (
                <>
                  <Check className="mr-1 h-4 w-4" /> 已复制
                </>
              ) : (
                <>
                  <Copy className="mr-1 h-4 w-4" /> 复制
                </>
              )}
            </Button>
          </div>
        </div>
      ) : null}

      <ScrollArea className="min-h-0 flex-1 px-4 py-5 md:px-5">
        <EmailContent content={stableEmailBody} viewMode={viewMode} contentKey={emailContentKey} />
      </ScrollArea>
    </div>
  );
}
