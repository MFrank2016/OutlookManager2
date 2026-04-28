"use client";

import { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { VerificationRule } from "@/types";
import { useCreateVerificationRule, useUpdateVerificationRule } from "@/hooks/useAdmin";

interface VerificationRuleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule?: VerificationRule | null;
}

interface FormState {
  name: string;
  scope_type: "targeted" | "global";
  match_mode: "and" | "or";
  priority: number;
  enabled: boolean;
  sender_pattern: string;
  subject_pattern: string;
  body_pattern: string;
  extract_pattern: string;
  is_regex: boolean;
  description: string;
}

const DEFAULT_FORM: FormState = {
  name: "",
  scope_type: "global",
  match_mode: "and",
  priority: 0,
  enabled: true,
  sender_pattern: "",
  subject_pattern: "",
  body_pattern: "",
  extract_pattern: "",
  is_regex: true,
  description: "",
};

export function VerificationRuleDialog({ open, onOpenChange, rule }: VerificationRuleDialogProps) {
  const isEditing = !!rule;
  const createRule = useCreateVerificationRule();
  const updateRule = useUpdateVerificationRule();
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);

  const submitting = createRule.isPending || updateRule.isPending;

  const initialForm = useMemo<FormState>(() => {
    if (!rule) return DEFAULT_FORM;
    return {
      name: rule.name,
      scope_type: rule.scope_type,
      match_mode: rule.match_mode,
      priority: rule.priority,
      enabled: rule.enabled,
      sender_pattern: rule.sender_pattern || "",
      subject_pattern: rule.subject_pattern || "",
      body_pattern: rule.body_pattern || "",
      extract_pattern: rule.extract_pattern,
      is_regex: rule.is_regex,
      description: rule.description || "",
    };
  }, [rule]);

  useEffect(() => {
    if (open) {
      setForm(initialForm);
    }
  }, [open, initialForm]);

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    const payload = {
      ...form,
      priority: Number(form.priority) || 0,
      sender_pattern: form.sender_pattern.trim() || undefined,
      subject_pattern: form.subject_pattern.trim() || undefined,
      body_pattern: form.body_pattern.trim() || undefined,
      description: form.description.trim() || undefined,
      extract_pattern: form.extract_pattern.trim(),
    };

    if (isEditing && rule) {
      await updateRule.mutateAsync({ ruleId: rule.id, payload });
    } else {
      await createRule.mutateAsync(payload);
    }
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[720px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? "编辑验证码规则" : "新建验证码规则"}</DialogTitle>
          <DialogDescription>
            支持定向 / 通用规则、AND / OR 条件组合与正则提取。
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="rule-name">规则名称</Label>
              <Input id="rule-name" value={form.name} onChange={(e) => updateField("name", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="rule-priority">优先级</Label>
              <Input id="rule-priority" type="number" value={form.priority} onChange={(e) => updateField("priority", Number(e.target.value))} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>规则类型</Label>
              <Select value={form.scope_type} onValueChange={(value: "targeted" | "global") => updateField("scope_type", value)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="targeted">定向规则</SelectItem>
                  <SelectItem value="global">通用规则</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>条件关系</Label>
              <Select value={form.match_mode} onValueChange={(value: "and" | "or") => updateField("match_mode", value)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="and">AND</SelectItem>
                  <SelectItem value="or">OR</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>开关</Label>
              <div className="flex h-10 items-center gap-3 rounded-md border px-3">
                <Checkbox checked={form.enabled} onCheckedChange={(checked) => updateField("enabled", checked === true)} />
                <span className="text-sm">启用</span>
                <Checkbox checked={form.is_regex} onCheckedChange={(checked) => updateField("is_regex", checked === true)} />
                <span className="text-sm">正则</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="sender-pattern">发件人条件</Label>
            <Input id="sender-pattern" value={form.sender_pattern} onChange={(e) => updateField("sender_pattern", e.target.value)} placeholder="例如 microsoft 或 noreply@github.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="subject-pattern">主题条件</Label>
            <Input id="subject-pattern" value={form.subject_pattern} onChange={(e) => updateField("subject_pattern", e.target.value)} placeholder="例如 verification|security code" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="body-pattern">内容条件</Label>
            <Textarea id="body-pattern" value={form.body_pattern} onChange={(e) => updateField("body_pattern", e.target.value)} rows={3} placeholder="例如 OTP|验证码|security code" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="extract-pattern">提取规则</Label>
            <Input id="extract-pattern" value={form.extract_pattern} onChange={(e) => updateField("extract_pattern", e.target.value)} placeholder="例如 (\\d{6})" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rule-description">描述</Label>
            <Textarea id="rule-description" value={form.description} onChange={(e) => updateField("description", e.target.value)} rows={2} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSubmit} disabled={submitting || !form.name.trim() || !form.extract_pattern.trim()}>
            {submitting ? "保存中..." : isEditing ? "保存修改" : "创建规则"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
