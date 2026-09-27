import { defineConfig } from "@playwright/test";
import local from "./playwright.config";

const target = process.env.TULYA_PREVIEW_URL;
if (!target || new URL(target).protocol !== "https:") {
  throw new Error("Set TULYA_PREVIEW_URL to the explicitly authorized HTTPS preview origin.");
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
  use: { ...local.use, baseURL: new URL(target).origin },
});
