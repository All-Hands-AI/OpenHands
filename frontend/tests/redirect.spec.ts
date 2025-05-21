import { expect, test } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("should redirect to /conversations after uploading a project zip", async ({
  page,
}) => {
  const fileInput = page.getByLabel("Upload a .zip");
  const filePath = path.join(dirname, "fixtures/project.zip");
  await fileInput.setInputFiles(filePath);

  await page.waitForURL(/\/conversations\/\d+/);
});

test("should redirect to /conversations after selecting a GitHub repo", async ({
  page,
}) => {
  // enter a github token to view the repositories
  const connectToGitHubButton = page.getByRole("button", {
    name: /connect to github/i,
  });
  await connectToGitHubButton.click();
  const tokenInput = page.getByLabel(/github token\*/i);
  await tokenInput.fill("fake-token");

  const submitButton = page.getByTestId("connect-to-github");
  await submitButton.click();

  // select a repository
  const repoDropdown = page.getByLabel(/github repository/i);
  await repoDropdown.click();

  const repoItem = page.getByTestId("github-repo-item").first();
  await repoItem.click();

  await page.waitForURL(/\/conversations\/\d+/);
});

test("should redirect to /conversations after selecting an Azure DevOps repo", async ({
  page,
}) => {
  // enter an Azure DevOps token to view the repositories
  const connectToAzureDevOpsButton = page.getByRole("button", {
    name: /connect to azure devops/i,
  });
  await connectToAzureDevOpsButton.click();
  const tokenInput = page.getByLabel(/azure devops token\*/i);
  await tokenInput.fill("fake-token");

  const organizationInput = page.getByLabel(/azure devops organization\*/i);
  await organizationInput.fill("test-organization");

  const submitButton = page.getByTestId("connect-to-azure-devops");
  await submitButton.click();

  // select a repository
  const repoDropdown = page.getByLabel(/azure devops repository/i);
  await repoDropdown.click();

  const repoItem = page.getByTestId("azure-devops-repo-item").first();
  await repoItem.click();

  await page.waitForURL(/\/conversations\/\d+/);
});

// FIXME: This fails because the MSW WS mocks change state too quickly,
// missing the OPENING status where the initial query is rendered.
test.skip("should redirect the user to /conversation with their initial query after selecting a project", async ({
  page,
}) => {
  // enter query
  const testQuery = "this is my test query";
  const textbox = page.getByPlaceholder(/what do you want to build/i);
  expect(textbox).not.toBeNull();
  await textbox.fill(testQuery);

  const fileInput = page.getByLabel("Upload a .zip");
  const filePath = path.join(dirname, "fixtures/project.zip");
  await fileInput.setInputFiles(filePath);

  await page.waitForURL("/conversation");

  // get user message
  const userMessage = page.getByTestId("user-message");
  expect(await userMessage.textContent()).toBe(testQuery);
});
