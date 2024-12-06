import { expect, Page, test } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

const confirmSettings = async (page: Page) => {
  const confirmPreferenceButton = page.getByRole("button", {
    name: /confirm preferences/i,
  });
  await confirmPreferenceButton.click();

  const configSaveButton = page.getByRole("button", {
    name: /save/i,
  });
  await configSaveButton.click();

  const confirmChanges = page.getByRole("button", {
    name: /yes, close settings/i,
  });
  await confirmChanges.click();
};

test("should redirect to /app after uploading a project zip", async ({
  page,
}) => {
  await page.goto("/");

  const fileInput = page.getByLabel("Upload a .zip");
  const filePath = path.join(dirname, "fixtures/project.zip");
  await fileInput.setInputFiles(filePath);

  await page.waitForURL("/app");
});

test("should redirect to /app after selecting a repo", async ({ page }) => {
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

  await page.waitForURL("/app");
  expect(page.url()).toBe("http://127.0.0.1:3000/app");
});

// FIXME: This fails because the MSW WS mocks change state too quickly,
// missing the OPENING status where the initial query is rendered.
test.fail(
  "should redirect the user to /app with their initial query after selecting a project",
  async ({ page }) => {
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

    await page.waitForURL("/app");

    // get user message
    const userMessage = page.getByTestId("user-message");
    expect(await userMessage.textContent()).toBe(testQuery);
  },
);

test("redirect to /app if token is present", async ({ page }) => {
  await page.goto("/");

  await page.evaluate(() => {
    localStorage.setItem("token", "test");
  });

  await page.waitForURL("/app");

  expect(page.url()).toBe("http://localhost:3001/app");
});
