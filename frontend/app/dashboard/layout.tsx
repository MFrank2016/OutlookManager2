"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState("");

  useEffect(() => {
    // 验证登录状态
    const checkAuth = async () => {
      const token = apiClient.getToken();
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const isValid = await apiClient.verifyToken();
        if (!isValid) {
          router.push("/login");
          return;
        }

        // 获取用户信息
        const profile = await apiClient.getAdminProfile();
        setUsername(profile.username);
      } catch {
        router.push("/login");
        return;
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  const handleLogout = () => {
    apiClient.logout();
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    );
  }

  const navItems = [
    { href: "/dashboard", label: "仪表板", icon: "📊" },
    { href: "/dashboard/accounts", label: "账户管理", icon: "👤" },
    { href: "/dashboard/emails", label: "邮件管理", icon: "📧" },
    { href: "/dashboard/settings", label: "系统设置", icon: "⚙️" },
  ];

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* 侧边栏 */}
      <aside className="w-64 bg-white shadow-md">
        <div className="flex h-16 items-center justify-center border-b px-4">
          <h1 className="text-xl font-bold text-blue-600">OutlookManager</h1>
        </div>

        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                    pathname === item.href
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="absolute bottom-0 w-64 border-t p-4">
          <div className="mb-2 text-sm text-gray-600">
            当前用户: <strong>{username}</strong>
          </div>
          <button
            onClick={handleLogout}
            className="w-full rounded-md bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
          >
            退出登录
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1">
        <div className="mx-auto max-w-7xl p-6">{children}</div>
      </main>
    </div>
  );
}

