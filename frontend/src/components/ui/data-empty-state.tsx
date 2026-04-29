import { type ReactNode } from "react"
import { Inbox } from "lucide-react"

import { cn } from "@/lib/utils"

interface DataEmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
  className?: string
}

export function DataEmptyState({
  title,
  description,
  action,
  icon,
  className,
}: DataEmptyStateProps) {
  return (
    <section
      data-slot="data-empty-state"
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-2xl border border-dashed border-border/80 bg-[color:var(--surface-1)]/70 px-6 py-10 text-center",
        className
      )}
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-border/80 bg-[color:var(--surface-2)] text-[color:var(--text-soft)]">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <h3 className="text-base font-medium text-foreground">{title}</h3>
      {description ? (
        <p className="mt-2 max-w-md text-sm leading-6 text-[color:var(--text-soft)]">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5 flex flex-wrap items-center justify-center gap-2">{action}</div> : null}
    </section>
  )
}
