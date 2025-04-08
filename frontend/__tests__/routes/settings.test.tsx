import { render, screen, waitFor, within } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent, { UserEvent } from "@testing-library/user-event";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";
import * as AdvancedSettingsUtlls from "#/utils/has-advanced-settings-set";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import * as ConsentHandlers from "#/utils/handle-capture-consent";
import AccountSettings from "#/routes/account-settings";
import { Provider } from "#/types/settings";

const toggleAdvancedSettings = async (user: UserEvent) => {
  const advancedSwitch = await screen.findByTestId("advanced-settings-switch");
  await user.click(advancedSwitch);
};

const mock_provider_tokens_are_set: Record<Provider, boolean> = {
  github: true,
  gitlab: false,
};

describe("Settings Screen", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
  const resetSettingsSpy = vi.spyOn(OpenHands, "resetSettings");
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
      // Use queryAllByText to handle multiple elements with the same text
      expect(screen.queryAllByText("SETTINGS$LLM_SETTINGS")).not.toHaveLength(0);
      screen.getByText("ACCOUNT_SETTINGS$ADDITIONAL_SETTINGS");
      screen.getByText("BUTTON$RESET_TO_DEFAULTS");
      screen.getByText("BUTTON$SAVE");
    });
  });

  describe("Account Settings", () => {
    beforeEach(() => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "oss",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: false,
        },
      });
    });

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

    it("should set '<hidden>' placeholder if the GitHub token is set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        provider_tokens_set: mock_provider_tokens_are_set,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("github-token-input");
        expect(input).toHaveProperty("placeholder", "<hidden>");
      });
    });

    it("should render an indicator if the GitHub token is set", async () => {
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        provider_tokens_set: mock_provider_tokens_are_set,
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

    // Tests for DISCONNECT_FROM_GITHUB button removed as the button is no longer included in main

    it("should not render the 'Configure GitHub Repositories' button if OSS mode", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "oss",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: false,
        },
      });

      renderSettingsScreen();

      const button = screen.queryByText("GITHUB$CONFIGURE_REPOS");
      expect(button).not.toBeInTheDocument();
    });

    it("should render the 'Configure GitHub Repositories' button if SaaS mode and app slug exists", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        APP_SLUG: "test-app",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: false,
        },
      });

      renderSettingsScreen();
      await screen.findByText("GITHUB$CONFIGURE_REPOS");
    });

    it("should not render the GitHub token input if SaaS mode", async () => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: false,
        },
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

      const saveButton = screen.getByText("BUTTON$SAVE");
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
    beforeEach(() => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "oss",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: false,
        },
      });
    });

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
        llm_api_key_set: true,
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

    it("should set '<hidden>' placeholder if the LLM API key is set", async () => {
      getSettingsSpy.mockResolvedValueOnce({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key_set: true,
      });

      renderSettingsScreen();

      await waitFor(() => {
        const input = screen.getByTestId("llm-api-key-input");
        expect(input).toHaveProperty("placeholder", "<hidden>");
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
          FEATURE_FLAGS: {
            ENABLE_BILLING: false,
            HIDE_LLM_SETTINGS: false,
          },
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);
        const input = screen.queryByTestId("runtime-settings-input");
        expect(input).not.toBeInTheDocument();
      });

      it.skip("should render the runtime settings input if SaaS mode", async () => {
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
          FEATURE_FLAGS: {
            ENABLE_BILLING: false,
            HIDE_LLM_SETTINGS: false,
          },
        });

        renderSettingsScreen();
        await screen.findByTestId("runtime-settings-input");
      });

      it.skip("should set the default runtime setting set", async () => {
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
          FEATURE_FLAGS: {
            ENABLE_BILLING: false,
            HIDE_LLM_SETTINGS: false,
          },
        });

        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
          remote_runtime_resource_factor: 1,
        });

        renderSettingsScreen();

        const input = await screen.findByTestId("runtime-settings-input");
        expect(input).toHaveValue("1x (2 core, 8G)");
      });

      it.skip("should always have the runtime input disabled", async () => {
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
          FEATURE_FLAGS: {
            ENABLE_BILLING: false,
            HIDE_LLM_SETTINGS: false,
          },
        });

        renderSettingsScreen();

        const input = await screen.findByTestId("runtime-settings-input");
        expect(input).toBeDisabled();
      });

      it.skip("should save the runtime settings when the 'Save Changes' button is clicked", async () => {
        const user = userEvent.setup();
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
          FEATURE_FLAGS: {
            ENABLE_BILLING: false,
            HIDE_LLM_SETTINGS: false,
          },
        });

        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
        });

        renderSettingsScreen();

        const input = await screen.findByTestId("runtime-settings-input");
        await user.click(input);

        const option = await screen.findByText("2x (4 core, 16G)");
        await user.click(option);

        const saveButton = screen.getByText("BUTTON$SAVE");
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

        const saveButton = screen.getByText("BUTTON$SAVE");
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

        getSettingsSpy.mockResolvedValueOnce({
          ...MOCK_DEFAULT_USER_SETTINGS,
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const resetButton = screen.getByText("BUTTON$RESET_TO_DEFAULTS");
        await user.click(resetButton);

        // show modal
        const modal = await screen.findByTestId("reset-modal");
        expect(modal).toBeInTheDocument();

        // Mock the settings that will be returned after reset
        // This should be the default settings with no advanced settings enabled
        getSettingsSpy.mockResolvedValueOnce({
          ...MOCK_DEFAULT_USER_SETTINGS,
          llm_base_url: "",
          confirmation_mode: false,
          security_analyzer: "",
        });

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

        const saveButton = screen.getByText("BUTTON$SAVE");
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
        user_consents_to_analytics: true,
        llm_base_url: "https://test.com",
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        agent: "CoActAgent",
        security_analyzer: "mock-invariant",
      });

      renderSettingsScreen();

      await waitFor(() => {
        expect(screen.getByTestId("language-input")).toHaveValue("Norsk");
        expect(screen.getByText("Disconnect Tokens")).toBeInTheDocument();
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

      const saveButton = screen.getByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: "", // empty because it's not set previously
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

      const saveButton = screen.getByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
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

      const resetButton = screen.getByText("BUTTON$RESET_TO_DEFAULTS");
      await user.click(resetButton);

      expect(saveSettingsSpy).not.toHaveBeenCalled();

      // show modal
      const modal = await screen.findByTestId("reset-modal");
      expect(modal).toBeInTheDocument();

      // confirm reset
      const confirmButton = within(modal).getByText("Reset");
      await user.click(confirmButton);

      await waitFor(() => {
        expect(resetSettingsSpy).toHaveBeenCalled();
      });

      // Mock the settings response after reset
      getSettingsSpy.mockResolvedValueOnce({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_base_url: "",
        confirmation_mode: false,
        security_analyzer: "",
      });

      // Wait for the mutation to complete and the modal to be removed
      await waitFor(() => {
        expect(screen.queryByTestId("reset-modal")).not.toBeInTheDocument();
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
      });
    });

    it("should cancel the reset when the 'Cancel' button is clicked", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue(MOCK_DEFAULT_USER_SETTINGS);

      renderSettingsScreen();

      const resetButton = await screen.findByText("BUTTON$RESET_TO_DEFAULTS");
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

      const saveButton = screen.getByText("BUTTON$SAVE");
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

      const saveButton = await screen.findByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(handleCaptureConsentSpy).toHaveBeenCalledWith(false);
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

      const saveButton = screen.getByText("BUTTON$SAVE");
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

      const saveButton = screen.getByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ llm_api_key: "" }),
      );
    });

    it("should not send an empty LLM API Key if the user submits an empty string but already has it set", async () => {
      const user = userEvent.setup();
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_api_key_set: true,
      });

      renderSettingsScreen();

      const input = await screen.findByTestId("llm-api-key-input");
      expect(input).toHaveValue("");

      const saveButton = screen.getByText("BUTTON$SAVE");
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

      const saveButton = screen.getByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({ llm_api_key: "new-api-key" }),
      );
    });
  });

  describe("SaaS mode", () => {
    beforeEach(() => {
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
        FEATURE_FLAGS: {
          ENABLE_BILLING: false,
          HIDE_LLM_SETTINGS: true,
        },
      });
    });

    it("should hide the entire LLM section", async () => {
      renderSettingsScreen();

      await waitFor(() => {
        screen.getByTestId("account-settings-form"); // wait for the account settings form to render

        const llmSection = screen.queryByTestId("llm-settings-section");
        expect(llmSection).not.toBeInTheDocument();
      });
    });

    it("should not render LLM Provider, LLM Model, and LLM API Key inputs", async () => {
      renderSettingsScreen();

      await waitFor(() => {
        screen.getByTestId("account-settings-form"); // wait for the account settings form to render

        const providerInput = screen.queryByTestId("llm-provider-input");
        const modelInput = screen.queryByTestId("llm-model-input");
        const apiKeyInput = screen.queryByTestId("llm-api-key-input");
        const llmApiKeyHelpAnchor = screen.queryByTestId(
          "llm-api-key-help-anchor",
        );
        const advancedSettingsSwitch = screen.queryByTestId(
          "advanced-settings-switch",
        );

        expect(providerInput).not.toBeInTheDocument();
        expect(modelInput).not.toBeInTheDocument();
        expect(apiKeyInput).not.toBeInTheDocument();
        expect(llmApiKeyHelpAnchor).not.toBeInTheDocument();
        expect(advancedSettingsSwitch).not.toBeInTheDocument();
      });
    });

    // We might want to bring this back if users wish to set advanced settings
    it.skip("should render advanced settings by default", async () => {
      renderSettingsScreen();

      await waitFor(() => {
        screen.getByTestId("account-settings-form"); // wait for the account settings form to render

        const agentInput = screen.getByTestId("agent-input"); // this is only rendered in advanced mode
        expect(agentInput).toBeInTheDocument();

        // we should not allow the user to change these fields
        const customModelInput = screen.queryByTestId("llm-custom-model-input");
        const baseUrlInput = screen.queryByTestId("base-url-input");

        expect(customModelInput).not.toBeInTheDocument();
        expect(baseUrlInput).not.toBeInTheDocument();
      });
    });

    it("should not submit the unwanted fields when saving", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      const saveButton = await screen.findByText("BUTTON$SAVE");
      await user.click(saveButton);

      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: undefined,
          llm_base_url: undefined,
          llm_model: undefined,
        }),
      );
    });

    it("should not submit the unwanted fields when resetting", async () => {
      const user = userEvent.setup();
      renderSettingsScreen();

      const resetButton = await screen.findByText("BUTTON$RESET_TO_DEFAULTS");
      await user.click(resetButton);

      const modal = await screen.findByTestId("reset-modal");
      const confirmButton = within(modal).getByText("Reset");
      await user.click(confirmButton);
      expect(saveSettingsSpy).not.toHaveBeenCalled();
      expect(resetSettingsSpy).toHaveBeenCalled();
    });
  });
});
