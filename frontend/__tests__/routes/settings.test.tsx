import { render, screen, waitFor } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";

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
        expect(input).not.toBeInTheDocument();
      });
    });
  });

  describe("LLM Settings", () => {
    it("should render the basic LLM settings by default", async () => {
      renderSettingsScreen();

      screen.getByTestId("llm-provider-input");
      screen.getByTestId("llm-model-input");
      screen.getByTestId("llm-api-key-input");
    });

    it.todo(
      "should render the advanced LLM settings if the advanced switch is toggled",
    );
  });
});
