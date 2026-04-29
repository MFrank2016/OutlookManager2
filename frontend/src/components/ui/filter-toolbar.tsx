import { type ReactNode } from "react"

import { cn } from "@/lib/utils"

interface FilterToolbarProps {
  leading?: ReactNode
  center?: ReactNode
  trailing?: ReactNode
  className?: string
}

export function FilterToolbar({
  leading,
  center,
  trailing,
  className,
}: FilterToolbarProps) {
  return (
    <section
      data-slot="filter-toolbar"
      className={cn("panel-surface space-y-3 p-3 md:p-4", className)}
    >
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start">
        {leading ? (
          <div className="flex min-w-0 flex-1 flex-col gap-3">
            {leading}
          </div>
        ) : null}

        {center ? (
          <div className="flex min-w-0 flex-1 flex-col gap-3">
            {center}
          </div>
        ) : null}

        {trailing ? (
          <div className="flex flex-wrap items-center gap-2 xl:ml-auto xl:justify-end">
            {trailing}
          </div>
        ) : null}
      </div>
    </section>
  )
}
