import test, { expect } from "@playwright/test";
import { confirmSettings } from "./helpers/confirm-settings";

test("redirect to /app with the session id as a query param", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

  // open project panel
  const projectPanelButton = page.getByTestId("toggle-project-panel");
  await projectPanelButton.click();

  const panel = page.getByTestId("project-panel");

  // select a project
  const projectItem = panel.getByTestId("project-card").first();
  await projectItem.click();

  // panel should close
  expect(panel).not.toBeVisible();

  await page.waitForURL("/app?sessionId=1");
  expect(page.url()).toBe("http://localhost:3001/app?sessionId=1");
});
