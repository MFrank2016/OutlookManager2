"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageSection } from "@/components/layout/PageSection";

export default function ApiDocsPage() {
  return (
    <div className="page-enter flex h-full min-h-[70dvh] flex-col gap-3 md:gap-4">
      <PageHeader
        title="API 文档"
        description="内嵌 Swagger UI，便于快速查看接口定义与调试参数。"
      />

      <PageSection className="flex-1" contentClassName="h-full min-h-[56dvh]">
        <iframe src="/docs" className="h-full w-full rounded-md border-none bg-white" title="API Documentation" />
      </PageSection>
    </div>
  );
}
