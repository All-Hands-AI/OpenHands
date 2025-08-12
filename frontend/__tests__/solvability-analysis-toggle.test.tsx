import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import AppSettingsScreen from "#/routes/app-settings";
import OpenHands from "#/api/open-hands";
import { MOCK_DEFAULT_USER_SETTINGS, resetTestHandlersMockSettings } from "#/mocks/handlers";

const renderAppSettingsScreen = () =>
  render(<AppSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("Solvability Analysis Toggle", () => {
  beforeEach(() => {
    // Reset the mock settings before each test
    resetTestHandlersMockSettings();
    vi.clearAllMocks();
  });

  it("should save the solvability analysis toggle state correctly", async () => {
    // Mock the API responses
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

    // Mock the initial settings with solvability analysis disabled
    getSettingsSpy.mockResolvedValueOnce({
      ...MOCK_DEFAULT_USER_SETTINGS,
      enable_solvability_analysis: false,
    });

    // Mock the config to show the solvability analysis toggle
    vi.spyOn(OpenHands, "getConfig").mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "fake-github-client-id",
      POSTHOG_CLIENT_KEY: "fake-posthog-client-key",
      STRIPE_PUBLISHABLE_KEY: "",
      FEATURE_FLAGS: {
        ENABLE_BILLING: false,
        HIDE_LLM_SETTINGS: true,
        ENABLE_JIRA: false,
        ENABLE_JIRA_DC: false,
        ENABLE_LINEAR: false,
      },
    });

    renderAppSettingsScreen();

    // Wait for the toggle to be rendered
    const toggle = await screen.findByTestId("enable-solvability-analysis-switch");
    expect(toggle).not.toBeChecked();

    // Toggle it on
    await userEvent.click(toggle);
    expect(toggle).toBeChecked();

    // Submit the form
    const submitButton = await screen.findByTestId("submit-button");
    expect(submitButton).not.toBeDisabled();
    await userEvent.click(submitButton);

    // Verify the API was called with the correct value
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          enable_solvability_analysis: true,
        }),
      );
    });

    // Mock the API to return the updated settings after saving
    getSettingsSpy.mockResolvedValueOnce({
      ...MOCK_DEFAULT_USER_SETTINGS,
      enable_solvability_analysis: true,
    });

    // Invalidate the query to force a refetch
    await waitFor(() => {
      // The toggle should stay checked after saving
      const updatedToggle = screen.getByTestId("enable-solvability-analysis-switch");
      console.log("Toggle checked state:", updatedToggle.checked);
      expect(updatedToggle).toBeChecked();
    });
  });
});
