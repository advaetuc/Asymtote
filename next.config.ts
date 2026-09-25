import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async rewrites() {
    // Focused local development only; Vercel handles production API routing.
    return process.env.NODE_ENV === "development" && !process.env.VERCEL
      ? [{ source: "/api/:path*", destination: "http://127.0.0.1:18000/api/:path*" }]
      : [];
  },
};

export default nextConfig;
