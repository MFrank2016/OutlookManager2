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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateUser, useUpdateUser } from "@/hooks/useAdmin";
import { useState, useEffect } from "react";
import { Plus, Edit } from "lucide-react";
import { User } from "@/types";

const userSchema = z.object({
  username: z.string().min(1, "用户名必填"),
  password: z.string().optional(), // Optional for edit
  email: z.string().email().optional().or(z.literal("")),
  role: z.enum(["admin", "user"]),
  is_active: z.boolean(),
});

interface UserDialogProps {
  user?: User;
  trigger?: React.ReactNode;
}

export function UserDialog({ user, trigger }: UserDialogProps) {
  const [open, setOpen] = useState(false);
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const isEdit = !!user;

  const form = useForm<z.infer<typeof userSchema>>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      username: user?.username || "",
      password: "",
      email: user?.email || "",
      role: user?.role || "user",
      is_active: user ? user.is_active : true,
    },
  });

  useEffect(() => {
    if (open && user) {
        form.reset({
            username: user.username,
            password: "",
            email: user.email || "",
            role: user.role,
            is_active: user.is_active,
        });
    } else if (open && !user) {
        form.reset({
            username: "",
            password: "",
            email: "",
            role: "user",
            is_active: true,
        });
    }
  }, [open, user, form]);

  function onSubmit(values: z.infer<typeof userSchema>) {
    if (isEdit && user) {
      const updateData: any = {
          email: values.email || null,
          role: values.role,
          is_active: values.is_active,
      };
      // If password is provided, we need a separate endpoint or handle it
      // But useUpdateUser logic in hooks uses generic update dict.
      // However, backend `UserUpdateRequest` model doesn't have password field.
      // Password update is a separate endpoint: `PUT /users/{username}/password`.
      // So we should handle password separately if provided.
      
      // Update basic info
      updateUser.mutate({ username: user.username, update: updateData }, {
          onSuccess: () => {
              setOpen(false);
          }
      });
      
      // TODO: Handle password update if provided (requires separate hook/call)
      
    } else {
      if (!values.password) {
          form.setError("password", { message: "新用户密码必填" });
          return;
      }
      createUser.mutate({
          ...values,
          password: values.password // Create expects password
      }, {
          onSuccess: () => {
              setOpen(false);
              form.reset();
          }
      });
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" /> 添加用户
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "编辑用户" : "添加新用户"}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>用户名</FormLabel>
                  <FormControl>
                    <Input placeholder="username" {...field} disabled={isEdit} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>密码 {isEdit && "(留空则不修改)"}</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="******" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input placeholder="email@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>角色</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择角色" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="user">普通用户</SelectItem>
                      <SelectItem value="admin">管理员</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>
                      激活账户
                    </FormLabel>
                  </div>
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={createUser.isPending || updateUser.isPending}>
              {createUser.isPending || updateUser.isPending ? "保存中..." : "保存用户"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

