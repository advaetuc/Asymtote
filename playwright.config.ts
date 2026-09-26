import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: 2,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  globalSetup: "./tests/e2e/global-setup.ts",
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: "uv run uvicorn api.index:app --host 127.0.0.1 --port 18000",
      url: "http://127.0.0.1:18000/api/health",
      reuseExistingServer: !process.env.CI && process.env.E2E_REUSE_SERVERS !== "0",
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
      url: "http://127.0.0.1:3000/solve",
      reuseExistingServer: !process.env.CI && process.env.E2E_REUSE_SERVERS !== "0",
      timeout: 120_000,
    },
  ],
});
