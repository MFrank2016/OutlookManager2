"use client";

import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

interface ThemeToggleProps {
  compact?: boolean;
  className?: string;
}

export function ThemeToggle({ compact = false, className }: ThemeToggleProps) {
  const { setTheme } = useTheme();

  const handleToggleTheme = () => {
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <Button
      variant="ghost"
      size={compact ? "icon" : "sm"}
      onClick={handleToggleTheme}
      className={cn(
        "interactive-lift relative border border-border/70 bg-[color:var(--surface-2)]/75 text-[color:var(--text-soft)] hover:text-foreground",
        compact ? "h-9 w-9" : "h-9 px-3",
        className
      )}
      title="切换明亮/暗黑模式"
      aria-label="切换明亮或暗黑模式"
    >
      <Sun className="h-4 w-4 transition-all dark:scale-75 dark:rotate-90 dark:opacity-0" />
      <Moon className="absolute h-4 w-4 scale-75 -rotate-90 opacity-0 transition-all dark:scale-100 dark:rotate-0 dark:opacity-100" />
      {!compact && <span className="text-xs font-medium">主题</span>}
    </Button>
  );
}
