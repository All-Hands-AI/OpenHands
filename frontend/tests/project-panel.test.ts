import test, { expect, Page } from "@playwright/test";
import { confirmSettings } from "./helpers/confirm-settings";

const openProjectPanel = async (page: Page) => {
  const projectPanelButton = page.getByTestId("toggle-project-panel");
  await projectPanelButton.click();

  return page.getByTestId("project-panel");
};

const selectProjectCard = async (page: Page, index: number) => {
  const panel = await openProjectPanel(page);

  // select a project
  const projectItem = panel.getByTestId("project-card").nth(index);
  await projectItem.click();

  // panel should close
  expect(panel).not.toBeVisible();

  await page.waitForURL(`/conversation?cid=${index + 1}`);
  expect(page.url()).toBe(
    `http://localhost:3001/conversation?cid=${index + 1}`,
  );
};

test("should only display the create new project button in /conversation", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);
  const panel = await openProjectPanel(page);

  const newProjectButton = panel.getByTestId("new-project-button");
  await expect(newProjectButton).not.toBeVisible();

  await page.goto("/conversation");
  await openProjectPanel(page);
  expect(newProjectButton).toBeVisible();
});

test("redirect to /conversation with the session id as a query param", async ({
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

  await page.waitForURL("/conversation?cid=1");
  expect(page.url()).toBe("http://localhost:3001/conversation?cid=1");
});

test("redirect to the home screen if the current session was deleted", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

  await page.goto("/conversation?cid=1");
  await page.waitForURL("/conversation?cid=1");

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
