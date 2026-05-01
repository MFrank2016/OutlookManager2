"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageSection } from "@/components/layout/PageSection";
import { Badge } from "@/components/ui/badge";

export default function ApiDocsPage() {
  return (
    <div className="page-enter flex h-full min-h-[70dvh] flex-col gap-3 md:gap-4">
      <PageHeader
        title="API 文档"
        description="内嵌 Swagger UI，便于快速查看接口定义与调试参数。"
      />

      <PageSection
        title="V2 快速入口"
        description="重点关注 Microsoft Access Layer 新增的 `/api/v2` 能力。"
        contentClassName="flex flex-wrap gap-2"
      >
        <Badge variant="secondary">POST /api/v2/accounts/probe</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/health"}</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/delivery-strategy"}</Badge>
        <Badge variant="secondary">{"GET /api/v2/accounts/{email}/messages"}</Badge>
        <Badge variant="secondary">POST /api/v2/accounts/import?mode=dry_run</Badge>
      </PageSection>

      <PageSection className="flex-1" contentClassName="h-full min-h-[56dvh]">
        <iframe src="/docs" className="h-full w-full rounded-md border-none bg-white" title="API Documentation" />
      </PageSection>
    </div>
  );
}
