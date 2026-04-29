import { type ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface SelectionBarProps {
  selectedCount: number
  itemLabel?: string
  primaryActions?: ReactNode
  secondaryActions?: ReactNode
  onClear?: () => void
  clearLabel?: string
  className?: string
}

export function SelectionBar({
  selectedCount,
  itemLabel = "项",
  primaryActions,
  secondaryActions,
  onClear,
  clearLabel = "清空选择",
  className,
}: SelectionBarProps) {
  return (
    <section
      data-slot="selection-bar"
      className={cn(
        "panel-surface flex flex-col gap-3 border-primary/20 bg-[color:color-mix(in_oklch,var(--brand)_8%,var(--panel)_92%)] p-3 md:flex-row md:items-center md:justify-between",
        className
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary" className="rounded-full px-2.5 py-0.5">
          已选 {selectedCount} {itemLabel}
        </Badge>
        <p className="text-sm text-[color:var(--text-soft)]">
          对当前选中的记录执行批量操作。
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 md:justify-end">
        {primaryActions}
        {secondaryActions}
        {onClear ? (
          <Button variant="ghost" size="sm" onClick={onClear}>
            {clearLabel}
          </Button>
        ) : null}
      </div>
    </section>
  )
}
