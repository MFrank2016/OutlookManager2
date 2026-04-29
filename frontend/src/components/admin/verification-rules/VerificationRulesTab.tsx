"use client";

import { useEffect, useMemo, useState } from "react";
import { VerificationRule, VerificationRuleTestResult } from "@/types";
import { useVerificationRules, useDeleteVerificationRule, useTestVerificationRule } from "@/hooks/useAdmin";
import { useAccounts } from "@/hooks/useAccounts";
import { useEmails } from "@/hooks/useEmails";
import { VerificationRuleDialog } from "./VerificationRuleDialog";
import { filterVerificationTestEmails, sortVerificationTestEmails } from "./emailFilter";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Plus, Pencil, Trash2, Play, RefreshCw, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";

type RuleMatcher = {
  source_type?: "sender" | "subject" | "body";
  keyword?: string;
  sort_order?: number;
};

type RuleExtractorAttempt = {
  source_type?: "subject" | "body";
  extract_pattern?: string;
  sort_order?: number;
  matched?: boolean;
  code?: string | null;
};

type RuleEvaluation = {
  rule_id?: number;
  rule_name?: string;
  matched?: boolean;
  reason?: string;
  matched_matchers?: RuleMatcher[];
  extractor_attempts?: RuleExtractorAttempt[];
};

const SOURCE_LABELS: Record<string, string> = {
  sender: "发件人",
  subject: "主题",
  body: "内容",
};

const formatSourceLabel = (sourceType?: string) => SOURCE_LABELS[sourceType || ""] || sourceType || "-";

export function VerificationRulesTab() {
  const { data } = useVerificationRules();
  const deleteRule = useDeleteVerificationRule();
  const testRule = useTestVerificationRule();
  const [accountSearchInput, setAccountSearchInput] = useState("");
  const [accountSearch, setAccountSearch] = useState("");
  const [accountPage, setAccountPage] = useState(1);
  const { data: accountsData, isFetching: isAccountsFetching } = useAccounts({
    page: accountPage,
    page_size: 12,
    email_search: accountSearch || undefined,
  });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<VerificationRule | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VerificationRule | null>(null);
  const [search, setSearch] = useState("");
  const [selectedAccount, setSelectedAccount] = useState("");
  const [selectedMessageId, setSelectedMessageId] = useState("");
  const [manualMessageId, setManualMessageId] = useState("");
  const [selectedRuleId, setSelectedRuleId] = useState<string>("all");
  const [testResult, setTestResult] = useState<VerificationRuleTestResult | null>(null);
  const [emailRefreshNonce, setEmailRefreshNonce] = useState(0);
  const [emailSearchInput, setEmailSearchInput] = useState("");
  const [onlyCodeEmails, setOnlyCodeEmails] = useState(false);

  const rules = useMemo(() => data?.rules ?? [], [data?.rules]);
  const filteredRules = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return rules;
    return rules.filter((rule) =>
      [
        rule.name,
        rule.description,
        ...rule.matchers.map((matcher) => `${matcher.source_type} ${matcher.keyword}`),
        ...rule.extractors.map((extractor) => `${extractor.source_type} ${extractor.extract_pattern}`),
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    );
  }, [rules, search]);

  const { data: emailsData, isFetching: isEmailsFetching } = useEmails({
    account: selectedAccount,
    page: 1,
    page_size: 50,
    folder: "all",
    sortBy: "date",
    sortOrder: "desc",
    forceRefresh: emailRefreshNonce > 0,
    refreshNonce: emailRefreshNonce,
  });

  useEffect(() => {
    setSelectedMessageId("");
    setManualMessageId("");
    setEmailSearchInput("");
    setOnlyCodeEmails(false);
  }, [selectedAccount, emailRefreshNonce]);

  const filteredEmails = useMemo(
    () => sortVerificationTestEmails(
      filterVerificationTestEmails(emailsData?.emails || [], emailSearchInput),
      onlyCodeEmails
    ),
    [emailsData?.emails, emailSearchInput, onlyCodeEmails]
  );

  const selectedEmail = useMemo(
    () => filteredEmails.find((email) => email.message_id === selectedMessageId)
      || (emailsData?.emails || []).find((email) => email.message_id === selectedMessageId)
      || null,
    [filteredEmails, emailsData?.emails, selectedMessageId]
  );
  const ruleEvaluations = useMemo(
    () => (testResult?.rule_evaluations ?? []) as RuleEvaluation[],
    [testResult?.rule_evaluations]
  );

  const handleDelete = async () => {
    if (!deleteTarget) return;
    await deleteRule.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  };

  const handleRunTest = async (ruleId?: number) => {
    const effectiveMessageId = manualMessageId.trim() || selectedMessageId;
    if (!selectedAccount || !effectiveMessageId) return;
    const result = await testRule.mutateAsync({
      email_account: selectedAccount,
      message_id: effectiveMessageId,
      rule_id: ruleId,
    });
    setTestResult(result);
  };

  const handleRefreshEmails = () => {
    if (!selectedAccount) return;
    setEmailRefreshNonce((prev) => prev + 1);
  };

  const totalAccountPages = accountsData?.total_pages || 1;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Input
          placeholder="搜索规则名称、匹配条件或提取规则..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-md"
        />
        <Button
          onClick={() => {
            setEditingRule(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          新建规则
        </Button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)]">
        <Card className="panel-surface">
          <CardHeader>
            <CardTitle>验证码规则</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>规则</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>条件</TableHead>
                  <TableHead>提取</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">暂无规则</TableCell>
                  </TableRow>
                ) : (
                  filteredRules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium">{rule.name}</div>
                          <div className="text-xs text-muted-foreground">优先级 {rule.priority} · {rule.enabled ? "启用" : "停用"}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <Badge variant={rule.scope_type === "targeted" ? "default" : "secondary"}>
                            {rule.scope_type === "targeted" ? "定向" : "通用"}
                          </Badge>
                          <Badge variant="outline">{rule.match_mode.toUpperCase()}</Badge>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[280px] text-xs text-muted-foreground">
                        {rule.matchers.length === 0 ? (
                          <div>-</div>
                        ) : (
                          rule.matchers.map((matcher) => (
                            <div key={`${rule.id}-matcher-${matcher.id ?? matcher.sort_order}`}>
                              {formatSourceLabel(matcher.source_type)}：{matcher.keyword}
                            </div>
                          ))
                        )}
                      </TableCell>
                      <TableCell className="max-w-[240px] break-all text-xs">
                        {rule.extractors.length === 0 ? (
                          "-"
                        ) : (
                          <div className="space-y-1">
                            {rule.extractors.map((extractor) => (
                              <div key={`${rule.id}-extractor-${extractor.id ?? extractor.sort_order}`}>
                                {formatSourceLabel(extractor.source_type)}：{extractor.extract_pattern}
                              </div>
                            ))}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => {
                            setEditingRule(rule);
                            setDialogOpen(true);
                          }}>
                            <Pencil className="mr-1 h-3.5 w-3.5" />
                            编辑
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => setDeleteTarget(rule)}>
                            <Trash2 className="mr-1 h-3.5 w-3.5" />
                            删除
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="panel-surface">
          <CardHeader>
            <CardTitle>实时测试</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm font-medium">账号</div>
              <div className="flex items-center gap-2">
                <Input
                  value={accountSearchInput}
                  onChange={(e) => setAccountSearchInput(e.target.value)}
                  placeholder="按邮箱地址搜索账号"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setAccountPage(1);
                    setAccountSearch(accountSearchInput.trim());
                  }}
                  disabled={isAccountsFetching}
                >
                  <Search className="h-4 w-4" />
                </Button>
              </div>
              <Select value={selectedAccount} onValueChange={(value) => {
                setSelectedAccount(value);
                setSelectedMessageId("");
              }}>
                <SelectTrigger><SelectValue placeholder={isAccountsFetching ? "加载账号中..." : "选择测试账号"} /></SelectTrigger>
                <SelectContent>
                  {(accountsData?.accounts || []).map((account) => (
                    <SelectItem key={account.email_id} value={account.email_id}>
                      {account.email_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  第 {accountPage} / {totalAccountPages} 页
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAccountPage((prev) => Math.max(1, prev - 1))}
                    disabled={accountPage <= 1 || isAccountsFetching}
                  >
                    <ChevronLeft className="mr-1 h-3.5 w-3.5" />
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAccountPage((prev) => Math.min(totalAccountPages, prev + 1))}
                    disabled={accountPage >= totalAccountPages || isAccountsFetching}
                  >
                    下一页
                    <ChevronRight className="ml-1 h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-medium">邮件</div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefreshEmails}
                  disabled={!selectedAccount || isEmailsFetching}
                >
                  <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isEmailsFetching ? "animate-spin" : ""}`} />
                  刷新邮件
                </Button>
              </div>
              <Input
                value={emailSearchInput}
                onChange={(e) => setEmailSearchInput(e.target.value)}
                placeholder="按主题、发件人、邮件ID、验证码搜索邮件"
                disabled={!selectedAccount}
              />
              <label className="flex items-center gap-2 text-xs text-muted-foreground">
                <Checkbox
                  checked={onlyCodeEmails}
                  onCheckedChange={(checked) => setOnlyCodeEmails(checked === true)}
                  disabled={!selectedAccount}
                />
                只看含验证码邮件
              </label>
              <Select value={selectedMessageId} onValueChange={setSelectedMessageId} disabled={!selectedAccount}>
                <SelectTrigger><SelectValue placeholder={!selectedAccount ? "先选择测试账号" : isEmailsFetching ? "刷新邮件列表中..." : "选择指定邮件"} /></SelectTrigger>
                <SelectContent>
                  {filteredEmails.map((email) => (
                    <SelectItem key={email.message_id} value={email.message_id}>
                      <div className="flex flex-col gap-0.5 py-1">
                        <span className="max-w-[320px] truncate text-sm font-medium">
                          {(email.subject || "(无主题)").slice(0, 44)}
                        </span>
                        <span className="max-w-[320px] truncate text-xs text-muted-foreground">
                          {email.from_email}
                        </span>
                        <span className="max-w-[320px] truncate text-[11px] text-muted-foreground">
                          ID: {email.message_id}
                          {email.verification_code ? ` · 验证码: ${email.verification_code}` : ""}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                value={manualMessageId}
                onChange={(event) => setManualMessageId(event.target.value)}
                placeholder="手动输入 message_id，优先级高于下拉选择"
                disabled={!selectedAccount}
              />
              <div className="text-xs text-muted-foreground">
                当前显示 {filteredEmails.length} / {emailsData?.emails?.length || 0} 封邮件
              </div>
              {manualMessageId.trim() && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  当前测试将优先使用手输 message_id：{manualMessageId.trim()}
                </div>
              )}
              {selectedEmail && (
                <div className="rounded-xl border border-border/70 bg-background/60 p-3 text-xs text-muted-foreground space-y-1">
                  <div className="font-medium text-foreground">{selectedEmail.subject || "(无主题)"}</div>
                  <div>{selectedEmail.from_email}</div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span>ID: {selectedEmail.message_id}</span>
                    {selectedEmail.verification_code && (
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        验证码: {selectedEmail.verification_code}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">测试规则</div>
              <Select value={selectedRuleId} onValueChange={setSelectedRuleId}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">按正式顺序测试全部规则</SelectItem>
                  {rules.map((rule) => (
                    <SelectItem key={rule.id} value={String(rule.id)}>
                      {rule.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              className="w-full"
              disabled={!selectedAccount || (!selectedMessageId && !manualMessageId.trim()) || testRule.isPending}
              onClick={() => handleRunTest(selectedRuleId === "all" ? undefined : Number(selectedRuleId))}
            >
              <Play className="mr-2 h-4 w-4" />
              {testRule.isPending ? "测试中..." : "运行测试"}
            </Button>

            <div className="space-y-2">
              <div className="text-sm font-medium">测试结果</div>
              {testResult && (
                <div className="rounded-xl border border-border/70 bg-background/60 p-3 space-y-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={testResult.code ? "default" : "secondary"}>
                      {testResult.code ? "识别成功" : "未识别"}
                    </Badge>
                    {testResult.matched_via && (
                      <Badge variant="outline">{testResult.matched_via}</Badge>
                    )}
                    {testResult.code && (
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        结果: {testResult.code}
                      </Badge>
                    )}
                  </div>
                  {testResult.matched_rule && (
                    <div className="text-xs text-muted-foreground">
                      命中规则：{testResult.matched_rule.name} · {testResult.matched_rule.scope_type} · priority {testResult.matched_rule.priority}
                    </div>
                  )}
                  {testResult.resolved_code_source && (
                    <div className="text-xs text-muted-foreground">
                      命中来源：{formatSourceLabel(testResult.resolved_code_source)}
                    </div>
                  )}
                  {testResult.matched_subject && (
                    <div className="text-xs text-muted-foreground">
                      主题命中：{testResult.matched_subject}
                    </div>
                  )}
                  {testResult.matched_body_excerpt && (
                    <div className="text-xs text-muted-foreground">
                      摘要：{testResult.matched_body_excerpt}
                    </div>
                  )}

                  {testResult.matched_matchers && testResult.matched_matchers.length > 0 && (
                    <div className="space-y-2 rounded-lg border border-border/60 bg-background/70 p-3">
                      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        命中的 matcher
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {testResult.matched_matchers.map((matcher, index) => (
                          <Badge key={`${matcher.source_type}-${matcher.sort_order ?? index}`} variant="secondary">
                            {formatSourceLabel(matcher.source_type)} · {matcher.keyword}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {testResult.extractor_attempts && testResult.extractor_attempts.length > 0 && (
                    <div className="space-y-2 rounded-lg border border-border/60 bg-background/70 p-3">
                      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        extractor 尝试顺序
                      </div>
                      <div className="space-y-2">
                        {testResult.extractor_attempts.map((attempt, index) => (
                          <div key={`${attempt.source_type}-${attempt.sort_order ?? index}`} className="rounded-md bg-muted/40 px-3 py-2 text-xs">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant={attempt.matched ? "default" : "secondary"}>
                                {attempt.matched ? "命中" : "未命中"}
                              </Badge>
                              <span className="font-medium text-foreground">{formatSourceLabel(String(attempt.source_type || ""))}</span>
                              {attempt.code ? (
                                <span className="text-emerald-700">提取结果: {String(attempt.code)}</span>
                              ) : null}
                            </div>
                            {attempt.extract_pattern ? (
                              <div className="mt-1 break-all text-muted-foreground">{String(attempt.extract_pattern)}</div>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {ruleEvaluations.length > 0 && (
                    <div className="space-y-2 rounded-lg border border-border/60 bg-background/70 p-3">
                      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        规则命中过程
                      </div>
                      <div className="space-y-2">
                        {ruleEvaluations.map((evaluation, index) => (
                          <div key={`${evaluation.rule_id ?? "rule"}-${index}`} className="rounded-lg border border-border/60 bg-background/80 p-3">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant={evaluation.matched ? "default" : "secondary"}>
                                {evaluation.matched ? "命中" : "未命中"}
                              </Badge>
                              <span className="font-medium text-foreground">
                                {evaluation.rule_name || `规则 ${evaluation.rule_id ?? index + 1}`}
                              </span>
                              {evaluation.reason && (
                                <span className="text-xs text-muted-foreground">{evaluation.reason}</span>
                              )}
                            </div>
                            <div className="mt-2 grid gap-2">
                              {evaluation.matched_matchers && evaluation.matched_matchers.length > 0 ? (
                                <div className="rounded-md bg-muted/40 px-2.5 py-2 text-xs">
                                  <div className="font-medium text-foreground">命中的 matcher</div>
                                  <div className="mt-1 flex flex-wrap gap-2">
                                    {evaluation.matched_matchers.map((matcher, matcherIndex) => (
                                      <Badge key={`${matcher.source_type}-${matcher.sort_order ?? matcherIndex}`} variant="secondary">
                                        {formatSourceLabel(matcher.source_type)} · {matcher.keyword}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              ) : null}
                              {evaluation.extractor_attempts && evaluation.extractor_attempts.length > 0 ? (
                                <div className="rounded-md bg-muted/40 px-2.5 py-2 text-xs">
                                  <div className="font-medium text-foreground">extractor 尝试</div>
                                  <div className="mt-2 space-y-2">
                                    {evaluation.extractor_attempts.map((attempt, attemptIndex) => (
                                      <div key={`${attempt.source_type}-${attempt.sort_order ?? attemptIndex}`} className="rounded-md border border-border/50 bg-background/80 px-2 py-2">
                                        <div className="flex flex-wrap items-center gap-2">
                                          <Badge variant={attempt.matched ? "default" : "secondary"}>
                                            {attempt.matched ? "命中" : "未命中"}
                                          </Badge>
                                          <span className="font-medium text-foreground">{formatSourceLabel(attempt.source_type)}</span>
                                          {attempt.code ? <span className="text-emerald-700">结果: {attempt.code}</span> : null}
                                        </div>
                                        {attempt.extract_pattern ? (
                                          <div className="mt-1 break-all text-muted-foreground">{attempt.extract_pattern}</div>
                                        ) : null}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ) : null}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              <details className="rounded-xl border border-border/70 bg-background/60 p-3">
                <summary className="cursor-pointer text-sm font-medium">查看原始 JSON</summary>
                <Textarea
                  readOnly
                  rows={16}
                  className="mt-3"
                  value={testResult ? JSON.stringify(testResult, null, 2) : "运行测试后，这里会显示原始 JSON。"}
                />
              </details>
            </div>
          </CardContent>
        </Card>
      </div>

      <VerificationRuleDialog open={dialogOpen} onOpenChange={setDialogOpen} rule={editingRule} />

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除规则</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除规则 <strong>{deleteTarget?.name}</strong> 吗？此操作不可恢复。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">删除</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
