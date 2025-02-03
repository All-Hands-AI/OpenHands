import { render, screen, waitFor } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent, { UserEvent } from "@testing-library/user-event";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";
import * as AdvancedSettingsUtlls from "#/utils/has-advanced-settings-set";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";

describe("Settings Screen", () => {
  const RouterStub = createRoutesStub([
    {
      Component: SettingsScreen,
      path: "/settings",
    },
  ]);

  const renderSettingsScreen = () =>
    render(<RouterStub initialEntries={["/settings"]} />, {
      wrapper: ({ children }) => (
        <AuthProvider>
          <QueryClientProvider client={new QueryClient()}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      ),
    });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render", async () => {
    renderSettingsScreen();

    screen.getByText("Account Settings");
    screen.getByText("LLM Settings");
    screen.getByText("Reset to defaults");
    screen.getByText("Save Changes");
  });

  describe("Account Settings", () => {
    it("should render the account settings", () => {
      renderSettingsScreen();

      screen.getByTestId("github-token-input");
      screen.getByTestId("github-token-help-anchor");
      screen.getByTestId("language-input");
      screen.getByTestId("enable-analytics-switch");
    });

    it("should not render a 'Disconnect from GitHub' button if the GitHub token is not set", async () => {
      const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
      // @ts-expect-error - we don't care about the return value except for the github_token_is_set property
      getSettingsSpy.mockResolvedValue({
        github_token_is_set: false,
      });

      renderSettingsScreen();

      const button = screen.queryByText("Disconnect from GitHub");
      expect(button).not.toBeInTheDocument();
    });

    it("should render a 'Disconnect from GitHub' button if the GitHub token is set", async () => {
      const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
      // @ts-expect-error - we don't care about the return value except for the github_token_is_set property
      getSettingsSpy.mockResolvedValue({
        github_token_is_set: true,
      });

      renderSettingsScreen();
      await screen.findByText("Disconnect from GitHub");
    });

    it("should render the 'Configure GitHub Repositories' button if SaaS mode", async () => {
      const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
      });

      const { rerender } = renderSettingsScreen();

      const button = screen.queryByText("Configure GitHub Repositories");
      expect(button).not.toBeInTheDocument();

      getConfigSpy.mockResolvedValue({
        APP_MODE: "oss",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "456",
      });

      rerender(<RouterStub initialEntries={["/settings"]} />);
      await screen.findByText("Configure GitHub Repositories");
    });

    it("should not render the GitHub token input if SaaS mode", async () => {
      const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
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
  });

  describe("LLM Settings", () => {
    it("should render the basic LLM settings by default", async () => {
      renderSettingsScreen();

      screen.getByTestId("advanced-settings-switch");
      screen.getByTestId("llm-provider-input");
      screen.getByTestId("llm-model-input");
      screen.getByTestId("llm-api-key-input");
      screen.getByTestId("llm-api-key-help-anchor");
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

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
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
      screen.getByTestId("security-analyzer-input");
      screen.getByTestId("enable-confirmation-mode-switch");
    });

    describe("Advanced LLM Settings", () => {
      const toggleAdvancedSettings = async (user: UserEvent) => {
        const advancedSwitch = screen.getByTestId("advanced-settings-switch");
        await user.click(advancedSwitch);
      };

      it("should not render the runtime settings input if OSS mode", async () => {
        const user = userEvent.setup();
        const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
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
        const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
        getConfigSpy.mockResolvedValue({
          APP_MODE: "saas",
          GITHUB_CLIENT_ID: "123",
          POSTHOG_CLIENT_KEY: "456",
        });

        renderSettingsScreen();

        await toggleAdvancedSettings(user);
        screen.getByTestId("runtime-settings-input");
      });

      test("security analyzer input should only be enabled if the confirmation mode is toggled", async () => {
        const user = userEvent.setup();
        renderSettingsScreen();

        await toggleAdvancedSettings(user);

        const securityAnalyzerInput = screen.getByTestId(
          "security-analyzer-input",
        );
        expect(securityAnalyzerInput).toBeDisabled();

        const confirmationModeSwitch = screen.getByTestId(
          "enable-confirmation-mode-switch",
        );
        await user.click(confirmationModeSwitch);

        expect(securityAnalyzerInput).toBeEnabled();
      });
    });

    describe("Network Requests", () => {
      it("should have advanced settings enabled if the user previously had them enabled", async () => {
        const hasAdvancedSettingsSetSpy = vi.spyOn(
          AdvancedSettingsUtlls,
          "hasAdvancedSettingsSet",
        );
        hasAdvancedSettingsSetSpy.mockReturnValue(true);

        renderSettingsScreen();

        const advancedSwitch = screen.getByTestId("advanced-settings-switch");
        expect(advancedSwitch).toBeChecked();

        const llmCustomInput = screen.getByTestId("llm-custom-model-input");
        expect(llmCustomInput).toBeInTheDocument();
      });

      it.skip("should have the values set if the user previously had them set", async () => {
        const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
        getSettingsSpy.mockResolvedValue({
          ...MOCK_DEFAULT_USER_SETTINGS,
          language: "no",
        });

        renderSettingsScreen();

        await waitFor(() => {
          const languageInput = screen.getByTestId("language-input");
          expect(languageInput).toHaveValue("Norsk");
        });
      });

      it.todo(
        "should save the settings when the 'Save Changes' button is clicked",
      );

      it.todo(
        "should reset the settings when the 'Reset to defaults' button is clicked",
      );
    });
  });
});
