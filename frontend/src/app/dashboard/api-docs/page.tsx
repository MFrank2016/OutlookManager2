"use client";

export default function ApiDocsPage() {
  return (
    <div className="page-enter flex h-full w-full flex-col">
      <h1 className="mb-4 text-2xl font-bold tracking-tight">API Documentation</h1>
      <div className="panel-surface flex-1 overflow-hidden rounded-md border-0 p-1">
        {/* Use the backend's /docs URL which serves Swagger UI */}
        <iframe 
          src="/docs" 
          className="h-full w-full rounded-sm border-none bg-white"
          title="API Documentation"
        />
      </div>
    </div>
  );
}
