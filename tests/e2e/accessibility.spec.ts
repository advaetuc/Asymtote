import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function audit(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]).analyze();
  expect(result.violations).toEqual([]);
}

for (const path of ["/", "/solve", "/learn"]) {
  test(`accessible page, keyboard skip link and security headers: ${path}`, async ({ page }) => {
    const response = await page.goto(path);
    expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
    expect(response?.headers()["x-frame-options"]).toBe("DENY");
    expect(response?.headers()["referrer-policy"]).toBe("no-referrer");
    expect(response?.headers()["permissions-policy"]).toContain("camera=()");
    const csp = response?.headers()["content-security-policy"] ?? "";
    expect(csp).toContain("'strict-dynamic'");
    if (process.env.E2E_PRODUCTION === "1") expect(csp).not.toContain("unsafe-eval");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
    expect(await page.getByRole("link", { name: "Skip to content" }).evaluate(element => parseFloat(getComputedStyle(element).outlineWidth))).toBeGreaterThanOrEqual(2);
    await page.keyboard.press("Enter");
    await audit(page);
    await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
    await audit(page);
  });
}

test("matrix errors, direct replay and complete report remain accessible", async ({ page }) => {
  await page.goto("/solve");
  await page.getByLabel("Explore an example").selectOption("unique");
  await page.getByLabel("Row 1, x1", { exact: true }).fill("1/0");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await expect(page.getByLabel("Row 1, x1", { exact: true })).toHaveAttribute("aria-invalid", "true");
  await audit(page);
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await audit(page);
  await page.emulateMedia({ forcedColors: "none", reducedMotion: "no-preference" });
  await page.getByLabel("Explore an example").selectOption("unique");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await page.getByRole("button", { name: "Solve system", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Unique solution", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await page.getByRole("button", { name: "Open printable report" }).click();
  await audit(page);
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await audit(page);
});

test("iterative table and geometry descriptions remain accessible", async ({ page }) => {
  await page.goto("/solve");
  await page.getByLabel("Explore an example").selectOption("permutation");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await page.getByRole("radio", { name: "Jacobi iteration", exact: true }).check();
  await page.getByRole("button", { name: "Solve system", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Converged", exact: true })).toBeVisible();
  await audit(page);
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible({ timeout: 60_000 });
  await audit(page);
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await audit(page);
});

test("fresh script nonces and CSP-compatible 3D WebGL and KaTeX", async ({ page }) => {
  const violations: string[] = [];
  page.on("console", message => { if (/violat.*content security policy|refused to.*(?:script|evaluate)/i.test(message.text())) violations.push(message.text()); });
  const first = await page.goto("/solve");
  const next = await page.reload();
  expect(first?.headers()["content-security-policy"]).not.toBe(next?.headers()["content-security-policy"]);
  await page.getByLabel("Explore an example").selectOption("planes");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await page.getByRole("button", { name: "Solve system", exact: true }).click();
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible({ timeout: 60_000 });
  await page.getByRole("button", { name: "Open printable report" }).click();
  await expect(page.locator(".report-preview .katex").first()).toBeVisible();
  expect(violations).toEqual([]);
});
