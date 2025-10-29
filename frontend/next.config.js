/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // 环境变量
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // 图片配置
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },
  
  // 编译配置
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Server Actions 在 Next.js 14 中已默认启用
  
  // 输出配置
  output: 'standalone',
  
  // 重定向配置 - 已在页面中处理，不需要自动重定向
  async redirects() {
    return [];
  },
};

module.exports = nextConfig;

