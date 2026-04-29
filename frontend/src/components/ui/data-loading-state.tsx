import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

interface DataLoadingStateProps {
  title?: string
  description?: string
  rows?: number
  className?: string
}

export function DataLoadingState({
  title = "正在加载数据",
  description = "请稍候，数据工作区正在准备中。",
  rows = 3,
  className,
}: DataLoadingStateProps) {
  return (
    <section
      data-slot="data-loading-state"
      className={cn("panel-surface space-y-4 p-4 md:p-5", className)}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border/80 bg-[color:var(--surface-2)] text-primary">
          <Loader2 className="h-4 w-4 animate-spin" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="text-sm text-[color:var(--text-soft)]">{description}</p>
        </div>
      </div>

      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, index) => (
          <div
            key={index}
            className="animate-pulse rounded-xl border border-border/70 bg-[color:var(--surface-1)]/75 p-3"
          >
            <div className="h-4 w-1/3 rounded-full bg-[color:var(--surface-3)]/80" />
            <div className="mt-3 h-3 w-full rounded-full bg-[color:var(--surface-2)]/85" />
            <div className="mt-2 h-3 w-5/6 rounded-full bg-[color:var(--surface-2)]/75" />
          </div>
        ))}
      </div>
    </section>
  )
}
