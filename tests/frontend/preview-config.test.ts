import { afterEach, beforeEach, expect, test, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("AUGMENTR_PREVIEW_URL", undefined);
});
afterEach(() => vi.unstubAllEnvs());

test("remote config defaults to Augmentr and starts no local servers", async () => {
  const { default: config } = await import("../../playwright.preview.config");
  expect(config.use?.baseURL).toBe("https://augmentr.vercel.app");
  expect(config.webServer).toEqual([]);
  expect(config.globalSetup).toBeUndefined();
});

test("an explicit authorized HTTPS origin overrides the default", async () => {
  vi.stubEnv("AUGMENTR_PREVIEW_URL", "https://authorized.example/");
  const { default: config } = await import("../../playwright.preview.config");
  expect(config.use?.baseURL).toBe("https://authorized.example");
});

test.each([
  "",
  "http://augmentr.vercel.app",
  "https://user:password@augmentr.vercel.app",
  "https://augmentr.vercel.app/solve",
  "https://augmentr.vercel.app?query=value",
  "https://augmentr.vercel.app#fragment",
  "not-a-url",
])("remote config rejects an invalid target: %s", async target => {
  vi.stubEnv("AUGMENTR_PREVIEW_URL", target);
  await expect(import("../../playwright.preview.config")).rejects.toThrow("Set AUGMENTR_PREVIEW_URL");
});
