"use client"

import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react"
import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { useEffect, useState } from "react"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // 避免 hydration mismatch - 只在客户端挂载后渲染
  useEffect(() => {
    setMounted(true)
  }, [])

  // 服务器端不渲染，避免 hydration mismatch
  if (!mounted) {
    return null
  }

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      toastOptions={{
        // 点击 toast 后立即关闭
        onClick: (toast) => {
          toast.dismiss();
        },
        // 显示关闭按钮
        closeButton: true,
        // 设置默认样式，让点击区域更明显
        classNames: {
          toast: "cursor-pointer",
        },
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }
