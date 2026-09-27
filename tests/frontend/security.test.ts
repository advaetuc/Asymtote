import { afterEach, expect, test, vi } from "vitest";
import { contentSecurityPolicy, securityHeaders } from "../../lib/security";
import nextConfig from "../../next.config";

afterEach(() => vi.unstubAllEnvs());

test.each(["development", "production"] as const)("Vercel %s cannot enable a loopback API rewrite", async mode => {
  vi.stubEnv("NODE_ENV", mode);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("TULYA_LOCAL_API_PROXY", "1");
  expect(await nextConfig.rewrites!()).toEqual([]);
});

test("ordinary production has no localhost rewrite; local integration explicitly opts in", async () => {
  vi.stubEnv("NODE_ENV", "production");
  vi.stubEnv("VERCEL", "");
  vi.stubEnv("TULYA_LOCAL_API_PROXY", "");
  expect(await nextConfig.rewrites!()).toEqual([]);
  vi.stubEnv("TULYA_LOCAL_API_PROXY", "1");
  expect(await nextConfig.rewrites!()).toEqual([{ source: "/api/:path*", destination: "http://127.0.0.1:18000/api/:path*" }]);
});

test("local development retains port 18000 without an environment override", async () => {
  vi.stubEnv("NODE_ENV", "development");
  vi.stubEnv("VERCEL", "");
  vi.stubEnv("TULYA_LOCAL_API_PROXY", "");
  expect(await nextConfig.rewrites!()).toEqual([{ source: "/api/:path*", destination: "http://127.0.0.1:18000/api/:path*" }]);
});

test("production scripts require a nonce without eval, with styles for KaTeX and Plotly", () => {
  const csp = contentSecurityPolicy("test-nonce", false, true);
  expect(csp).toContain("script-src 'self' 'nonce-test-nonce' 'strict-dynamic';");
  expect(csp).not.toContain("unsafe-eval");
  expect(csp).toContain("style-src 'self' 'unsafe-inline'");
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).toContain("upgrade-insecure-requests");
  expect(csp).toContain("connect-src 'self';");
  expect(securityHeaders.find(header => header.key === "X-Frame-Options")?.value).toBe("DENY");
});

test("debug evaluation and local reload connections stay in development", () => {
  expect(contentSecurityPolicy("dev", true, false)).toContain("unsafe-eval");
  expect(contentSecurityPolicy("dev", true, false)).not.toContain("upgrade-insecure-requests");
});
