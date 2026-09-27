import { expect, test } from "@playwright/test";

test("live happy paths have same-origin API traffic and no browser errors", async ({ page, baseURL }, testInfo) => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const apiRequests: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => {
    if (message.type() === "error") errors.push(message.text());
    if (message.type() === "warning") warnings.push(message.text());
  });
  page.on("request", request => {
    if (new URL(request.url()).pathname.startsWith("/api/")) apiRequests.push(request.url());
  });
  for (const route of ["/", "/learn", "/solve"]) {
    expect((await page.goto(route))?.status()).toBe(200);
    await expect(page.getByRole("main")).toBeVisible();
  }
  for (const method of ["Gaussian elimination", "Gauss–Jordan", "Jacobi", "Gauss–Seidel"]) {
    await page.getByLabel("Explore an example").selectOption("planes");
    const analyzed = page.waitForResponse(response => response.url().endsWith("/api/v1/analyze"));
    await page.getByRole("button", { name: "Analyze system", exact: true }).click();
    expect((await analyzed).status()).toBe(200);
    await page.getByRole("radio", { name: method, exact: true }).check();
    const solved = page.waitForResponse(response => response.url().endsWith("/api/v1/solve"));
    await page.getByRole("button", { name: "Solve system", exact: true }).click();
    expect((await solved).status()).toBe(200);
    await expect(page.getByRole("heading", { name: method.startsWith("Gauss") && method !== "Gauss–Seidel" ? "Unique solution" : "Converged", exact: true })).toBeVisible();
  }
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible({ timeout: 60_000 });
  await page.getByRole("button", { name: "Open printable report" }).click();
  await expect(page.locator(".report-preview .katex").first()).toBeVisible();
  await testInfo.attach("browser-observations", {
    body: JSON.stringify({ origin: baseURL, errors, warnings, apiRequests }, null, 2),
    contentType: "application/json",
  });
  expect(apiRequests.length).toBeGreaterThanOrEqual(8);
  expect(apiRequests.every(url => new URL(url).origin === new URL(baseURL!).origin)).toBe(true);
  expect(errors).toEqual([]);
});
