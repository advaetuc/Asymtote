import { expect, test } from "@playwright/test";

test("landing renders and the same-origin Python health endpoint responds", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Linear equations");
  await page.getByRole("link", { name: /Explore the four methods/ }).click();
  await expect(page).toHaveURL(/#methods$/);
  const response = await request.get("/api/health");
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toEqual({ status: "ok", api_version: "0.1.0" });
});
