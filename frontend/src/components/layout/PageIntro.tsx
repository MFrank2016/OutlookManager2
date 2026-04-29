import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageIntroProps {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function PageIntro({
  title,
  description,
  actions,
  children,
  className,
}: PageIntroProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border/70 bg-[color:var(--surface-1)]/80 p-3 backdrop-blur-sm md:p-4",
        className
      )}
    >
      {(title || description || actions) && (
        <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            {title ? <h2 className="text-sm font-medium text-foreground">{title}</h2> : null}
            {description ? <p className="text-xs text-[color:var(--text-soft)]">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      )}

      {children}
    </section>
  );
}
