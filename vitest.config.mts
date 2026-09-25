import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["tests/frontend/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/frontend/setup.ts"],
  },
});
