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

test("redirect to the home screen if the current session was deleted", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

  await page.goto("/app?sessionId=1");
  await page.waitForURL("/app?sessionId=1");

  // open project panel
  const projectPanelButton = page.getByTestId("toggle-project-panel");
  await projectPanelButton.click();

  const panel = page.getByTestId("project-panel");
  const firstCard = panel.getByTestId("project-card").first();
  const deleteButton = firstCard.getByTestId("delete-button");

  await deleteButton.click();

  // confirm modal
  const confirmButton = page.getByText("Confirm");
  await confirmButton.click();

  await page.waitForURL("/");
});

test("redirect to the home screen if the current session is not found", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

  await page.goto("/app?sessionId=11111");
  await page.waitForURL("/");
});
