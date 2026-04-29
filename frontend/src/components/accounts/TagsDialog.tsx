"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { X, Plus } from "lucide-react";
import { useUpdateTags } from "@/hooks/useAccounts";

interface TagsDialogProps {
  accountEmail: string | null;
  initialTags: string[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TagsDialog({ accountEmail, initialTags, open, onOpenChange }: TagsDialogProps) {
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const updateTags = useUpdateTags();

  useEffect(() => {
    if (open) {
      setTags([...initialTags]);
    }
  }, [open, initialTags]);

  const handleAddTag = () => {
    const tag = newTag.trim();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSave = () => {
    if (accountEmail) {
      updateTags.mutate({ email_id: accountEmail, tags }, {
        onSuccess: () => onOpenChange(false)
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>管理标签 - {accountEmail}</DialogTitle>
          <DialogDescription>
            为当前账户补充业务标签，便于后续筛选、分享与批量处理。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex min-h-[96px] flex-wrap gap-2 rounded-xl border border-border/70 bg-[color:var(--surface-1)]/80 p-4">
            {tags.length === 0 ? (
               <div className="flex h-full w-full items-center justify-center text-sm italic text-[color:var(--text-faint)]">
                 暂无标签
               </div>
            ) : (
                tags.map(tag => (
                <Badge key={tag} variant="secondary" className="flex items-center gap-1 pl-2 pr-1 py-1">
                    {tag}
                    <button onClick={() => handleRemoveTag(tag)} className="ml-1 rounded-full p-0.5 hover:text-red-500">
                    <X className="h-3 w-3" />
                    </button>
                </Badge>
                ))
            )}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="添加新标签..."
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
            />
            <Button onClick={handleAddTag} size="icon">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={updateTags.isPending}>
            {updateTags.isPending ? "保存中..." : "保存更改"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
