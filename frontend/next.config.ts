import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // 注意：开发模式指示器只在开发环境中显示
  // 生产模式（npm run start）不会显示调试悬浮球
  
  // API代理配置：将 /api/* 请求代理到后端服务器
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:38000/:path*',
      },
    ];
  },
  
  // 确保代理正确处理重定向
  async headers() {
    return [];
  },
};

export default nextConfig;
