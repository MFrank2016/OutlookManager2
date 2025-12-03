"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useCreateConfig, useUpdateConfig } from "@/hooks/useAdmin";
import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { ConfigItem } from "@/types";

const configSchema = z.object({
  key: z.string().min(1, "配置键必填"),
  value: z.string().min(1, "配置值必填"),
  description: z.string().optional(),
});

interface ConfigDialogProps {
  config?: ConfigItem;
  trigger?: React.ReactNode;
}

export function ConfigDialog({ config, trigger }: ConfigDialogProps) {
  const [open, setOpen] = useState(false);
  const createConfig = useCreateConfig();
  const updateConfig = useUpdateConfig();
  const isEdit = !!config;

  const form = useForm<z.infer<typeof configSchema>>({
    resolver: zodResolver(configSchema),
    defaultValues: {
      key: config?.key || "",
      value: config?.value || "",
      description: config?.description || "",
    },
  });

  useEffect(() => {
    if (open && config) {
      form.reset({
        key: config.key,
        value: config.value,
        description: config.description || "",
      });
    } else if (open && !config) {
      form.reset({
        key: "",
        value: "",
        description: "",
      });
    }
  }, [open, config, form]);

  function onSubmit(values: z.infer<typeof configSchema>) {
    if (isEdit && config) {
      updateConfig.mutate(
        {
          key: config.key,
          value: values.value,
          description: values.description,
        },
        {
          onSuccess: () => {
            setOpen(false);
            form.reset();
          },
        }
      );
    } else {
      createConfig.mutate(
        {
          key: values.key,
          value: values.value,
          description: values.description,
        },
        {
          onSuccess: () => {
            setOpen(false);
            form.reset();
          },
        }
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" /> 新增配置
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "编辑配置" : "新增配置"}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>配置键</FormLabel>
                  <FormControl>
                    <Input placeholder="config_key" {...field} disabled={isEdit} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="value"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>配置值</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="配置值"
                      {...field}
                      className="min-h-[100px]"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>描述（可选）</FormLabel>
                  <FormControl>
                    <Input placeholder="配置描述" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              className="w-full"
              disabled={createConfig.isPending || updateConfig.isPending}
            >
              {createConfig.isPending || updateConfig.isPending
                ? "保存中..."
                : isEdit
                ? "更新配置"
                : "创建配置"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

