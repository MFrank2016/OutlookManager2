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
import { toast as sonnerToast } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // 避免 hydration mismatch - 只在客户端挂载后渲染
  useEffect(() => {
    setMounted(true)
  }, [])

  // 添加点击关闭功能
  useEffect(() => {
    if (!mounted) return

    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      // 检查是否点击了 toast 元素（但不是关闭按钮）
      const toastElement = target.closest('[data-sonner-toast]')
      if (!toastElement) return
      
      // 检查是否点击了关闭按钮或操作按钮
      const closeButton = target.closest('[data-close-button]')
      const actionButton = target.closest('[data-button]')
      
      if (toastElement && !closeButton && !actionButton) {
        // 获取 toast ID（sonner 使用 data-id 属性）
        const toastId = (toastElement as HTMLElement).getAttribute('data-id')
        if (toastId) {
          sonnerToast.dismiss(toastId)
        } else {
          // 如果没有 data-id，尝试通过其他方式关闭
          // 触发关闭按钮的点击事件
          const closeBtn = toastElement.querySelector('[data-close-button]') as HTMLElement
          if (closeBtn) {
            closeBtn.click()
          }
        }
      }
    }

    // 使用捕获阶段确保能捕获到事件
    document.addEventListener('click', handleClick, true)
    return () => {
      document.removeEventListener('click', handleClick, true)
    }
  }, [mounted])

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
