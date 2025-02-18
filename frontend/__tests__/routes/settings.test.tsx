import { render, screen, waitFor, within } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent, { UserEvent } from "@testing-library/user-event";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";
import * as AdvancedSettingsUtlls from "#/utils/has-advanced-settings-set";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import { PostApiSettings } from "#/types/settings";
import * as ConsentHandlers from "#/utils/handle-capture-consent";
import AccountSettings from "#/routes/account-settings";

const toggleAdvancedSettings = async (user: UserEvent) => {
  const advancedSwitch = await screen.findByTestId("advanced-settings-switch");
  await user.click(advancedSwitch);
};

describe("Settings Screen", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

  const { handleLogoutMock } = vi.hoisted(() => ({
    handleLogoutMock: vi.fn(),
  }));
  vi.mock("#/hooks/use-app-logout", () => ({
    useAppLogout: vi.fn().mockReturnValue({ handleLogout: handleLogoutMock }),
  }));

  afterEach(() => {
    vi.clearAllMocks();
  });

  const RouterStub = createRoutesStub([
    {
      Component: SettingsScreen,
      path: "/settings",
      children: [{ Component: AccountSettings, path: "/settings" }],
    },
  ]);

  const renderSettingsScreen = () => {
    const queryClient = new QueryClient();
    return render(<RouterStub initialEntries={["/settings"]} />, {
      wrapper: ({ children }) => (
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      ),
    });
  };

  it("should render", async () => {
    renderSettingsScreen();

    await waitFor(() => {
      screen.getByText("LLM Settings");
      screen.getByText("GitHub Settings");
      screen.getByText("Additional Settings");
      screen.getByText("Reset to defaults");
      screen.getByText("Save Changes");
    });
  });

  describe("Account Settings", () => {
    it("should render the account settings", async () => {
      renderSettingsScreen();

      await waitFor(() => {
        screen.getByTestId("github-token-input");
        screen.getByTestId("github-token-help-anchor");
        screen.getByTestId("language-input");
        screen.getByTestId("enable-analytics-switch");
      });
    });

    // TODO: Set a better unset indicator
    it.skip("should render an indicator if the GitHub token is not set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: false,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("github-token-input");
        const inputParent = input.parentElement;

        if (inputParent) {
          const badge = within(inputParent).getByTestId("unset-indicator");
          expect(badge).toBeInTheDocument();
        } else {
          throw new Error("GitHub token input parent not found");
        }
      });
    });

    it("should set asterik placeholder if the GitHub token is set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: true,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("github-token-input");
        expect(input).toHaveProperty("placeholder", "**********");
      });
    });

    it("should render an indicator if the GitHub token is set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: true,
      });

      renderSettingsScreen();

      const input = await screen.findByTestId("github-token-input");
      const inputParent = input.parentElement;

      if (inputParent) {
        const badge = await within(inputParent).findByTestId("set-indicator");
        expect(badge).toBeInTheDocument();
      } else {
        throw new Error("GitHub token input parent not found");
      }
    });

    it("should render a disabled 'Disconnect from GitHub' button if the GitHub token is not set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: false,
      });

      renderSettingsScreen();

      const button = await screen.findByText("Disconnect from GitHub");
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
    });

    it("should render an enabled 'Disconnect from GitHub' button if the GitHub token is set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: true,
      });

      renderSettingsScreen();
      const button = await screen.findByText("Disconnect from GitHub");
      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();

      // input should still be rendered
      const input = await screen.findByTestId("github-token-input");
      expect(input).toBeInTheDocument();
    });

    it("should logout the user when the 'Disconnect from GitHub' button is clicked", async () => {
      const user = userEvent.setup();

      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: true,
      });

      renderSettingsScreen();

      const button = await screen.findByText("Disconnect from GitHub");
      await user.click(button);

      expect(handleLogoutMock).toHaveBeenCalled();
    });

    it("should not render the 'Configure GitHub Repositories' button if OSS mode", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "oss",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
      });

      renderSettingsScreen();

      const button = screen.queryByText("Configure GitHub Repositories");
      expect(button).not.toBeInTheDocument();
    });

    it("should render the 'Configure GitHub Repositories' button if SaaS mode and app slug exists", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        APP_SLUG: "test-app",
      });

      renderSettingsScreen();
      await screen.findByText("Configure GitHub Repositories");
    });

    it("should not render the GitHub token input if SaaS mode", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.queryByTestId("github-token-input");
        const helpAnchor = screen.queryByTestId("github-token-help-anchor");

        expect(input).not.toBeInTheDocument();
        expect(helpAnchor).not.toBeInTheDocument();
      });
    });

    it.skip("should not reset LLM Provider and Model if GitHub token is invalid", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        github_token_is_set: false,
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
      });
      saveSettingsSpy.mockRejectedValueOnce(new Error("Invalid GitHub token"));

      renderSettingsScreen();

      let llmProviderInput = await screen.findByTestId("llm-provider-input");
      let llmModelInput = await screen.findByTestId("llm-model-input");

      expect(llmProviderInput).toHaveValue("Anthropic");
      expect(llmModelInput).toHaveValue("claude-3-5-sonnet-20241022");

      const input = await screen.findByTestId("github-token-input");
      await user.type(input, "invalid-token");

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      llmProviderInput = await screen.findByTestId("llm-provider-input");
      llmModelInput = await screen.findByTestId("llm-model-input");

      expect(llmProviderInput).toHaveValue("Anthropic");
      expect(llmModelInput).toHaveValue("claude-3-5-sonnet-20241022");
    });

    test("enabling advanced, enabling confirmation mode, and then disabling + enabling advanced should not render the security analyzer input", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      await toggleAdvancedSettings(user);

      const confirmationModeSwitch = await screen.findByTestId(
        "enable-confirmation-mode-switch",
      );
      await user.click(confirmationModeSwitch);

      let securityAnalyzerInput = screen.queryByTestId(
        "security-analyzer-input",
      );
      expect(securityAnalyzerInput).toBeInTheDocument();

      await toggleAdvancedSettings(user);

      securityAnalyzerInput = screen.queryByTestId("security-analyzer-input");
      expect(securityAnalyzerInput).not.toBeInTheDocument();

      await toggleAdvancedSettings(user);

      securityAnalyzerInput = screen.queryByTestId("security-analyzer-input");
      expect(securityAnalyzerInput).not.toBeInTheDocument();
    });
  });

  describe("LLM Settings", () => {
    it("should render the basic LLM settings by default", async () => {
      renderSettingsScreen();

      await waitFor(() => {
        screen.getByTestId("advanced-settings-switch");
        screen.getByTestId("llm-provider-input");
        screen.getByTestId("llm-model-input");
        screen.getByTestId("llm-api-key-input");
        screen.getByTestId("llm-api-key-help-anchor");
      });
    });

    it("should render the advanced LLM settings if the advanced switch is toggled", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      // Should not render the advanced settings by default
      expect(
        screen.queryByTestId("llm-custom-model-input"),
      ).not.toBeInTheDocument();
      expect(screen.queryByTestId("base-url-input")).not.toBeInTheDocument();
      expect(screen.queryByTestId("agent-input")).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("security-analyzer-input"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("enable-confirmation-mode-switch"),
      ).not.toBeInTheDocument();

      const advancedSwitch = await screen.findByTestId(
        "advanced-settings-switch",
      );
      await user.click(advancedSwitch);

      // Should render the advanced settings
      expect(
        screen.queryByTestId("llm-provider-input"),
      ).not.toBeInTheDocument();
      expect(screen.queryByTestId("llm-model-input")).not.toBeInTheDocument();

      screen.getByTestId("llm-custom-model-input");
      screen.getByTestId("base-url-input");
      screen.getByTestId("agent-input");

      // "Invariant" security analyzer
      screen.getByTestId("enable-confirmation-mode-switch");

      // Not rendered until the switch is toggled
      // screen.getByTestId("security-analyzer-input");
    });

    // TODO: Set a better unset indicator
    it.skip("should render an indicator if the LLM API key is not set", async () => {
      getSettingsSpy.mockResolvedValueOnce({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key: null,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("llm-api-key-input");
        const inputParent = input.parentElement;

        if (inputParent) {
          const badge = within(inputParent).getByTestId("unset-indicator");
          expect(badge).toBeInTheDocument();
        } else {
          throw new Error("LLM API Key input parent not found");
        }
      });
    });

    it("should render an indicator if the LLM API key is set", async () => {
      getSettingsSpy.mockResolvedValueOnce({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key: "**********",
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("llm-api-key-input");
        const inputParent = input.parentElement;

        if (inputParent) {
          const badge = within(inputParent).getByTestId("set-indicator");
          expect(badge).toBeInTheDocument();
        } else {
          throw new Error("LLM API Key input parent not found");
        }
      });
    });

    it("should set asterik placeholder if the LLM API key is set", async () => {
      getSettingsSpy.mockResolvedValueOnce({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key: "**********",
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("llm-api-key-input");
        expect(input).toHaveProperty("placeholder", "**********");
      });
    });

    describe("Basic Model Selector", () => {
      it("should set the provider and model", async () => {
        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
          llm_model: "anthropic/claude-3-5-sonnet-20241022",
        });

        renderSettingsScreen();

        await waitFor(() => {
          const providerInput = screen.getByTestId("llm-provider-input");
          const modelInput = screen.getByTestId("llm-model-input");

          expect(providerInput).toHaveValue("Anthropic");
          expect(modelInput).toHaveValue("claude-3-5-sonnet-20241022");
        });
      });

      it.todo("should change the model values if the provider is changed");

      it.todo("should clear the model values if the provider is cleared");
    });

    describe("Advanced LLM Settings", () => {
      it("should not render the runtime settings input if OSS mode", async () => {
        const user = userEvent.setup();
        getConfigSpy.mockResolvedValue({
          APP_MODE: "oss",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);
        const input = screen.queryByTestId("runtime-settings-input");
        expect(input).not.toBeInTheDocument();
      });

      it("should render the runtime settings input if SaaS mode", async () => {
        const user = userEvent.setup();
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);
        screen.getByTestId("runtime-settings-input");
      });

      it("should set the default runtime setting set", async () => {
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
          remote_runtime_resource_factor: 1,
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(userEvent.setup());

        const input = await screen.findByTestId("runtime-settings-input");
        expect(input).toHaveValue("1x (2 core, 8G)");
      });

      it("should always have the runtime input disabled", async () => {
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(userEvent.setup());

        const input = await screen.findByTestId("runtime-settings-input");
        expect(input).toBeDisabled();
      });

      it.skip("should save the runtime settings when the 'Save Changes' button is clicked", async () => {
        const user = userEvent.setup();
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const input = await screen.findByTestId("runtime-settings-input");
        await user.click(input);

        const option = await screen.findByText("2x (4 core, 16G)");
        await user.click(option);

        const saveButton = screen.getByText("Save Changes");
        await user.click(saveButton);

        expect(saveSettingsSpy).toHaveBeenCalledWith(
          expect.objectContaining({
            remote_runtime_resource_factor: 2,
          }),
        );
      });

      test("saving with no changes but having advanced enabled should hide the advanced items", async () => {
        const user = userEvent.setup();
        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const saveButton = screen.getByText("Save Changes");
        await user.click(saveButton);

        await waitFor(() => {
          expect(
            screen.queryByTestId("llm-custom-model-input"),
          ).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("base-url-input"),
          ).not.toBeInTheDocument();
          expect(screen.queryByTestId("agent-input")).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("security-analyzer-input"),
          ).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("enable-confirmation-mode-switch"),
          ).not.toBeInTheDocument();
        });
      });

      test("resetting settings with no changes but having advanced enabled should hide the advanced items", async () => {
        const user = userEvent.setup();
        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const resetButton = screen.getByText("Reset to defaults");
        await user.click(resetButton);

        // show modal
        const modal = await screen.findByTestId("reset-modal");
        expect(modal).toBeInTheDocument();

        // confirm reset
        const confirmButton = within(modal).getByText("Reset");
        await user.click(confirmButton);

        await waitFor(() => {
          expect(
            screen.queryByTestId("llm-custom-model-input"),
          ).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("base-url-input"),
          ).not.toBeInTheDocument();
          expect(screen.queryByTestId("agent-input")).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("security-analyzer-input"),
          ).not.toBeInTheDocument();
          expect(
            screen.queryByTestId("enable-confirmation-mode-switch"),
          ).not.toBeInTheDocument();
        });
      });

      it("should save if only confirmation mode is enabled", async () => {
        const user = userEvent.setup();
        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const confirmationModeSwitch = await screen.findByTestId(
          "enable-confirmation-mode-switch",
        );
        await user.click(confirmationModeSwitch);

        const saveButton = screen.getByText("Save Changes");
        await user.click(saveButton);

        expect(saveSettingsSpy).toHaveBeenCalledWith(
          expect.objectContaining({
            confirmation_mode: true,
          }),
        );
      });
    });

    it("should toggle advanced if user had set a custom model", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_model: "some/custom-model",
      });
      renderSettingsScreen();

      await waitFor(() => {
        const advancedSwitch = screen.getByTestId("advanced-settings-switch");
        expect(advancedSwitch).toBeChecked();

        const llmCustomInput = screen.getByTestId("llm-custom-model-input");
        expect(llmCustomInput).toBeInTheDocument();
        expect(llmCustomInput).toHaveValue("some/custom-model");
      });
    });

    it("should have advanced settings enabled if the user previously had them enabled", async () => {
      const hasAdvancedSettingsSetSpy = vi.spyOn(
        AdvancedSettingsUtlls,
        "hasAdvancedSettingsSet",
      );
      hasAdvancedSettingsSetSpy.mockReturnValue(true);

      renderSettingsScreen();

      await waitFor(() => {
        const advancedSwitch = screen.getByTestId("advanced-settings-switch");
        expect(advancedSwitch).toBeChecked();

        const llmCustomInput = screen.getByTestId("llm-custom-model-input");
        expect(llmCustomInput).toBeInTheDocument();
      });
    });

    it("should have confirmation mode enabled if the user previously had it enabled", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        confirmation_mode: true,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const confirmationModeSwitch = screen.getByTestId(
          "enable-confirmation-mode-switch",
        );
        expect(confirmationModeSwitch).toBeChecked();
      });
    });

    // FIXME: security analyzer is not found for some reason...
    it.skip("should have the values set if the user previously had them set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        language: "no",
        github_token_is_set: true,
        user_consents_to_analytics: true,
        llm_base_url: "https://test.com",
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        agent: "CoActAgent",
        security_analyzer: "mock-invariant",
      });

      renderSettingsScreen();

      await waitFor(() => {
        expect(screen.getByTestId("language-input")).toHaveValue("Norsk");
        expect(screen.getByText("Disconnect from GitHub")).toBeInTheDocument();
        expect(screen.getByTestId("enable-analytics-switch")).toBeChecked();
        expect(screen.getByTestId("advanced-settings-switch")).toBeChecked();
        expect(screen.getByTestId("base-url-input")).toHaveValue(
          "https://test.com",
        );
        expect(screen.getByTestId("llm-custom-model-input")).toHaveValue(
          "anthropic/claude-3-5-sonnet-20241022",
        );
        expect(screen.getByTestId("agent-input")).toHaveValue("CoActAgent");
        expect(
          screen.getByTestId("enable-confirmation-mode-switch"),
        ).toBeChecked();
        expect(screen.getByTestId("security-analyzer-input")).toHaveValue(
          "mock-invariant",
        );
      });
    });

    it("should save the settings when the 'Save Changes' button is clicked", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
      });

      renderSettingsScreen();

      const languageInput = await screen.findByTestId("language-input");
      await user.click(languageInput);

      const norskOption = await screen.findByText("Norsk");
      await user.click(norskOption);

      expect(languageInput).toHaveValue("Norsk");

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: "", // empty because it's not set previously
          github_token: undefined,
          language: "no",
        }),
      );
    });

    it("should properly save basic LLM model settings", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
      });

      renderSettingsScreen();

      // disable advanced mode
      const advancedSwitch = await screen.findByTestId(
        "advanced-settings-switch",
      );
      await user.click(advancedSwitch);

      const providerInput = await screen.findByTestId("llm-provider-input");
      await user.click(providerInput);

      const openaiOption = await screen.findByText("OpenAI");
      await user.click(openaiOption);

      const modelInput = await screen.findByTestId("llm-model-input");
      await user.click(modelInput);

      const gpt4Option = await screen.findByText("gpt-4o");
      await user.click(gpt4Option);

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          github_token: undefined,
          llm_api_key: "", // empty because it's not set previously
          llm_model: "openai/gpt-4o",
        }),
      );
    });

    it("should reset the settings when the 'Reset to defaults' button is clicked", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue(MOCK_DEFAULT_USER_SETTINGS);

      renderSettingsScreen();

      const languageInput = await screen.findByTestId("language-input");
      await user.click(languageInput);

      const norskOption = await screen.findByText("Norsk");
      await user.click(norskOption);

      expect(languageInput).toHaveValue("Norsk");

      const resetButton = screen.getByText("Reset to defaults");
      await user.click(resetButton);

      expect(saveSettingsSpy).not.toHaveBeenCalled();

      // show modal
      const modal = await screen.findByTestId("reset-modal");
      expect(modal).toBeInTheDocument();

      // confirm reset
      const confirmButton = within(modal).getByText("Reset");
      await user.click(confirmButton);

      const mockCopy: Partial<PostApiSettings> = {
        ...MOCK_DEFAULT_USER_SETTINGS,
      };
      delete mockCopy.github_token_is_set;
      delete mockCopy.unset_github_token;
      delete mockCopy.user_consents_to_analytics;

      expect(saveSettingsSpy).toHaveBeenCalledWith({
        ...mockCopy,
        github_token: undefined, // not set
        llm_api_key: "", // reset as well
      });
      expect(screen.queryByTestId("reset-modal")).not.toBeInTheDocument();
    });

    it("should cancel the reset when the 'Cancel' button is clicked", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue(MOCK_DEFAULT_USER_SETTINGS);

      renderSettingsScreen();

      const resetButton = await screen.findByText("Reset to defaults");
      await user.click(resetButton);

      const modal = await screen.findByTestId("reset-modal");
      expect(modal).toBeInTheDocument();

      const cancelButton = within(modal).getByText("Cancel");
      await user.click(cancelButton);

      expect(saveSettingsSpy).not.toHaveBeenCalled();
      expect(screen.queryByTestId("reset-modal")).not.toBeInTheDocument();
    });

    it("should call handleCaptureConsent with true if the save is successful", async () => {
      const user = userEvent.setup();
      const handleCaptureConsentSpy = vi.spyOn(
        ConsentHandlers,
        "handleCaptureConsent",
      );
      renderSettingsScreen();

      const analyticsConsentInput = await screen.findByTestId(
        "enable-analytics-switch",
      );

      expect(analyticsConsentInput).not.toBeChecked();
      await user.click(analyticsConsentInput);
      expect(analyticsConsentInput).toBeChecked();

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
    });

    it("should call handleCaptureConsent with false if the save is successful", async () => {
      const user = userEvent.setup();
      const handleCaptureConsentSpy = vi.spyOn(
        ConsentHandlers,
        "handleCaptureConsent",
      );
      renderSettingsScreen();

      const saveButton = await screen.findByText("Save Changes");
      await user.click(saveButton);

      expect(handleCaptureConsentSpy).toHaveBeenCalledWith(false);
    });

    it("should not reset analytics consent when resetting to defaults", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        user_consents_to_analytics: true,
      });

      renderSettingsScreen();

      const analyticsConsentInput = await screen.findByTestId(
        "enable-analytics-switch",
      );
      expect(analyticsConsentInput).toBeChecked();

      const resetButton = await screen.findByText("Reset to defaults");
      await user.click(resetButton);

      const modal = await screen.findByTestId("reset-modal");
      const confirmButton = within(modal).getByText("Reset");
      await user.click(confirmButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ user_consents_to_analytics: undefined }),
      );
    });

    it("should render the security analyzer input if the confirmation mode is enabled", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      let securityAnalyzerInput = screen.queryByTestId(
        "security-analyzer-input",
      );
      expect(securityAnalyzerInput).not.toBeInTheDocument();

      const confirmationModeSwitch = await screen.findByTestId(
        "enable-confirmation-mode-switch",
      );
      await user.click(confirmationModeSwitch);

      securityAnalyzerInput = await screen.findByTestId(
        "security-analyzer-input",
      );
      expect(securityAnalyzerInput).toBeInTheDocument();
    });

    // FIXME: localStorage isn't being set
    it.skip("should save with ENABLE_DEFAULT_CONDENSER with true if user set the feature flag in local storage", async () => {
      localStorage.setItem("ENABLE_DEFAULT_CONDENSER", "true");

      const user = userEvent.setup();
      renderSettingsScreen();

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          enable_default_condenser: true,
        }),
      );
    });

    it("should send an empty LLM API Key if the user submits an empty string", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      const input = await screen.findByTestId("llm-api-key-input");
      expect(input).toHaveValue("");

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ llm_api_key: "" }),
      );
    });

    it("should not send an empty LLM API Key if the user submits an empty string but already has it set", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key: "**********",
      });

      renderSettingsScreen();

      const input = await screen.findByTestId("llm-api-key-input");
      expect(input).toHaveValue("");

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ llm_api_key: undefined }),
      );
    });

    it("should submit the LLM API Key if it is the first time the user sets it", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      const input = await screen.findByTestId("llm-api-key-input");
      await user.type(input, "new-api-key");

      const saveButton = screen.getByText("Save Changes");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ llm_api_key: "new-api-key" }),
      );
    });
  });
});
