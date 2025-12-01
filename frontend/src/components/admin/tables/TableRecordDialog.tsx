"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTableRecord, useUpdateTableRecord } from "@/hooks/useAdmin";
import { Plus, Edit, Save } from "lucide-react";

interface TableRecordDialogProps {
  tableName: string;
  columns: string[];
  record?: any;
  trigger?: React.ReactNode;
}

export function TableRecordDialog({ tableName, columns, record, trigger }: TableRecordDialogProps) {
  const [open, setOpen] = useState(false);
  const createRecord = useCreateTableRecord();
  const updateRecord = useUpdateTableRecord();
  const isEdit = !!record;

  // We use a simple state for form data since columns are dynamic
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    if (open) {
        if (record) {
            setFormData({ ...record });
        } else {
            const initialData: any = {};
            columns.forEach(col => {
                if (col !== 'id' && col !== 'created_at' && col !== 'updated_at') {
                    initialData[col] = "";
                }
            });
            setFormData(initialData);
        }
    }
  }, [open, record, columns]);

  const handleChange = (col: string, value: string) => {
      setFormData(prev => ({ ...prev, [col]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      
      // Filter out read-only columns for create/update
      const dataToSubmit = { ...formData };
      delete dataToSubmit.id;
      delete dataToSubmit.created_at;
      delete dataToSubmit.updated_at;

      if (isEdit && record) {
          updateRecord.mutate({ 
              tableName, 
              recordId: record.id, 
              data: dataToSubmit 
          }, {
              onSuccess: () => setOpen(false)
          });
      } else {
          createRecord.mutate({ 
              tableName, 
              data: dataToSubmit 
          }, {
              onSuccess: () => setOpen(false)
          });
      }
  };

  const isPending = createRecord.isPending || updateRecord.isPending;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" /> 添加记录
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "编辑记录" : "添加新记录"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
            {columns.map(col => {
                // Skip ID and timestamps for form input usually
                // But for editing, maybe show them as disabled?
                if (col === 'id' || col === 'created_at' || col === 'updated_at') {
                    if (!isEdit) return null; // Don't show for create
                    return (
                        <div key={col} className="grid gap-2">
                            <Label htmlFor={col} className="capitalize">{col}</Label>
                            <Input id={col} value={formData[col] || ''} disabled className="bg-slate-50" />
                        </div>
                    );
                }
                
                return (
                    <div key={col} className="grid gap-2">
                        <Label htmlFor={col} className="capitalize">{col}</Label>
                        <Input 
                            id={col} 
                            value={formData[col] || ''} 
                            onChange={(e) => handleChange(col, e.target.value)}
                        />
                    </div>
                );
            })}
            <DialogFooter>
                <Button type="submit" disabled={isPending}>
                    {isPending ? "保存中..." : "保存记录"}
                </Button>
            </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

