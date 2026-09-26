import { request } from "@playwright/test";

/** Reused ports must belong to this app, including the frontend API proxy. */
export default async function globalSetup() {
  const context = await request.newContext();
  try {
    for (const origin of ["http://127.0.0.1:18000", "http://127.0.0.1:3000"]) {
      const response = await context.get(`${origin}/api/health`);
      if (!response.ok() || JSON.stringify(await response.json()) !== JSON.stringify({ status: "ok", api_version: "0.1.0" })) throw new Error(`Expected TULYA health endpoint at ${origin}. Stop the unrelated service before running E2E tests.`);
    }
  } finally { await context.dispose(); }
}
