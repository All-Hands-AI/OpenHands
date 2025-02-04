import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { AxiosError } from "axios";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import OpenHands from "#/api/open-hands";

// These tests will now fail because the conversation panel is rendered through a portal
// and technically not a child of the Sidebar component.

const RouterStub = createRoutesStub([
  {
    path: "/conversation/:conversationId",
    Component: () => <Sidebar />,
  },
]);

const renderSidebar = () =>
  renderWithProviders(<RouterStub initialEntries={["/conversation/123"]} />);

describe("Sidebar", () => {
  describe("Settings", () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

    afterEach(() => {
      vi.clearAllMocks();
    });

    it("should fetch settings data on mount", () => {
      renderSidebar();
      expect(getSettingsSpy).toHaveBeenCalledOnce();
    });

    it("should send all settings data when saving AI configuration", async () => {
      const user = userEvent.setup();
      renderSidebar();

      const settingsButton = screen.getByTestId("settings-button");
      await user.click(settingsButton);

      const settingsModal = screen.getByTestId("ai-config-modal");
      const saveButton = within(settingsModal).getByTestId(
        "save-settings-button",
      );
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        agent: "CodeActAgent",
        confirmation_mode: false,
        enable_default_condenser: false,
        language: "en",
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        remote_runtime_resource_factor: 1,
      });
    });

    it("should not reset AI configuration when saving account settings", async () => {
      const user = userEvent.setup();
      renderSidebar();

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      const menu = screen.getByTestId("account-settings-context-menu");
      const accountSettingsButton = within(menu).getByTestId(
        "account-settings-button",
      );
      await user.click(accountSettingsButton);

      const accountSettingsModal = screen.getByTestId("account-settings-form");

      const languageInput =
        within(accountSettingsModal).getByLabelText(/language/i);
      await user.click(languageInput);

      const norskOption = screen.getByText(/norsk/i);
      await user.click(norskOption);

      const tokenInput =
        within(accountSettingsModal).getByLabelText(/GITHUB\$TOKEN_LABEL/i);
      await user.type(tokenInput, "new-token");

      const analyticsConsentInput =
        within(accountSettingsModal).getByTestId("analytics-consent");
      await user.click(analyticsConsentInput);

      const saveButton =
        within(accountSettingsModal).getByTestId("save-settings");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        agent: "CodeActAgent",
        confirmation_mode: false,
        enable_default_condenser: false,
        github_token: "new-token",
        language: "no",
        llm_base_url: "",
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        remote_runtime_resource_factor: 1,
        security_analyzer: "",
        user_consents_to_analytics: true,
      });
    });

    it("should not send the api key if its SET", async () => {
      const user = userEvent.setup();
      renderSidebar();

      const settingsButton = screen.getByTestId("settings-button");
      await user.click(settingsButton);

      const settingsModal = screen.getByTestId("ai-config-modal");

      // Click the advanced options switch to show the API key input
      const advancedOptionsSwitch = within(settingsModal).getByTestId(
        "advanced-option-switch",
      );
      await user.click(advancedOptionsSwitch);

      const apiKeyInput = within(settingsModal).getByLabelText(/API\$KEY/i);
      await user.type(apiKeyInput, "**********");

      const saveButton = within(settingsModal).getByTestId(
        "save-settings-button",
      );
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        agent: "CodeActAgent",
        confirmation_mode: false,
        enable_default_condenser: false,
        language: "en",
        llm_base_url: "",
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        remote_runtime_resource_factor: 1,
      });
    });
  });

  describe("Settings Modal", () => {
    it("should open the settings modal if the user clicks the settings button", async () => {
      const user = userEvent.setup();
      renderSidebar();

      expect(screen.queryByTestId("ai-config-modal")).not.toBeInTheDocument();

      const settingsButton = screen.getByTestId("settings-button");
      await user.click(settingsButton);

      const settingsModal = screen.getByTestId("ai-config-modal");
      expect(settingsModal).toBeInTheDocument();
    });

    it("should open the settings modal if GET /settings fails with a 404", async () => {
      const error = new AxiosError(
        "Request failed with status code 404",
        "ERR_BAD_REQUEST",
        undefined,
        undefined,
        {
          status: 404,
          statusText: "Not Found",
          data: { message: "Settings not found" },
          headers: {},
          // @ts-expect-error - we only need the response object for this test
          config: {},
        },
      );

      vi.spyOn(OpenHands, "getSettings").mockRejectedValue(error);

      renderSidebar();

      const settingsModal = await screen.findByTestId("ai-config-modal");
      expect(settingsModal).toBeInTheDocument();
    });
  });
});
