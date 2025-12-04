import * as React from "react"
import { useRef, useMemo } from "react"

import { cn } from "@/lib/utils"

export interface TextareaProps extends React.ComponentProps<"textarea"> {
  /**
   * 是否启用防抖（默认 false，适用于搜索输入框时可设为 true）
   * 对于表单输入框（如 React Hook Form），请保持为 false
   * 当为 false 时，onChange 会立即触发
   */
  debounce?: boolean
  /**
   * 防抖延迟时间（毫秒），默认 500ms
   * 仅在 debounce={true} 时生效
   */
  debounceMs?: number
}

function Textarea({ 
  className, 
  debounce = false,
  debounceMs = 500,
  onChange,
  value,
  ...props 
}: TextareaProps) {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const onChangeRef = useRef(onChange)
  const isControlled = value !== undefined
  
  // 保持 onChange 引用最新
  React.useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  const debouncedOnChange = useMemo(() => {
    if (!debounce || !onChange) {
      return onChange
    }

    return (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      // 清除之前的定时器
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      // 创建合成事件对象以保持兼容性
      const syntheticEvent = {
        ...e,
        target: e.target,
        currentTarget: e.currentTarget,
      } as React.ChangeEvent<HTMLTextAreaElement>

      // 设置新的定时器
      timeoutRef.current = setTimeout(() => {
        if (onChangeRef.current) {
          onChangeRef.current(syntheticEvent)
        }
        timeoutRef.current = null
      }, debounceMs)
    }
  }, [debounce, debounceMs, onChange])

  // 清理定时器
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // 对于受控组件（如 React Hook Form），不应用防抖
  const handleChange = debounce && !isControlled && onChange 
    ? debouncedOnChange 
    : onChange

  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 flex field-sizing-content min-h-16 w-full rounded-md border bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      onChange={handleChange}
      value={value}
      {...props}
    />
  )
}

export { Textarea }
