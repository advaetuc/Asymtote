import { expect, test } from "@playwright/test";

test("landing renders and the same-origin Python health endpoint responds", async ({ page, request }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Augmentr — Linear system solver");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Augmentr");
  await expect(page.getByRole("link", { name: "Augmentr home" })).toBeVisible();
  await page.getByRole("link", { name: /New to these methods/ }).click();
  await expect(page).toHaveURL(/\/learn$/);
  await expect(page).toHaveTitle("How these methods work — Augmentr");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("How these methods work");
  await page.getByRole("link", { name: /Start solving/ }).click();
  await expect(page).toHaveTitle("Solver workspace — Augmentr");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("How many equations, how many unknowns?");
  const response = await request.get("/api/health");
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toEqual({ status: "ok", api_version: "0.1.0" });
});
