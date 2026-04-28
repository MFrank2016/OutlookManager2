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

type RuleEvaluation = {
  rule_id?: number;
  rule_name?: string;
  matched?: boolean;
  reason?: string;
  checks?: Record<string, { configured?: boolean; matched?: boolean; pattern?: string | null }>;
};

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
      [rule.name, rule.sender_pattern, rule.subject_pattern, rule.body_pattern, rule.extract_pattern, rule.description]
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
    if (!selectedAccount || !selectedMessageId) return;
    const result = await testRule.mutateAsync({
      email_account: selectedAccount,
      message_id: selectedMessageId,
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
                        <div>发件人：{rule.sender_pattern || "-"}</div>
                        <div>主题：{rule.subject_pattern || "-"}</div>
                        <div>内容：{rule.body_pattern || "-"}</div>
                      </TableCell>
                      <TableCell className="max-w-[240px] break-all text-xs">{rule.extract_pattern}</TableCell>
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
                      {(email.subject || "(无主题)").slice(0, 44)} · {email.from_email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="text-xs text-muted-foreground">
                当前显示 {filteredEmails.length} / {emailsData?.emails?.length || 0} 封邮件
              </div>
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
              disabled={!selectedAccount || !selectedMessageId || testRule.isPending}
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
                            {evaluation.checks && (
                              <div className="mt-2 grid gap-2 sm:grid-cols-3">
                                {Object.entries(evaluation.checks).map(([key, value]) => (
                                  <div key={key} className="rounded-md bg-muted/40 px-2.5 py-2 text-xs">
                                    <div className="font-medium text-foreground">{key}</div>
                                    <div className="mt-1 text-muted-foreground">
                                      {value.configured ? (value.matched ? "已命中" : "未命中") : "未配置"}
                                    </div>
                                    {value.pattern && (
                                      <div className="mt-1 break-all text-[11px] text-muted-foreground/90">
                                        {value.pattern}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
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
