import { Page } from "@playwright/test";

export const confirmSettings = async (page: Page) => {
  const confirmPreferenceButton = page.getByRole("button", {
    name: /confirm preferences/i,
  });
  await confirmPreferenceButton.click();

  const configSaveButton = page
    .getByRole("button", {
      name: /save/i,
    })
    .first();
  await configSaveButton.click();

  const confirmChanges = page.getByRole("button", {
    name: /yes, close settings/i,
  });
  await confirmChanges.click();
};
