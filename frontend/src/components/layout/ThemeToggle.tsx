"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getNextTheme, getThemeToggleLabel } from "@/lib/theme";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  compact?: boolean;
  className?: string;
}

export function ThemeToggle({ compact = false, className }: ThemeToggleProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const nextThemeLabel = mounted ? getThemeToggleLabel(resolvedTheme) : "切换主题";

  const handleToggleTheme = () => {
    if (!mounted) {
      return;
    }
    setTheme(getNextTheme(resolvedTheme));
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
      title={nextThemeLabel}
      aria-label={nextThemeLabel}
      disabled={!mounted}
    >
      <Sun className="h-4 w-4 transition-all motion-reduce:transition-none dark:scale-75 dark:rotate-90 dark:opacity-0 motion-reduce:dark:scale-100 motion-reduce:dark:rotate-0" />
      <Moon className="absolute h-4 w-4 scale-75 -rotate-90 opacity-0 transition-all motion-reduce:transition-none dark:scale-100 dark:rotate-0 dark:opacity-100 motion-reduce:scale-100 motion-reduce:rotate-0" />
      {!compact && <span className="text-xs font-medium">主题</span>}
    </Button>
  );
}
