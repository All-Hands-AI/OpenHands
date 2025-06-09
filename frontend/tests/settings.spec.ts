import test, { expect } from "@playwright/test";

test("do not navigate to /settings/billing if not SaaS mode", async ({
  page,
}) => {
  await page.goto("/settings/billing");
  await expect(page.getByTestId("settings-screen")).toBeVisible();
  expect(page.url()).toBe("http://localhost:3001/settings");
});

// FIXME: This test is failing because the config is not being set to SaaS mode
// since MSW is always returning APP_MODE as "oss"
test.skip("navigate to /settings/billing if SaaS mode", async ({ page }) => {
  await page.goto("/settings/billing");
  await expect(page.getByTestId("settings-screen")).toBeVisible();
  expect(page.url()).toBe("http://localhost:3001/settings/billing");
});
