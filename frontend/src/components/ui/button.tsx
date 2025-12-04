import * as React from "react"
import { useRef, useCallback, useMemo } from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost:
          "hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        sm: "h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5",
        lg: "h-10 rounded-md px-6 has-[>svg]:px-4",
        icon: "size-9",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps extends React.ComponentProps<"button">, VariantProps<typeof buttonVariants> {
  /**
   * 是否作为子组件（用于 Radix UI Slot）
   */
  asChild?: boolean
  /**
   * 是否启用节流（默认 false，需显式启用）
   * 适用于需要防止重复点击的操作按钮
   */
  throttle?: boolean
  /**
   * 节流延迟时间（毫秒），默认 300ms
   * 仅在 throttle={true} 时生效
   * 注意：type="submit" 的按钮不会应用节流，避免阻止表单提交
   */
  throttleMs?: number
}

function Button({
  className,
  variant,
  size,
  asChild = false,
  throttle = false,
  throttleMs = 300,
  onClick,
  type,
  disabled,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button"
  const lastRunRef = useRef<number>(0)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const onClickRef = useRef(onClick)

  // 保持 onClick 引用最新
  React.useEffect(() => {
    onClickRef.current = onClick
  }, [onClick])

  // 创建节流函数
  const throttledOnClick = useMemo(() => {
    if (!throttle || !onClick) {
      return onClick
    }

    return (e: React.MouseEvent<HTMLButtonElement>) => {
      const now = Date.now()
      const timeSinceLastRun = now - lastRunRef.current

      if (timeSinceLastRun >= throttleMs) {
        // 可以立即执行
        lastRunRef.current = now
        if (onClickRef.current) {
          onClickRef.current(e)
        }
      } else {
        // 需要等待，清除之前的定时器
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }

        // 设置新的定时器，在剩余时间后执行
        const remainingTime = throttleMs - timeSinceLastRun
        timeoutRef.current = setTimeout(() => {
          lastRunRef.current = Date.now()
          if (onClickRef.current) {
            onClickRef.current(e)
          }
          timeoutRef.current = null
        }, remainingTime)
      }
    }
  }, [throttle, throttleMs, onClick])

  // 清理定时器
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // 表单提交按钮不应该应用节流，避免阻止表单提交
  // 禁用状态的按钮也不需要节流
  const shouldThrottle = throttle && type !== "submit" && !disabled && onClick
  const handleClick = shouldThrottle ? throttledOnClick : onClick

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      onClick={handleClick}
      type={type}
      disabled={disabled}
      {...props}
    />
  )
}

export { Button, buttonVariants }
