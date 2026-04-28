"use client";

import { useMemo, useState } from "react";
import { VerificationRule, VerificationRuleTestResult } from "@/types";
import { useVerificationRules, useDeleteVerificationRule, useTestVerificationRule } from "@/hooks/useAdmin";
import { useAccounts } from "@/hooks/useAccounts";
import { useEmails } from "@/hooks/useEmails";
import { VerificationRuleDialog } from "./VerificationRuleDialog";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Plus, Pencil, Trash2, Play } from "lucide-react";

export function VerificationRulesTab() {
  const { data } = useVerificationRules();
  const deleteRule = useDeleteVerificationRule();
  const testRule = useTestVerificationRule();
  const { data: accountsData } = useAccounts({ page_size: 100 });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<VerificationRule | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VerificationRule | null>(null);
  const [search, setSearch] = useState("");
  const [selectedAccount, setSelectedAccount] = useState("");
  const [selectedMessageId, setSelectedMessageId] = useState("");
  const [selectedRuleId, setSelectedRuleId] = useState<string>("all");
  const [testResult, setTestResult] = useState<VerificationRuleTestResult | null>(null);

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

  const { data: emailsData } = useEmails({
    account: selectedAccount,
    page: 1,
    page_size: 50,
    folder: "all",
    sortBy: "date",
    sortOrder: "desc",
  });

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
              <Select value={selectedAccount} onValueChange={(value) => {
                setSelectedAccount(value);
                setSelectedMessageId("");
              }}>
                <SelectTrigger><SelectValue placeholder="选择测试账号" /></SelectTrigger>
                <SelectContent>
                  {(accountsData?.accounts || []).map((account) => (
                    <SelectItem key={account.email_id} value={account.email_id}>
                      {account.email_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">邮件</div>
              <Select value={selectedMessageId} onValueChange={setSelectedMessageId} disabled={!selectedAccount}>
                <SelectTrigger><SelectValue placeholder="选择指定邮件" /></SelectTrigger>
                <SelectContent>
                  {(emailsData?.emails || []).map((email) => (
                    <SelectItem key={email.message_id} value={email.message_id}>
                      {email.subject || "(无主题)"} · {email.from_email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
              <Textarea
                readOnly
                rows={16}
                value={testResult ? JSON.stringify(testResult, null, 2) : "运行测试后，这里会显示命中规则、识别来源、提取结果和上下文。"}
              />
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
