import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";
import OpenHands from "#/api/open-hands";
import { MOCK_USER_PREFERENCES } from "#/mocks/handlers";

const renderSidebar = () => {
  const RouterStub = createRoutesStub([
    {
      path: "/conversation/:conversationId",
      Component: Sidebar,
    },
  ]);

  renderWithProviders(<RouterStub initialEntries={["/conversation/123"]} />);
};

describe("Sidebar", () => {
  it.skipIf(!MULTI_CONVERSATION_UI)(
    "should have the conversation panel open by default",
    () => {
      renderSidebar();
      expect(screen.getByTestId("conversation-panel")).toBeInTheDocument();
    },
  );

  it.skipIf(!MULTI_CONVERSATION_UI)(
    "should toggle the conversation panel",
    async () => {
      const user = userEvent.setup();
      renderSidebar();

      const projectPanelButton = screen.getByTestId(
        "toggle-conversation-panel",
      );

      await user.click(projectPanelButton);

      expect(
        screen.queryByTestId("conversation-panel"),
      ).not.toBeInTheDocument();
    },
  );

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
        ...MOCK_USER_PREFERENCES.settings,
        // the actual values are falsey (null or "") but we're checking for undefined
        llm_api_key: undefined,
        llm_base_url: undefined,
        security_analyzer: undefined,
      });
    });

    it("should send all settings data when saving account settings", async () => {
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
      const saveButton =
        within(accountSettingsModal).getByTestId("save-settings");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        ...MOCK_USER_PREFERENCES.settings,
        llm_api_key: undefined, // null or undefined
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

      const saveButton =
        within(accountSettingsModal).getByTestId("save-settings");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        ...MOCK_USER_PREFERENCES.settings,
        language: "no",
        llm_api_key: undefined, // null or undefined
      });
    });

    it("should not send the api key if its SET", async () => {
      const user = userEvent.setup();
      renderSidebar();

      const settingsButton = screen.getByTestId("settings-button");
      await user.click(settingsButton);

      const settingsModal = screen.getByTestId("ai-config-modal");

      // Click the advanced options switch to show the API key input
      const advancedOptionsSwitch = within(settingsModal).getByTestId("advanced-option-switch");
      await user.click(advancedOptionsSwitch);

      const apiKeyInput = within(settingsModal).getByLabelText(/API\$KEY/i);
      await user.type(apiKeyInput, "SET");

      const saveButton = within(settingsModal).getByTestId(
        "save-settings-button",
      );
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        ...MOCK_USER_PREFERENCES.settings,
        llm_api_key: undefined,
        llm_base_url: "",
        security_analyzer: undefined,
      });
    });
  });
});
