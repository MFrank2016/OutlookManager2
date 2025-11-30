"use client";

export default function ApiDocsPage() {
  return (
    <div className="h-full w-full flex flex-col">
      <h1 className="text-2xl font-bold tracking-tight mb-4">API Documentation</h1>
      <div className="flex-1 border rounded-md overflow-hidden bg-white">
        {/* Use the backend's /docs URL which serves Swagger UI */}
        <iframe 
          src="/docs" 
          className="w-full h-full border-none"
          title="API Documentation"
        />
      </div>
    </div>
  );
}

