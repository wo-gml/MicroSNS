import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // 브라우저의 /api/* 요청을 FastAPI로 전달합니다. 같은 출처가 되어 CORS 설정이 필요 없습니다.
  rewrites() {
    const apiUrl = process.env.API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
