"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const formSchema = z.object({
  username: z.string().min(1, {
    message: "用户名必填",
  }),
  password: z.string().min(1, {
    message: "密码必填",
  }),
});

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    try {
      // 1. Login to get token
      const loginResponse = await api.post("/auth/login", {
        username: values.username,
        password: values.password,
      });
      const token = loginResponse.data.access_token;
      
      // Temporarily set token in localStorage so subsequent request has it (interceptor)
      // although store.login handles it, we need it immediately for the next call if store update is async/batched
      // Actually the interceptor reads from localStorage directly.
      localStorage.setItem("auth_token", token);

      // 2. Fetch user info
      const userResponse = await api.get("/auth/me");
      const user = userResponse.data;

      // 3. Update store
      login(token, user);
      
      toast.success("登录成功");
      router.push("/dashboard");
    } catch (error: unknown) {
      console.error(error);
      const msg =
        error && typeof error === "object" && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "登录失败，请检查您的凭据。")
          : "登录失败，请检查您的凭据。";
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 page-enter">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 top-[-120px] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle,color-mix(in_oklch,var(--brand)_40%,transparent),transparent_68%)] blur-2xl" />
        <div className="absolute -right-16 bottom-[-160px] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle,color-mix(in_oklch,var(--accent)_35%,transparent),transparent_70%)] blur-2xl" />
      </div>

      <Card className="interactive-lift w-full max-w-[380px] border-border/80 bg-[color:var(--surface-1)] py-0 shadow-[0_20px_48px_rgba(5,8,20,0.55)] backdrop-blur-xl">
        <CardHeader>
          <div className="mx-auto mb-1 flex h-10 w-10 items-center justify-center rounded-full border border-border/80 bg-[color:var(--surface-2)]">
            <span className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_12px_color-mix(in_oklch,var(--brand)_70%,transparent)]" />
          </div>
          <CardTitle className="text-center text-2xl tracking-wide">Outlook Manager</CardTitle>
          <p className="text-center text-sm text-muted-foreground">控制台登录</p>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>用户名</FormLabel>
                    <FormControl>
                      <Input placeholder="admin" {...field} />
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
                    <FormLabel>密码</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="******" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                className="w-full bg-primary text-[color:var(--primary-foreground)] transition-transform duration-200 hover:translate-y-[-1px] hover:bg-primary/90"
                disabled={isLoading}
              >
                {isLoading ? "登录中..." : "登录"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
