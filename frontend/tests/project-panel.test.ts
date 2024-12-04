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

  // select a project
  const projectItem = page.getByTestId("project-card").first();
  await projectItem.click();

  await page.waitForURL("/app?sessionId=1");
  expect(page.url()).toBe("http://localhost:3001/app?sessionId=1");
});
