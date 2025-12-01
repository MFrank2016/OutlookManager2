"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { useAddAccount } from "@/hooks/useAccounts";
import { useState } from "react";
import { Plus } from "lucide-react";

const formSchema = z.object({
  email: z.string().email(),
  client_id: z.string().min(1, "Client ID 必填"),
  refresh_token: z.string().min(1, "Refresh Token 必填"),
  tags: z.string().optional(), // comma separated
});

export function AddAccountDialog() {
  const [open, setOpen] = useState(false);
  const addAccount = useAddAccount();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      client_id: "",
      refresh_token: "",
      tags: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    const tagsArray = values.tags ? values.tags.split(",").map(t => t.trim()).filter(Boolean) : [];
    addAccount.mutate({
      ...values,
      tags: tagsArray
    }, {
        onSuccess: () => {
            setOpen(false);
            form.reset();
        }
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Plus className="mr-2 h-4 w-4" /> 添加账户</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>添加新账户</DialogTitle>
          <DialogDescription>
            输入 Outlook 账户的 OAuth2 凭据。
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input placeholder="user@outlook.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="client_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Client ID</FormLabel>
                  <FormControl>
                    <Input placeholder="Azure App Client ID" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="refresh_token"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Refresh Token</FormLabel>
                  <FormControl>
                    <Input placeholder="OAuth2 Refresh Token" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="tags"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>标签（逗号分隔）</FormLabel>
                  <FormControl>
                    <Input placeholder="vip, work" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={addAccount.isPending}>
              {addAccount.isPending ? "添加中..." : "添加账户"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

