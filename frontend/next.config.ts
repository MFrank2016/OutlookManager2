import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/:path*", // Proxy /api requests to backend root if backend routes are at root
      },
      // Specific backend routes mapping if they are not under /api prefix in backend
      {
        source: "/accounts/:path*",
        destination: "http://127.0.0.1:8000/accounts/:path*",
      },
      {
        source: "/auth/:path*",
        destination: "http://127.0.0.1:8000/auth/:path*",
      },
      {
        source: "/emails/:path*",
        destination: "http://127.0.0.1:8000/emails/:path*",
      },
      {
        source: "/admin/:path*",
        destination: "http://127.0.0.1:8000/admin/:path*",
      },
      {
        source: "/cache/:path*",
        destination: "http://127.0.0.1:8000/cache/:path*",
      },
      {
        source: "/docs",
        destination: "http://127.0.0.1:8000/docs",
      },
      {
        source: "/openapi.json",
        destination: "http://127.0.0.1:8000/openapi.json",
      },
    ];
  },
};

export default nextConfig;
