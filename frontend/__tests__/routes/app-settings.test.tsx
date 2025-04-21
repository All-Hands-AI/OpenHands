import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppSettingsScreen from "#/routes/app-settings";
import OpenHands from "#/api/open-hands";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import { AuthProvider } from "#/context/auth-context";

const renderAppSettingsScreen = () =>
  render(<AppSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    ),
  });

describe("Content", () => {
  it("should render the screen", () => {
    renderAppSettingsScreen();
    screen.getByTestId("app-settings-screen");
  });

  it("should render the inputs", async () => {
    renderAppSettingsScreen();

    await waitFor(() => {
      screen.getByTestId("language-input");
      screen.getByTestId("enable-analytics-switch");
      screen.getByTestId("enable-sound-notifications-switch");
    });
  });

  it("should render the correct default values", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      language: "no",
      user_consents_to_analytics: true,
      enable_sound_notifications: true,
    });

    renderAppSettingsScreen();

    await waitFor(() => {
      const language = screen.getByTestId("language-input");
      const analytics = screen.getByTestId("enable-analytics-switch");
      const sound = screen.getByTestId("enable-sound-notifications-switch");

      expect(language).toHaveValue("Norsk");
      expect(analytics).toBeChecked();
      expect(sound).toBeChecked();
    });
  });
});
