import { defineConfig } from "@playwright/test";
import local from "./playwright.config";

const target = process.env.AUGMENTR_PREVIEW_URL ?? "https://augmentr-solvr.vercel.app";
let origin: string;
try {
  const url = new URL(target);
  if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("Invalid origin");
  }
  origin = url.origin;
} catch {
  throw new Error("Set AUGMENTR_PREVIEW_URL to an authorized HTTPS origin without credentials, a path, query, or fragment (default: https://augmentr-solvr.vercel.app).");
}

export default defineConfig({
  ...local,
  testDir: "./tests",
  testMatch: ["e2e/**/*.spec.ts", "preview/**/*.spec.ts"],
  globalSetup: undefined,
  webServer: [],
  retries: 0,
  workers: 2,
  timeout: 90_000,
  outputDir: "test-results/preview",
  reporter: [["list"], ["json", { outputFile: "test-results/preview-results.json" }]],
  use: { ...local.use, baseURL: origin },
});
