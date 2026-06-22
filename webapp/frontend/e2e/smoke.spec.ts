import { expect, test } from "@playwright/test";

const BE = "http://127.0.0.1:10701";
const FE = "http://127.0.0.1:10700";

test.describe("Fleet Audit", () => {
  test("Backend health", async ({ request }) => {
    const resp = await request.get(`${BE}/health`);
    expect(resp.status()).toBe(200);
  });

  test("Backend dashboard API", async ({ request }) => {
    const resp = await request.get(`${BE}/api/v1/dashboard`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toHaveProperty("host");
    expect(data).toHaveProperty("vms");
  });

  test("Frontend loads", async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator("#root")).toBeAttached();
  });

  test("Dashboard page has KPIs", async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="kpi-cpu"]')).toBeAttached();
    await expect(page.locator('[data-testid="kpi-memory"]')).toBeAttached();
    await expect(page.locator('[data-testid="kpi-disk"]')).toBeAttached();
    await expect(page.locator('[data-testid="kpi-vms"]')).toBeAttached();
  });

  test("Backend status indicator visible", async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="backend-status"]')).toBeAttached();
  });

  test("Navigation sidebar has API Docs link", async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.getByText("API Docs")).toBeAttached();
  });

  test("No console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    expect(errors).toEqual([]);
  });

  test("Settings page loads", async ({ page }) => {
    await page.goto(`${FE}/settings`, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator("#root")).toBeAttached();
  });
});
