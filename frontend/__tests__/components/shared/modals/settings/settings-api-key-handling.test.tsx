import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { screen } from "@testing-library/react";
import OpenHands from "#/api/open-hands";
import { SettingsForm } from "#/components/shared/modals/settings/settings-form";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { Settings } from "#/types/settings";

describe("Settings API Key Handling", () => {
  const onCloseMock = vi.fn();
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

  beforeEach(() => {
    saveSettingsSpy.mockClear();
    onCloseMock.mockClear();
  });

  it("should preserve the API key when submitting from the modal with asterisks", async () => {
    // Create settings with an API key that's already set (showing asterisks)
    const settingsWithApiKey: Settings = {
      ...DEFAULT_SETTINGS,
      LLM_API_KEY: "**********", // This represents an already set API key
    };

    const RouteStub = createRoutesStub([
      {
        Component: () => (
          <SettingsForm
            settings={settingsWithApiKey}
            models={[settingsWithApiKey.LLM_MODEL]}
            onClose={onCloseMock}
          />
        ),
        path: "/",
      },
    ]);

    const user = userEvent.setup();
    renderWithProviders(<RouteStub />);

    // Verify the API key input shows placeholder for hidden value
    const apiKeyInput = screen.getByTestId("llm-api-key-input");
    expect(apiKeyInput).toHaveAttribute("placeholder", "<hidden>");

    // Submit the form without changing the API key
    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    // The API key should be undefined to preserve the existing key
    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_api_key: undefined,
      }),
    );
  });

  it("should correctly handle new API key input in the modal", async () => {
    // Create settings with no API key set
    const settingsWithoutApiKey: Settings = {
      ...DEFAULT_SETTINGS,
      LLM_API_KEY: null,
    };

    const RouteStub = createRoutesStub([
      {
        Component: () => (
          <SettingsForm
            settings={settingsWithoutApiKey}
            models={[settingsWithoutApiKey.LLM_MODEL]}
            onClose={onCloseMock}
          />
        ),
        path: "/",
      },
    ]);

    const user = userEvent.setup();
    renderWithProviders(<RouteStub />);

    // Enter a new API key
    const apiKeyInput = screen.getByTestId("llm-api-key-input");
    await user.type(apiKeyInput, "new-api-key");

    // Submit the form
    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    // The new API key should be sent correctly
    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_api_key: "new-api-key",
      }),
    );
  });
});
