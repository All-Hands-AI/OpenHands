import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import OpenHands from "#/api/open-hands";
import { MOCK_USER_PREFERENCES } from "#/mocks/handlers";

describe("AccountSettingsModal", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

  afterEach(() => {
    vi.clearAllMocks();
    vi.resetAllMocks();
  });

  it("should save the settings", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const githubTokenLabel = screen.getByTestId("github-token");
    const githubTokenInput =
      within(githubTokenLabel).getByTestId("github-token-input");

    const languageInput = screen.getByLabelText(/language/i);
    await user.click(languageInput);

    const norskOption = screen.getByText(/norsk/i);
    await user.click(norskOption);

    await user.type(githubTokenInput, "1234");
    await user.tab();

    await user.click(screen.getByTestId("save-settings"));

    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith({
        github_token: "1234",
        language: "no", // Norwegian
      });
    });
  });

  it("should not send unchanged values", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const githubTokenLabel = screen.getByTestId("github-token");
    const githubTokenInput =
      within(githubTokenLabel).getByTestId("github-token-input");

    await user.type(githubTokenInput, " ");
    await user.tab();

    await user.click(screen.getByTestId("save-settings"));

    await waitFor(() => {
      expect(saveSettingsSpy).not.toHaveBeenCalled();
    });

    await user.type(githubTokenInput, "1234");
    await user.tab();

    await user.click(screen.getByTestId("save-settings"));

    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith({
        github_token: "1234",
      });
    });
  });

  describe("GitHub token", () => {
    it("should render an unset badge when the user has no GitHub token set", () => {
      renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

      const githubTokenLabel = screen.getByTestId("github-token");
      const githubTokenInput =
        within(githubTokenLabel).getByTestId("github-token-input");

      expect(githubTokenInput).toBeEnabled();
      within(githubTokenLabel).getByText("unset");
    });

    it("should render a set badge when the user has a GitHub token set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_USER_PREFERENCES.settings,
        github_token_is_set: true,
      });

      renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

      const githubTokenLabel = screen.getByTestId("github-token");
      const githubTokenInput =
        within(githubTokenLabel).queryByTestId("github-token-input");

      await waitFor(() => {
        expect(githubTokenInput).not.toBeInTheDocument();
        within(githubTokenLabel).getByText("set");
      });
    });

    it("should render an unset button when the user has a GitHub token set", async () => {
      const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_USER_PREFERENCES.settings,
        github_token_is_set: true,
      });

      renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

      const githubTokenLabel = screen.getByTestId("github-token");
      const githubTokenButton = await within(githubTokenLabel).findByTestId(
        "unset-github-token-button",
      );

      await user.click(githubTokenButton);
      expect(saveSettingsSpy).toHaveBeenCalledWith({
        github_token: "",
      });
    });
  });
});
