"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
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
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>管理标签 - {accountEmail}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex flex-wrap gap-2 min-h-[80px] p-4 bg-slate-50 rounded-md border border-slate-200">
            {tags.length === 0 ? (
               <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm italic">
                 暂无标签
               </div>
            ) : (
                tags.map(tag => (
                <Badge key={tag} variant="secondary" className="pl-2 pr-1 py-1 flex items-center gap-1">
                    {tag}
                    <button onClick={() => handleRemoveTag(tag)} className="hover:text-red-500 ml-1">
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
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={updateTags.isPending}>
            {updateTags.isPending ? "保存中..." : "保存更改"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

