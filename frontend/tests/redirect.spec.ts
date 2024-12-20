import { expect, test } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";
import { confirmSettings } from "./helpers/confirm-settings";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

test("should redirect to /conversation after uploading a project zip", async ({
  page,
}) => {
  await page.goto("/");
  await page.evaluate(() => {
    localStorage.setItem("analytics-consent", "true");
    localStorage.setItem("SETTINGS_VERSION", "4");
  });

  const fileInput = page.getByLabel("Upload a .zip");
  const filePath = path.join(dirname, "fixtures/project.zip");
  await fileInput.setInputFiles(filePath);

  await page.waitForURL("/conversation");
});

test("should redirect to /conversation after selecting a repo", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

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

  await page.waitForURL("/conversation");
  expect(page.url()).toBe("http://localhost:3001/conversation");
});

// FIXME: This fails because the MSW WS mocks change state too quickly,
// missing the OPENING status where the initial query is rendered.
test.skip("should redirect the user to /conversation with their initial query after selecting a project", async ({
  page,
}) => {
  await page.goto("/");
  await confirmSettings(page);

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

test("redirect to /conversation if token is present", async ({ page }) => {
  await page.goto("/");

  await page.evaluate(() => {
    localStorage.setItem("token", "test");
  });

  await page.waitForURL("/conversation");
  expect(page.url()).toBe("http://localhost:3001/conversation");
});
