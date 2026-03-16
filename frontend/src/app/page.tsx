"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, token } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && token) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [isAuthenticated, token, router]);

  return (
    <div className="flex h-screen items-center justify-center page-enter">
      <div className="h-9 w-9 animate-spin rounded-full border-2 border-muted border-t-primary"></div>
    </div>
  );
}
