import { render, screen, waitFor } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import AccountSettings from "#/routes/account-settings";

describe("Personality Settings", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
  const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

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

  it("should render the personality dropdown", async () => {
    renderSettingsScreen();

    await waitFor(() => {
      const personalityInput = screen.getByTestId("personality-input");
      expect(personalityInput).toBeInTheDocument();
    });
  });

  it("should set the default personality to empty", async () => {
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      PERSONALITY: null,
    });

    renderSettingsScreen();

    await waitFor(() => {
      const personalityInput = screen.getByTestId("personality-input");
      expect(personalityInput).toHaveValue("Default");
    });
  });

  it("should set the personality value from settings", async () => {
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      PERSONALITY: "enthusiastic",
    });

    renderSettingsScreen();

    await waitFor(() => {
      const personalityInput = screen.getByTestId("personality-input");
      expect(personalityInput).toHaveValue("Enthusiastic");
    });
  });

  it("should save the personality setting when the form is submitted", async () => {
    const user = userEvent.setup();
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      PERSONALITY: null,
    });

    renderSettingsScreen();

    // Find the personality dropdown
    const personalityInput = await screen.findByTestId("personality-input");
    
    // Click to open the dropdown
    await user.click(personalityInput);
    
    // Find and click the "Funny" option
    const funnyOption = await screen.findByText("Funny");
    await user.click(funnyOption);
    
    // Click the save button
    const saveButton = screen.getByText("Save Changes");
    await user.click(saveButton);
    
    // Verify the settings were saved with the correct personality
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          PERSONALITY: "funny",
        })
      );
    });
  });
});