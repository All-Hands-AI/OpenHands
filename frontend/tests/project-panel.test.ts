import test, { expect, Page } from "@playwright/test";
import { confirmSettings } from "./helpers/confirm-settings";

const selectProjectCard = async (page: Page, index: number) => {
  // open project panel
  const projectPanelButton = page.getByTestId("toggle-project-panel");
  await projectPanelButton.click();

  const panel = page.getByTestId("project-panel");

  // select a project
  const projectItem = panel.getByTestId("project-card").nth(index);
  await projectItem.click();

  // panel should close
  expect(panel).not.toBeVisible();

  await page.waitForURL(`/app?sessionId=${index + 1}`);
  expect(page.url()).toBe(`http://localhost:3001/app?sessionId=${index + 1}`);
};

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

  const ellipsisButton = firstCard.getByTestId("ellipsis-button");
  await ellipsisButton.click();

  const deleteButton = firstCard.getByTestId("delete-button");
  await deleteButton.click();

  // confirm modal
  const confirmButton = page.getByText("Confirm");
  await confirmButton.click();

  await page.waitForURL("/");
});

test("load relevant files in the file explorer", async ({ page }) => {
  await page.goto("/");
  await confirmSettings(page);
  await selectProjectCard(page, 0);

  // check if the file explorer has the correct files
  const fileExplorer = page.getByTestId("file-explorer");

  await expect(fileExplorer.getByText("file1.txt")).toBeVisible();
  await expect(fileExplorer.getByText("file2.txt")).toBeVisible();
  await expect(fileExplorer.getByText("file3.txt")).toBeVisible();

  await selectProjectCard(page, 2);

  // check if the file explorer has the correct files
  expect(fileExplorer.getByText("reboot_skynet.exe")).toBeVisible();
  expect(fileExplorer.getByText("target_list.txt")).toBeVisible();
  expect(fileExplorer.getByText("terminator_blueprint.txt")).toBeVisible();
});
