import { screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import userEvent from "@testing-library/user-event";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { SettingsForm } from "#/components/shared/modals/settings/settings-form";
import OpenHands from "#/api/open-hands";

describe("SettingsForm", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

  const onCloseMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  getConfigSpy.mockResolvedValue({
    APP_MODE: "saas",
    GITHUB_CLIENT_ID: "123",
    POSTHOG_CLIENT_KEY: "123",
  });

  const RouterStub = createRoutesStub([
    {
      Component: () => (
        <SettingsForm
          settings={DEFAULT_SETTINGS}
          models={["anthropic/claude-3-5-sonnet-20241022", "model2"]}
          agents={["CodeActAgent", "agent2"]}
          securityAnalyzers={["analyzer1", "analyzer2"]}
          onClose={onCloseMock}
        />
      ),
      path: "/",
    },
  ]);

  it("should not show runtime size selector by default", () => {
    renderWithProviders(<RouterStub />);
    expect(screen.queryByText("Runtime Size")).not.toBeInTheDocument();
  });

  it("should show runtime size selector when advanced options are enabled", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RouterStub />);

    const toggleAdvancedMode = screen.getByTestId("advanced-option-switch");
    await user.click(toggleAdvancedMode);

    await screen.findByTestId("runtime-size");
  });

  it("should not submit the form if required fields are empty", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RouterStub />);

    expect(screen.queryByTestId("custom-model-input")).not.toBeInTheDocument();

    const toggleAdvancedMode = screen.getByTestId("advanced-option-switch");
    await user.click(toggleAdvancedMode);

    const customModelInput = screen.getByTestId("custom-model-input");
    expect(customModelInput).toBeInTheDocument();

    await user.clear(customModelInput);

    const saveButton = screen.getByTestId("save-settings-button");
    await user.click(saveButton);

    expect(saveSettingsSpy).not.toHaveBeenCalled();
    expect(onCloseMock).not.toHaveBeenCalled();
  });
});
