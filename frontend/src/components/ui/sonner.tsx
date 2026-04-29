"use client";

import { useEffect, useState } from "react";
import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { useTheme } from "next-themes";
import { toast as sonnerToast, Toaster as Sonner, type ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) {
      return;
    }

    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const toastElement = target.closest("[data-sonner-toast]");
      if (!toastElement) {
        return;
      }

      const closeButton = target.closest("[data-close-button]");
      const actionButton = target.closest("[data-button]");
      const interactiveElement = target.closest(
        "a,button,input,textarea,select,label,[role='button'],[data-sonner-no-dismiss]"
      );

      if (!closeButton && !actionButton && !interactiveElement) {
        const toastId = toastElement.getAttribute("data-id");
        if (toastId) {
          sonnerToast.dismiss(toastId);
          return;
        }

        const fallbackCloseButton = toastElement.querySelector("[data-close-button]") as HTMLElement | null;
        fallbackCloseButton?.click();
      }
    };

    document.addEventListener("click", handleClick, true);
    return () => {
      document.removeEventListener("click", handleClick, true);
    };
  }, [mounted]);

  if (!mounted) {
    return null;
  }

  return (
    <Sonner
      theme={(resolvedTheme ?? "system") as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      toastOptions={{
        closeButton: true,
        classNames: {
          toast:
            "cursor-pointer border border-[var(--normal-border)] bg-[var(--normal-bg)] text-[var(--normal-text)] shadow-[var(--shadow-soft)]",
          title: "text-[color:var(--foreground)]",
          description: "text-[color:var(--text-soft)]",
          actionButton:
            "border border-border bg-[color:var(--surface-2)] text-[color:var(--foreground)] hover:bg-[color:var(--surface-3)]",
          cancelButton:
            "border border-border bg-transparent text-[color:var(--text-soft)] hover:bg-[color:var(--surface-2)]",
          closeButton:
            "border border-transparent bg-transparent text-[color:var(--text-faint)] hover:border-border hover:bg-[color:var(--surface-2)] hover:text-[color:var(--foreground)]",
          success:
            "bg-[var(--success-bg)] text-[var(--success-text)] border-[var(--success-border)]",
          warning:
            "bg-[var(--warning-bg)] text-[var(--warning-text)] border-[var(--warning-border)]",
          error: "bg-[var(--error-bg)] text-[var(--error-text)] border-[var(--error-border)]",
          info: "bg-[var(--info-bg)] text-[var(--info-text)] border-[var(--info-border)]",
        },
      }}
      style={
        {
          "--normal-bg": "var(--panel)",
          "--normal-text": "var(--foreground)",
          "--normal-border": "color-mix(in oklch, var(--border) 84%, transparent)",
          "--success-bg": "color-mix(in oklch, var(--ok) 14%, var(--panel) 86%)",
          "--success-text": "var(--foreground)",
          "--success-border": "color-mix(in oklch, var(--ok) 42%, var(--border) 58%)",
          "--warning-bg": "color-mix(in oklch, var(--warn) 14%, var(--panel) 86%)",
          "--warning-text": "var(--foreground)",
          "--warning-border": "color-mix(in oklch, var(--warn) 42%, var(--border) 58%)",
          "--error-bg": "color-mix(in oklch, var(--danger) 14%, var(--panel) 86%)",
          "--error-text": "var(--foreground)",
          "--error-border": "color-mix(in oklch, var(--danger) 48%, var(--border) 52%)",
          "--info-bg": "color-mix(in oklch, var(--brand) 12%, var(--panel) 88%)",
          "--info-text": "var(--foreground)",
          "--info-border": "color-mix(in oklch, var(--brand) 38%, var(--border) 62%)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
