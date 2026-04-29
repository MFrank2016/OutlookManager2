import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageSectionProps {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

export function PageSection({
  title,
  description,
  actions,
  children,
  className,
  contentClassName,
}: PageSectionProps) {
  return (
    <section className={cn("panel-surface space-y-4 p-3 md:p-4", className)}>
      {(title || description || actions) && (
        <div className="flex flex-col gap-2 border-b border-border/70 pb-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            {title ? <h2 className="text-lg font-medium text-foreground">{title}</h2> : null}
            {description ? <p className="text-sm text-[color:var(--text-soft)]">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      )}

      <div className={cn("min-w-0", contentClassName)}>{children}</div>
    </section>
  );
}
