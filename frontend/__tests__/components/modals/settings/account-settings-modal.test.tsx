import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import OpenHands from "#/api/open-hands";

describe("AccountSettingsModal", () => {
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should send all settings data when saving account settings", async () => {
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const languageInput = screen.getByLabelText(/language/i);
    await user.click(languageInput);

    const norskOption = screen.getByText(/norsk/i);
    await user.click(norskOption);

    const tokenInput = screen.getByTestId("github-token-input");
    await user.type(tokenInput, "new-token");

    const saveButton = screen.getByTestId("save-settings");
    await user.click(saveButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith({
      agent: "CodeActAgent",
      confirmation_mode: false,
      enable_default_condenser: false,
      language: "no",
      github_token: "new-token",
      llm_base_url: "",
      llm_model: "anthropic/claude-3-5-sonnet-20241022",
      remote_runtime_resource_factor: 1,
      security_analyzer: "",
    });
  });

  it("should render a checkmark and not the input if the github token is set", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      github_token_is_set: true,
    });
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    await waitFor(() => {
      const checkmark = screen.queryByTestId("github-token-set-checkmark");
      const input = screen.queryByTestId("github-token-input");

      expect(checkmark).toBeInTheDocument();
      expect(input).not.toBeInTheDocument();
    });
  });

  it("should send an unset github token property when pressing disconnect", async () => {
    const user = userEvent.setup();
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      github_token_is_set: true,
    });
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const disconnectButton = await screen.findByTestId("disconnect-github");
    await user.click(disconnectButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith({
      agent: "CodeActAgent",
      confirmation_mode: false,
      enable_default_condenser: false,
      language: "en",
      llm_base_url: "",
      llm_model: "anthropic/claude-3-5-sonnet-20241022",
      remote_runtime_resource_factor: 1,
      security_analyzer: "",
      unset_github_token: true,
    });
  });

  it("should not unset the github token when changing the language", async () => {
    const user = userEvent.setup();
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      github_token_is_set: true,
    });
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const languageInput = screen.getByLabelText(/language/i);
    await user.click(languageInput);

    const norskOption = screen.getByText(/norsk/i);
    await user.click(norskOption);

    const saveButton = screen.getByTestId("save-settings");
    await user.click(saveButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith({
      agent: "CodeActAgent",
      confirmation_mode: false,
      enable_default_condenser: false,
      language: "no",
      llm_base_url: "",
      llm_model: "anthropic/claude-3-5-sonnet-20241022",
      remote_runtime_resource_factor: 1,
      security_analyzer: "",
    });
  });
});
