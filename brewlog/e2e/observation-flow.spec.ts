import { expect, test } from "@playwright/test";

test("admin sees user observed after permission-denied burst", async ({ page, browser }) => {
  // 1. Register a normal user
  await page.goto("/register");
  await page.fill('input[type=email]', "victim@x.com");
  await page.fill('input[type=password]', "hunter2");
  await page.click('button[type=submit]');
  await expect(page).toHaveURL(/\/dashboard/);

  // 2. Trigger 5x permission-denied bursts via direct API (uses cookie context)
  for (let i = 0; i < 5; i++) {
    await page.request.get("/api/v1/admin/observed-users");
  }

  // 3. Open a second browser as admin
  const adminCtx = await browser.newContext();
  const adminPage = await adminCtx.newPage();
  await adminPage.goto("/login");
  await adminPage.fill('input[type=email]', "admin@brewlog.local");
  await adminPage.fill('input[type=password]', "admin");
  await adminPage.click('button[type=submit]');
  await adminPage.goto("/admin/observed");
  await expect(adminPage.locator('text=victim@x.com')).toBeVisible();
});
