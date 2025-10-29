"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 检查是否已登录
    const token = apiClient.getToken();
    if (token) {
      // 验证 token 是否有效
      apiClient.verifyToken().then((valid) => {
        if (valid) {
          router.push("/dashboard");
        } else {
          router.push("/login");
        }
      });
    } else {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold">加载中...</h1>
      </div>
    </div>
  );
}

