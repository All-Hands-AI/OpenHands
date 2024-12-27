import test, { expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => {
    localStorage.setItem("analytics-consent", "true");
    localStorage.setItem("SETTINGS_VERSION", "4");
  });
});

test("change ai config settings", async ({ page }) => {
  const aiConfigModal = page.getByTestId("ai-config-modal");
  await expect(aiConfigModal).toBeVisible();
});

test.skip("change user settings", async ({ page }) => {});
