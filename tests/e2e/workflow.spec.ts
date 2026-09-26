import { expect, test, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";

async function preset(page: Page, name = "unique") {
  await page.goto("/solve");
  await page.getByLabel("Explore an example").selectOption(name);
}
async function analyze(page: Page) {
  const pending = page.waitForResponse(r => r.url().endsWith("/api/v1/analyze") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  const response = await pending;
  expect(response.status()).toBe(200);
  expect(response.headers()["x-request-id"]).toBeTruthy();
  await expect(page.getByRole("heading", { name: "Method settings" })).toBeVisible();
}
async function solve(page: Page, heading = "Unique solution") {
  const pending = page.waitForResponse(r => r.url().endsWith("/api/v1/solve") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Solve system", exact: true }).click();
  expect((await pending).status()).toBe(200);
  await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
}
test("matrix editing, keyboard navigation, validation recovery and Gaussian replay", async ({ page }) => {
  await preset(page);
  const first = page.getByLabel("Row 1, x1", { exact: true });
  await first.fill("1/0");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await expect(first).toHaveAttribute("aria-invalid", "true");
  await first.fill("4"); await first.press("ArrowRight");
  await expect(page.getByLabel("Row 1, x2", { exact: true })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Row 1, right-hand side", { exact: true })).toBeFocused();
  await expect(page.getByRole("heading", { name: "Method settings" })).toHaveCount(0);
  await analyze(page); await solve(page);
  await expect(page.getByRole("button", { name: "Previous step", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(page.getByText("Eliminate a coefficient", { exact: true })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "2 · target", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.getByText("Original augmented matrix", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("server validation 422 recovers after a bounded-value correction", async ({ page }) => {
  await preset(page); await page.getByLabel("Row 1, x1", { exact: true }).fill("1e20");
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Check your input" })).toBeVisible();
  await expect(page.getByLabel("Row 1, x1", { exact: true })).toHaveAttribute("aria-invalid", "true");
  await page.getByLabel("Row 1, x1", { exact: true }).fill("4");
  await analyze(page); await solve(page);
});

test("exact Gauss-Jordan row swaps and deterministic full report downloads", async ({ page }, testInfo) => {
  await preset(page, "permutation"); await page.getByRole("combobox", { name: "Arithmetic", exact: true }).selectOption("exact");
  await analyze(page); await page.getByRole("radio", { name: "Gauss–Jordan", exact: true }).check();
  await solve(page); await page.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(page.getByText("Swap equations", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "End", exact: true }).click();
  await expect(page.getByText("Scale a pivot row", { exact: true })).toBeVisible();
  const texts: Record<string, string> = {};
  for (const [label, extension] of [["Markdown", "md"], ["LaTeX", "tex"], ["JSON", "json"]]) {
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: `Download ${label}` }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe(`tulya-gauss_jordan-report.${extension}`);
    texts[extension!] = await readFile((await download.path())!, "utf8");
    await download.saveAs(testInfo.outputPath(`report.${extension}`));
  }
  expect(texts.md).toContain("Complete elimination trace"); expect(texts.tex).toContain("\\frac{");
  expect(JSON.parse(texts.json!).outcome.result.trace.length).toBeGreaterThan(1);
  expect(JSON.parse(texts.json!).analysis.classification.classification).toBe("unique");
  const repeat = page.waitForEvent("download"); await page.getByRole("button", { name: "Download JSON" }).click();
  expect(await readFile((await (await repeat).path())!, "utf8")).toBe(texts.json);
  await page.getByRole("button", { name: "Open printable report" }).click();
  await expect(page.getByRole("article", { name: "Complete printable report" })).toBeVisible();
  await expect(page.locator(".report-preview .katex").first()).toBeVisible();
  await page.emulateMedia({ media: "print" });
  await expect(page.getByRole("button", { name: "Download JSON" })).toBeHidden();
  await expect(page.getByRole("article", { name: "Complete printable report" })).toBeVisible();
  expect(await page.locator(".report-preview").evaluate(e => getComputedStyle(e).color)).toBe("rgb(0, 0, 0)");
  await page.locator(".report-preview").screenshot({ path: testInfo.outputPath("print-report.png") });
  if (testInfo.project.name === "chromium") await page.pdf({ path: testInfo.outputPath("report.pdf"), format: "A4", printBackground: true });
});

for (const method of ["Jacobi", "Gauss–Seidel"]) {
  test(`${method} applies row permutation and draws an iteration trajectory`, async ({ page }) => {
    await preset(page, "permutation"); await analyze(page);
    await page.getByRole("radio", { name: method, exact: true }).check();
    await solve(page, "Converged");
    await expect(page.getByText("Equations reordered", { exact: true })).toBeVisible();
    await expect(page.getByText(/1 ← 2; 2 ← 1/)).toBeVisible();
    await page.getByRole("button", { name: "Show geometry" }).click();
    await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible({ timeout: 60_000 });
    await expect(page.locator(".geometry-canvas")).toContainText("Iteration trajectory");
    await page.getByRole("button", { name: "Hide geometry" }).click();
    await expect(page.locator(".geometry-canvas")).toHaveCount(0);
  });
  test(`${method} declines risk, then honors explicit consent without claiming convergence`, async ({ page }) => {
    await preset(page, "divergent"); await analyze(page);
    await page.getByRole("radio", { name: method, exact: true }).check();
    await solve(page, "Convergence risk declined");
    await page.getByLabel("Run even if convergence is not guaranteed").check();
    await page.getByLabel("Maximum iterations", { exact: true }).fill("3");
    await solve(page, "Iteration limit reached");
    await expect(page.getByRole("heading", { name: "Last iterate — not a converged solution" })).toBeVisible();
  });
}

test("infinite rectangular system explains eligibility and unavailable geometry", async ({ page }) => {
  await preset(page, "infinite"); await analyze(page);
  await expect(page.getByRole("radio", { name: "Jacobi", exact: true })).toBeDisabled();
  await solve(page, "Infinitely many solutions");
  await expect(page.getByRole("heading", { name: "Parametric solution" })).toBeVisible();
  await expect(page.getByText(/Geometric plotting is available for 2 × 2 and 3 × 3/)).toBeVisible();
});

for (const [name, heading] of [["inconsistent", "Inconsistent system"], ["coincident", "Infinitely many solutions"], ["planes", "Unique solution"], ["line3d", "Infinitely many solutions"]]) {
  test(`geometry renders ${name} and toggles cleanly`, async ({ page }, testInfo) => {
    await preset(page, name); await analyze(page); await solve(page, heading);
    await page.getByRole("button", { name: "Show geometry" }).click();
    await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible({ timeout: 60_000 });
    await expect(page.locator(".geometry-canvas .plot-container")).toHaveCount(1);
    if (name === "inconsistent") await expect(page.getByText(/There is no common intersection/)).toBeVisible();
    if (name === "line3d") await expect(page.getByText(/solution family has 1 free parameter/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.locator(".geometry-content").screenshot({ path: testInfo.outputPath("geometry.png") });
    await page.getByRole("button", { name: "Hide geometry" }).click();
    await expect(page.locator(".geometry-canvas")).toHaveCount(0);
  });
}

test("network failure and 500 can be retried without losing the matrix", async ({ page }) => {
  await preset(page);
  await page.route("**/api/v1/analyze", route => route.abort(), { times: 1 });
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Request could not be completed" })).toBeVisible();
  await page.route("**/api/v1/analyze", route => route.fulfill({ status: 500, contentType: "application/json", headers: { "X-Request-ID": "e2e-500" }, body: JSON.stringify({ status: "error", request_id: "e2e-500", error: { code: "internal_error", message: "Internal server error.", location: [] }, details: [] }) }), { times: 1 });
  await page.getByRole("button", { name: "Retry request" }).click();
  await expect(page.getByRole("heading", { name: "The solver encountered an error" })).toBeVisible();
  await expect(page.getByText("Request e2e-500")).toBeVisible();
  await page.getByRole("button", { name: "Retry request" }).click();
  await expect(page.getByRole("heading", { name: "Method settings" })).toBeVisible();
  await expect(page.getByLabel("Row 1, x1", { exact: true })).toHaveValue("4");
});

test("non-zero diagonal fallback is explicit and supports a bounded risky run", async ({ page }) => {
  await preset(page, "planes");
  const a = [[0,1,1],[1,1,1],[1,2,3]];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) await page.getByLabel(`Row ${i + 1}, x${j + 1}`, { exact: true }).fill(String(a[i]![j]));
  await analyze(page); await page.getByRole("radio", { name: "Jacobi", exact: true }).check();
  await page.getByLabel("Seek strict diagonal dominance by reordering rows").uncheck();
  await page.getByLabel("Allow non-zero diagonal fallback").check();
  await page.getByLabel("Run even if convergence is not guaranteed").check();
  await page.getByLabel("Maximum iterations", { exact: true }).fill("2");
  await solve(page, "Iteration limit reached");
  await expect(page.getByText("Equations reordered", { exact: true })).toBeVisible();
  await expect(page.getByText(/Reason: nonzero diagonal/)).toBeVisible();
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible();
  await expect(page.locator(".geometry-canvas")).toContainText("Iteration trajectory");
});

test("canceling an in-flight request preserves editable input", async ({ page }) => {
  await preset(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/analyze", async route => { await gate; await route.continue().catch(() => {}); });
  await page.getByRole("button", { name: "Analyze system", exact: true }).click();
  await page.getByRole("button", { name: "Cancel request", exact: true }).click();
  release();
  await page.getByLabel("Row 1, x1", { exact: true }).fill("5");
  await expect(page.getByRole("heading", { name: "Method settings" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Analyze system", exact: true })).toBeEnabled();
});

test("Plotly is fetched only after opening geometry, and reopening draws a fresh plot", async ({ page }) => {
  const plotRequests: string[] = [];
  page.on("request", request => { if (/plotly/i.test(request.url()) && request.resourceType() === "script") plotRequests.push(request.url()); });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(plotRequests).toEqual([]);
  await preset(page); await analyze(page); await solve(page);
  expect(plotRequests).toEqual([]);
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.getByText("Interactive geometry ready", { exact: true })).toBeVisible();
  expect(plotRequests.length).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Hide geometry" }).click();
  await page.getByRole("button", { name: "Show geometry" }).click();
  await expect(page.locator(".geometry-canvas .plot-container")).toHaveCount(1);
});
