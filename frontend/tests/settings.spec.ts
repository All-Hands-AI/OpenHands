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

  const providerSelect = aiConfigModal.getByTestId("llm-provider");
  expect(providerSelect).toBeDefined();

  await providerSelect.click();

  const openAiOption = page.getByTestId("provider-item-openai");
  expect(openAiOption).toBeDefined();

  await openAiOption.click();

  const modelSelect = aiConfigModal.getByTestId("llm-model");
  expect(modelSelect).toBeDefined();

  await modelSelect.click();

  const gpt4Option = page.getByText("gpt-4o");
  expect(gpt4Option).toBeDefined();

  await gpt4Option.click();

  const saveButton = aiConfigModal.getByText("Save");
  expect(saveButton).toBeDefined();

  await saveButton.click();

  const settingsButton = page.getByTestId("settings-button");
  await settingsButton.click();

  await expect(providerSelect).toHaveValue("OpenAI");
  await expect(modelSelect).toHaveValue("gpt-4o");
});

test.skip("change user settings", async ({}) => {});
