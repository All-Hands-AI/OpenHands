import test, { expect, Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => {
    localStorage.setItem("analytics-consent", "true");
    localStorage.setItem("SETTINGS_VERSION", "4");
  });
});

const selectGpt4o = async (page: Page) => {
  const aiConfigModal = page.getByTestId("ai-config-modal");
  await expect(aiConfigModal).toBeVisible();

  const providerSelectElement = aiConfigModal.getByTestId("llm-provider");
  await providerSelectElement.click();

  const openAiOption = page.getByTestId("provider-item-openai");
  await openAiOption.click();

  const modelSelectElement = aiConfigModal.getByTestId("llm-model");
  await modelSelectElement.click();

  const gpt4Option = page.getByText("gpt-4o", { exact: true });
  await gpt4Option.click();

  return {
    aiConfigModal,
    providerSelectElement,
    modelSelectElement,
  };
};

test("change ai config settings", async ({ page }) => {
  const { aiConfigModal, modelSelectElement, providerSelectElement } =
    await selectGpt4o(page);

  const saveButton = aiConfigModal.getByText("Save");
  await saveButton.click();

  const settingsButton = page.getByTestId("settings-button");
  await settingsButton.click();

  await expect(providerSelectElement).toHaveValue("OpenAI");
  await expect(modelSelectElement).toHaveValue("gpt-4o");
});

test("reset to default settings", async ({ page }) => {
  const { aiConfigModal } = await selectGpt4o(page);

  const saveButton = aiConfigModal.getByText("Save");
  await saveButton.click();

  const settingsButton = page.getByTestId("settings-button");
  await settingsButton.click();

  const resetButton = aiConfigModal.getByText(/reset to defaults/i);
  await resetButton.click();

  const endSessionModal = page.getByTestId("reset-defaults-modal");
  expect(endSessionModal).toBeVisible();

  const confirmButton = endSessionModal.getByText(/reset to defaults/i);
  await confirmButton.click();

  await settingsButton.click();

  const providerSelectElement = aiConfigModal.getByTestId("llm-provider");
  await expect(providerSelectElement).toHaveValue("Anthropic");

  const modelSelectElement = aiConfigModal.getByTestId("llm-model");
  await expect(modelSelectElement).toHaveValue(/claude-3.5/i);
});
