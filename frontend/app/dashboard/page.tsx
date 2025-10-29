"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { SystemStats } from "@/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiClient.getSystemStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-gray-900">仪表板</h1>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="总账户数"
          value={stats?.total_accounts || 0}
          icon="👤"
          color="blue"
        />
        <StatCard
          title="活跃账户"
          value={stats?.active_accounts || 0}
          icon="✅"
          color="green"
        />
        <StatCard
          title="总邮件数"
          value={stats?.total_emails || 0}
          icon="📧"
          color="purple"
        />
        <StatCard
          title="未读邮件"
          value={stats?.unread_emails || 0}
          icon="📬"
          color="orange"
        />
      </div>

      <div className="mt-8 rounded-lg bg-white p-6 shadow-md">
        <h2 className="mb-4 text-xl font-semibold">快速操作</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <QuickActionCard
            title="添加账户"
            description="添加新的Outlook账户"
            href="/dashboard/accounts"
            icon="➕"
          />
          <QuickActionCard
            title="查看邮件"
            description="浏览所有邮件"
            href="/dashboard/emails"
            icon="📧"
          />
          <QuickActionCard
            title="系统设置"
            description="配置系统参数"
            href="/dashboard/settings"
            icon="⚙️"
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: number;
  icon: string;
  color: string;
}) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    orange: "bg-orange-50 text-orange-600",
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold">{value}</p>
        </div>
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-full text-2xl ${
            colorClasses[color as keyof typeof colorClasses]
          }`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function QuickActionCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
}) {
  return (
    <a
      href={href}
      className="block rounded-lg border border-gray-200 p-4 transition-shadow hover:shadow-md"
    >
      <div className="mb-2 text-2xl">{icon}</div>
      <h3 className="mb-1 font-semibold">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </a>
  );
}

