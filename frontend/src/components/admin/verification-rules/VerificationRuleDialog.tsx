"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  VerificationRule,
  VerificationRuleExtractor,
  VerificationRuleMatcher,
} from "@/types";
import { useCreateVerificationRule, useUpdateVerificationRule } from "@/hooks/useAdmin";

interface VerificationRuleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule?: VerificationRule | null;
}

interface FormState {
  name: string;
  scope_type: "targeted" | "global";
  priority: number;
  enabled: boolean;
  is_regex: boolean;
  description: string;
  matchers: VerificationRuleMatcher[];
  extractors: VerificationRuleExtractor[];
}

const createMatcher = (
  source_type: VerificationRuleMatcher["source_type"] = "sender",
  keyword = ""
): VerificationRuleMatcher => ({
  source_type,
  keyword,
  sort_order: 1,
});

const createExtractor = (
  source_type: VerificationRuleExtractor["source_type"] = "subject",
  extract_pattern = ""
): VerificationRuleExtractor => ({
  source_type,
  extract_pattern,
  sort_order: 1,
});

const normalizeMatchers = (matchers: VerificationRuleMatcher[]): VerificationRuleMatcher[] =>
  matchers.map((matcher, index) => ({
    ...matcher,
    sort_order: index + 1,
  }));

const normalizeExtractors = (extractors: VerificationRuleExtractor[]): VerificationRuleExtractor[] =>
  extractors.map((extractor, index) => ({
    ...extractor,
    sort_order: index + 1,
  }));

const DEFAULT_FORM: FormState = {
  name: "",
  scope_type: "global",
  priority: 0,
  enabled: true,
  is_regex: true,
  description: "",
  matchers: [createMatcher()],
  extractors: [createExtractor()],
};

const validateForm = (form: FormState): string | null => {
  if (!form.name.trim()) {
    return "规则名称不能为空";
  }
  if (form.matchers.length === 0) {
    return "至少需要 1 条匹配规则";
  }
  const emptyMatcherIndex = form.matchers.findIndex((matcher) => !matcher.keyword.trim());
  if (emptyMatcherIndex >= 0) {
    return `匹配规则 ${emptyMatcherIndex + 1} 的关键词不能为空`;
  }
  if (form.extractors.length === 0) {
    return "至少需要 1 条提取规则";
  }
  const emptyExtractorIndex = form.extractors.findIndex((extractor) => !extractor.extract_pattern.trim());
  if (emptyExtractorIndex >= 0) {
    return `提取规则 ${emptyExtractorIndex + 1} 的正则不能为空`;
  }
  return null;
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
      priority: rule.priority,
      enabled: rule.enabled,
      is_regex: rule.is_regex,
      description: rule.description || "",
      matchers: normalizeMatchers(
        rule.matchers.length > 0
          ? rule.matchers.map((matcher) => ({
              id: matcher.id,
              rule_id: matcher.rule_id,
              source_type: matcher.source_type,
              keyword: matcher.keyword || "",
              sort_order: matcher.sort_order,
              created_at: matcher.created_at,
              updated_at: matcher.updated_at,
            }))
          : [createMatcher()]
      ),
      extractors: normalizeExtractors(
        rule.extractors.length > 0
          ? rule.extractors.map((extractor) => ({
              id: extractor.id,
              rule_id: extractor.rule_id,
              source_type: extractor.source_type,
              extract_pattern: extractor.extract_pattern || "",
              sort_order: extractor.sort_order,
              created_at: extractor.created_at,
              updated_at: extractor.updated_at,
            }))
          : [createExtractor()]
      ),
    };
  }, [rule]);

  const validationError = useMemo(() => validateForm(form), [form]);

  useEffect(() => {
    if (open) {
      setForm(initialForm);
    }
  }, [open, initialForm]);

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateMatcher = (
    index: number,
    key: keyof VerificationRuleMatcher,
    value: VerificationRuleMatcher[keyof VerificationRuleMatcher]
  ) => {
    setForm((prev) => ({
      ...prev,
      matchers: normalizeMatchers(
        prev.matchers.map((matcher, matcherIndex) =>
          matcherIndex === index ? { ...matcher, [key]: value } : matcher
        )
      ),
    }));
  };

  const updateExtractor = (
    index: number,
    key: keyof VerificationRuleExtractor,
    value: VerificationRuleExtractor[keyof VerificationRuleExtractor]
  ) => {
    setForm((prev) => ({
      ...prev,
      extractors: normalizeExtractors(
        prev.extractors.map((extractor, extractorIndex) =>
          extractorIndex === index ? { ...extractor, [key]: value } : extractor
        )
      ),
    }));
  };

  const handleAddMatcher = () => {
    setForm((prev) => ({
      ...prev,
      matchers: normalizeMatchers([...prev.matchers, createMatcher("subject")]),
    }));
  };

  const handleRemoveMatcher = (index: number) => {
    setForm((prev) => ({
      ...prev,
      matchers: normalizeMatchers(prev.matchers.filter((_, matcherIndex) => matcherIndex !== index)),
    }));
  };

  const handleAddExtractor = () => {
    setForm((prev) => ({
      ...prev,
      extractors: normalizeExtractors([...prev.extractors, createExtractor("body")]),
    }));
  };

  const handleRemoveExtractor = (index: number) => {
    setForm((prev) => ({
      ...prev,
      extractors: normalizeExtractors(prev.extractors.filter((_, extractorIndex) => extractorIndex !== index)),
    }));
  };

  const handleSubmit = async () => {
    if (validationError) {
      return;
    }

    const payload = {
      name: form.name.trim(),
      scope_type: form.scope_type,
      match_mode: "or" as const,
      priority: Number(form.priority) || 0,
      enabled: form.enabled,
      is_regex: form.is_regex,
      description: form.description.trim() || undefined,
      matchers: normalizeMatchers(
        form.matchers.map((matcher) => ({
          ...matcher,
          keyword: matcher.keyword.trim(),
        }))
      ),
      extractors: normalizeExtractors(
        form.extractors.map((extractor) => ({
          ...extractor,
          extract_pattern: extractor.extract_pattern.trim(),
        }))
      ),
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
      <DialogContent className="sm:max-w-[820px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "编辑验证码规则" : "新建验证码规则"}</DialogTitle>
          <DialogDescription>
            配置任意 matcher 命中后，按 extractor 顺序提取验证码。
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-5 py-2">
          <section className="grid gap-4 rounded-xl border border-border/70 p-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="rule-name">规则名称</Label>
                <Input
                  id="rule-name"
                  value={form.name}
                  onChange={(event) => updateField("name", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-priority">优先级</Label>
                <Input
                  id="rule-priority"
                  type="number"
                  value={form.priority}
                  onChange={(event) => updateField("priority", Number(event.target.value))}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>规则范围</Label>
                <Select
                  value={form.scope_type}
                  onValueChange={(value: "targeted" | "global") => updateField("scope_type", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="targeted">定向规则</SelectItem>
                    <SelectItem value="global">通用规则</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>开关</Label>
                <div className="flex h-10 items-center gap-6 rounded-md border px-3 text-sm">
                  <label className="flex items-center gap-2">
                    <Checkbox
                      checked={form.enabled}
                      onCheckedChange={(checked) => updateField("enabled", checked === true)}
                    />
                    <span>启用</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox
                      checked={form.is_regex}
                      onCheckedChange={(checked) => updateField("is_regex", checked === true)}
                    />
                    <span>正则匹配</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="rule-description">描述</Label>
              <Textarea
                id="rule-description"
                value={form.description}
                onChange={(event) => updateField("description", event.target.value)}
                rows={2}
              />
            </div>
          </section>

          <section className="space-y-3 rounded-xl border border-border/70 p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="font-medium">匹配规则列表</div>
                <div className="text-sm text-muted-foreground">任意一条命中即可进入提取</div>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleAddMatcher}>
                <Plus className="mr-2 h-4 w-4" />
                新增匹配规则
              </Button>
            </div>
            <div className="space-y-3">
              {form.matchers.map((matcher, index) => (
                <div key={`${matcher.id ?? "matcher"}-${index}`} className="grid gap-3 rounded-xl border border-border/70 p-3 md:grid-cols-[180px_minmax(0,1fr)_auto]">
                  <div className="space-y-2">
                    <Label>来源 #{index + 1}</Label>
                    <Select
                      value={matcher.source_type}
                      onValueChange={(value: VerificationRuleMatcher["source_type"]) => updateMatcher(index, "source_type", value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sender">发件人</SelectItem>
                        <SelectItem value="subject">主题</SelectItem>
                        <SelectItem value="body">内容</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>关键词</Label>
                    <Input
                      value={matcher.keyword}
                      onChange={(event) => updateMatcher(index, "keyword", event.target.value)}
                      placeholder="例如 github、security code、temporary code"
                    />
                  </div>
                  <div className="flex items-end justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveMatcher(index)}
                      disabled={form.matchers.length === 1}
                      title="删除匹配规则"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-3 rounded-xl border border-border/70 p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="font-medium">提取规则列表</div>
                <div className="text-sm text-muted-foreground">按顺序依次提取，命中即停止</div>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleAddExtractor}>
                <Plus className="mr-2 h-4 w-4" />
                新增提取规则
              </Button>
            </div>
            <div className="space-y-3">
              {form.extractors.map((extractor, index) => (
                <div key={`${extractor.id ?? "extractor"}-${index}`} className="grid gap-3 rounded-xl border border-border/70 p-3 md:grid-cols-[180px_minmax(0,1fr)_auto]">
                  <div className="space-y-2">
                    <Label>来源 #{index + 1}</Label>
                    <Select
                      value={extractor.source_type}
                      onValueChange={(value: VerificationRuleExtractor["source_type"]) => updateExtractor(index, "source_type", value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="subject">主题</SelectItem>
                        <SelectItem value="body">内容</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>提取正则</Label>
                    <Input
                      value={extractor.extract_pattern}
                      onChange={(event) => updateExtractor(index, "extract_pattern", event.target.value)}
                      placeholder="例如 (\\d{6})"
                    />
                  </div>
                  <div className="flex items-end justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveExtractor(index)}
                      disabled={form.extractors.length === 1}
                      title="删除提取规则"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {validationError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
              {validationError}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || !!validationError}>
            {submitting ? "保存中..." : isEditing ? "保存修改" : "创建规则"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
