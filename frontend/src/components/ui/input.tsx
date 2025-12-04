import * as React from "react"
import { useRef, useCallback, useMemo } from "react"

import { cn } from "@/lib/utils"

export interface InputProps extends React.ComponentProps<"input"> {
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

function Input({ 
  className, 
  type, 
  debounce = false,
  debounceMs = 500,
  onChange,
  value,
  ...props 
}: InputProps) {
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

    return (e: React.ChangeEvent<HTMLInputElement>) => {
      // 对于受控组件，立即更新值（通过原生 input 的行为）
      // 但延迟调用 onChange 回调
      
      // 清除之前的定时器
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      // 创建合成事件对象以保持兼容性
      const syntheticEvent = {
        ...e,
        target: e.target,
        currentTarget: e.currentTarget,
      } as React.ChangeEvent<HTMLInputElement>

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

  // 对于受控组件（如 React Hook Form），即使 debounce 为 true，也不应该延迟更新
  // 因为这会干扰表单的状态同步和验证
  // 所以我们只在非受控组件上应用防抖，或者提供一个内部状态
  const handleChange = debounce && !isControlled && onChange 
    ? debouncedOnChange 
    : onChange

  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
        className
      )}
      onChange={handleChange}
      value={value}
      {...props}
    />
  )
}

export { Input }
