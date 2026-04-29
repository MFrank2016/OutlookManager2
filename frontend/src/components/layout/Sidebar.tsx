"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Book,
  LayoutDashboard,
  LogOut,
  Mail,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Share2,
  Shield,
  X,
} from "lucide-react";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/useAuthStore";

interface SidebarProps {
  collapsed: boolean;
  toggleCollapsed: () => void;
  isMobile?: boolean;
  mobileMode?: boolean;
  onNavigate?: () => void;
}

export function Sidebar({
  collapsed,
  toggleCollapsed,
  isMobile = false,
  mobileMode = false,
  onNavigate,
}: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  const routes = [
    {
      label: "账户管理",
      icon: LayoutDashboard,
      href: "/dashboard",
      active: pathname === "/dashboard" || pathname.startsWith("/dashboard/accounts"),
    },
    {
      label: "邮件",
      icon: Mail,
      href: "/dashboard/emails",
      active: pathname.startsWith("/dashboard/emails"),
    },
    {
      label: "分享管理",
      icon: Share2,
      href: "/dashboard/share",
      active: pathname.startsWith("/dashboard/share"),
    },
    {
      label: "管理面板",
      icon: Settings,
      href: "/dashboard/admin",
      active: pathname.startsWith("/dashboard/admin"),
      adminOnly: true,
    },
    {
      label: "API文档",
      icon: Book,
      href: "/dashboard/api-docs",
      active: pathname.startsWith("/dashboard/api-docs"),
    },
  ];

  const compact = collapsed && !mobileMode && !isMobile;

  const handleNavigate = () => {
    if (onNavigate) {
      onNavigate();
    }
  };

  const handleLogout = () => {
    logout();
    if (onNavigate) {
      onNavigate();
    }
  };

  const activeLinkClass =
    "border border-primary/45 bg-primary/16 text-foreground shadow-[0_8px_24px_rgba(70,130,255,0.18)]";
  const idleLinkClass =
    "border border-transparent text-[color:var(--text-soft)] hover:border-border/80 hover:bg-[color:var(--surface-2)] hover:text-foreground";

  return (
    <div
      className={cn(
        "relative flex h-full flex-col border-r border-border/70 bg-[color:var(--surface-0)] text-foreground backdrop-blur-xl",
        compact ? "w-20" : "w-full"
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,color-mix(in_oklch,var(--brand)_18%,transparent),transparent_42%)]" />

      <div className="relative flex h-16 items-center gap-2 border-b border-border/70 px-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border/70 bg-[color:var(--surface-2)]">
          <Shield className="h-4 w-4 text-primary" />
        </div>

        {!compact && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-wide">OutlookManager2</p>
            <p className="truncate text-[11px] text-[color:var(--text-faint)]">统一管理控制台</p>
          </div>
        )}

        {mobileMode ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNavigate}
            className="ml-auto h-8 w-8 text-[color:var(--text-faint)] hover:bg-[color:var(--surface-2)] hover:text-foreground"
            aria-label="关闭侧边栏"
          >
            <X className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapsed}
            className={cn(
              "h-8 w-8 text-[color:var(--text-faint)] hover:bg-[color:var(--surface-2)] hover:text-foreground",
              compact && "ml-auto"
            )}
            aria-label={compact ? "展开侧边栏" : "收起侧边栏"}
          >
            {compact ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        )}
      </div>

      <ScrollArea className="relative flex-1 py-4">
        <nav className="space-y-1 px-2">
          {routes.map((route) => {
            if (route.adminOnly && user?.role !== "admin") return null;

            return (
              <Link
                key={route.href}
                href={route.href}
                onClick={handleNavigate}
                className={cn(
                  "interactive-lift flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                  route.active ? activeLinkClass : idleLinkClass,
                  compact && "justify-center px-0"
                )}
                title={compact ? route.label : undefined}
              >
                <route.icon className={cn("h-5 w-5", !compact && "mr-3")} />
                {!compact && <span>{route.label}</span>}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>

      <div className="relative border-t border-border/70 p-3">
        <div className={cn("flex items-center", compact ? "flex-col gap-2" : "gap-3")}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-sm font-bold text-[color:var(--primary-foreground)]">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>

          {!compact && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user?.username || "未登录用户"}</p>
              <p className="truncate text-xs text-[color:var(--text-faint)]">
                {user?.role === "admin" ? "管理员" : "普通用户"}
              </p>
            </div>
          )}

          <div className={cn("flex items-center gap-2", compact && "flex-col")}>
            <ThemeToggle compact />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="h-9 w-9 text-[color:var(--text-faint)] hover:bg-red-500/10 hover:text-red-600"
              title="退出登录"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
