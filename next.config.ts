import type { NextConfig } from "next";
import { securityHeaders } from "./lib/security";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // npm scripts run from the project root; ignore unrelated ancestor lockfiles.
  turbopack: { root: process.cwd() },
  outputFileTracingRoot: process.cwd(),
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    // Local development/integration only; Vercel owns production API routing.
    return (process.env.NODE_ENV === "development" || process.env.AUGMENTR_LOCAL_API_PROXY === "1") && !process.env.VERCEL
      ? [{ source: "/api/:path*", destination: "http://127.0.0.1:18000/api/:path*" }]
      : [];
  },
};

export default nextConfig;
