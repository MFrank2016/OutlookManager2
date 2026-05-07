"use client";

import { format } from "date-fns";
import { ChevronLeft, ChevronRight, Copy, Eye, Trash } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DataEmptyState } from "@/components/ui/data-empty-state";
import { DataLoadingState } from "@/components/ui/data-loading-state";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Email } from "@/types";

interface EmailListPanelProps {
  emails: Email[];
  isLoading: boolean;
  activeEmailId: string | null;
  searchKeyword: string;
  page: number;
  pageSize: number;
  totalPages: number;
  totalEmails: number;
  jumpPage: string;
  onJumpPageChange: (value: string) => void;
  onJumpPage: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
  onPageSizeChange: (value: string) => void;
  onOpenEmail: (messageId: string, email: Email) => void;
  onDeleteRequest: (messageId: string) => void;
  onCopyCode: (code: string) => void;
}

function getSenderDisplay(fromEmail: string) {
  if (!fromEmail.includes("<")) {
    return {
      name: fromEmail,
      email: "",
    };
  }

  const parts = fromEmail.split("<");
  return {
    name: parts[0].trim().replace(/^['"]+|['"]+$/g, ""),
    email: parts[1].replace(">", "").trim(),
  };
}

export function EmailListPanel({
  emails,
  isLoading,
  activeEmailId,
  searchKeyword,
  page,
  pageSize,
  totalPages,
  totalEmails,
  jumpPage,
  onJumpPageChange,
  onJumpPage,
  onPrevPage,
  onNextPage,
  onPageSizeChange,
  onOpenEmail,
  onDeleteRequest,
  onCopyCode,
}: EmailListPanelProps) {
  if (isLoading && emails.length === 0) {
    return (
      <DataLoadingState
        title="正在加载邮件"
        description="邮件列表与验证码摘要正在同步。"
      />
    );
  }

  if (emails.length === 0) {
    return (
      <DataEmptyState
        title={searchKeyword ? "未找到匹配邮件" : "暂无邮件数据"}
        description={
          searchKeyword
            ? "你可以调整搜索词、账户或文件夹后再试一次。"
            : "当前账户或文件夹下还没有可展示的邮件。"
        }
      />
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <ScrollArea className="min-h-0 flex-1 pr-1">
        <div className="space-y-4 pb-1">
          <div className="grid gap-3">
            {emails.map((email) => {
              const sender = getSenderDisplay(email.from_email);
              return (
                <Card
                  key={email.message_id}
                  className={cn(
                    "cursor-pointer border-border/70 p-0",
                    email.verification_code && "border-amber-300/70 bg-amber-50/70 shadow-[0_12px_24px_rgba(251,191,36,0.10)]",
                    activeEmailId === email.message_id && "border-primary/35"
                  )}
                  onClick={() => onOpenEmail(email.message_id, email)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-2.5">
                        <Avatar className="h-10 w-10 shrink-0">
                          <AvatarFallback className="bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-sm font-semibold text-[color:var(--primary-foreground)]">
                            {email.sender_initial}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-foreground">{sender.name}</div>
                          <div className="truncate text-xs text-[color:var(--text-faint)]">
                            {sender.email || email.from_email}
                          </div>
                        </div>
                      </div>
                      <div className="shrink-0 whitespace-nowrap text-xs text-[color:var(--text-faint)]">
                        {format(new Date(email.date), "MM-dd HH:mm")}
                      </div>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="space-y-1">
                        <div className="line-clamp-2 text-sm font-semibold text-foreground">{email.subject}</div>
                        <div className="truncate text-[11px] text-[color:var(--text-faint)]">ID: {email.message_id}</div>
                      </div>

                      {email.verification_code ? (
                        <Button
                          variant="outline"
                          className="w-full justify-center border-amber-300 bg-amber-50/90 text-amber-700 hover:bg-amber-100"
                          onClick={(event) => {
                            event.stopPropagation();
                            onCopyCode(email.verification_code!);
                          }}
                        >
                          <Copy className="mr-1.5 h-3.5 w-3.5" />
                          复制验证码 {email.verification_code}
                        </Button>
                      ) : null}

                      <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/75 px-3 py-2.5">
                        <p className="line-clamp-2 text-xs leading-relaxed text-[color:var(--text-soft)]">
                          {email.body_preview || "暂无预览内容"}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-3"
                          onClick={(event) => {
                            event.stopPropagation();
                            onOpenEmail(email.message_id, email);
                          }}
                        >
                          <Eye className="mr-1.5 h-3.5 w-3.5" />
                          查看详情
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-3 text-red-600 hover:text-red-700"
                          onClick={(event) => {
                            event.stopPropagation();
                            onDeleteRequest(email.message_id);
                          }}
                        >
                          <Trash className="mr-1.5 h-3.5 w-3.5" />
                          删除
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </ScrollArea>

      {totalEmails > 0 ? (
        <div className="flex items-center justify-between gap-2 rounded-xl border border-border/70 bg-[color:var(--surface-1)]/75 p-3 text-xs md:text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground whitespace-nowrap">共 {totalEmails} 封</span>
            <div className="flex items-center gap-1.5">
              <span className="text-muted-foreground whitespace-nowrap">每页</span>
              <Select value={pageSize.toString()} onValueChange={onPageSizeChange}>
                <SelectTrigger className="w-[78px]" size="sm">
                  <SelectValue placeholder="20" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                  <SelectItem value="500">500</SelectItem>
                  <SelectItem value="1000">1000</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={onPrevPage} disabled={page === 1 || isLoading}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex min-w-[80px] items-center justify-center text-sm">
              <span>{page} / {totalPages}</span>
            </div>
            <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={onNextPage} disabled={page >= totalPages || isLoading}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          <div className="hidden items-center gap-2 sm:flex">
            <Input
              className="h-8 w-[64px] px-2 text-center text-sm"
              placeholder="页码"
              type="number"
              min={1}
              max={totalPages}
              value={jumpPage}
              onChange={(event) => onJumpPageChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onJumpPage();
                }
              }}
            />
            <Button variant="outline" size="sm" className="h-8 px-3" onClick={onJumpPage} disabled={!jumpPage}>
              跳转
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
