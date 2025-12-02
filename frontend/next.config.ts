import type { NextConfig } from "next";

// 获取后端 API 地址（Docker 环境中使用服务名，本地开发使用 localhost）
const getBackendUrl = () => {
  // 在 Docker 环境中，使用服务名；在本地开发中，使用 localhost
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL;
  }
  // Docker Compose 网络中使用服务名，本地开发使用 localhost
  return process.env.NODE_ENV === "production" 
    ? "http://outlook-email-api:8000" 
    : "http://127.0.0.1:8000";
};

const backendUrl = getBackendUrl();

const nextConfig: NextConfig = {
  // 启用 standalone 输出模式，用于 Docker 部署
  output: "standalone",
  
  // 禁用 React Strict Mode 以避免开发模式下的双重渲染
  // React Strict Mode 会导致 useEffect 被调用两次，创建多个 interval
  reactStrictMode: false,
  
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`, // Proxy /api requests to backend
      },
      // Specific backend routes mapping
      {
        source: "/accounts/:path*",
        destination: `${backendUrl}/accounts/:path*`,
      },
      {
        source: "/auth/:path*",
        destination: `${backendUrl}/auth/:path*`,
      },
      {
        source: "/emails/:path*",
        destination: `${backendUrl}/emails/:path*`,
      },
      {
        source: "/admin/:path*",
        destination: `${backendUrl}/admin/:path*`,
      },
      {
        source: "/cache/:path*",
        destination: `${backendUrl}/cache/:path*`,
      },
      {
        source: "/share/:path*",
        destination: `${backendUrl}/share/:path*`,
      },
      {
        source: "/docs",
        destination: `${backendUrl}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${backendUrl}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
