import { render, screen, within } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";
import OpenHands from "#/api/open-hands";

describe("Settings Screen", () => {
  const { handleLogoutMock } = vi.hoisted(() => ({
    handleLogoutMock: vi.fn(),
  }));
  vi.mock("#/hooks/use-app-logout", () => ({
    useAppLogout: vi.fn().mockReturnValue({ handleLogout: handleLogoutMock }),
  }));

  const RouterStub = createRoutesStub([
    {
      Component: SettingsScreen,
      path: "/settings",
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

  it("should render the navbar", async () => {
    const sectionsToInclude = ["llm", "git", "application"];
    const sectionsToExclude = ["api keys", "credits"];
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return app mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
    });

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    sectionsToInclude.forEach((section) => {
      const sectionElement = within(navbar).getByText(section, {
        exact: false, // case insensitive
      });
      expect(sectionElement).toBeInTheDocument();
    });
    sectionsToExclude.forEach((section) => {
      const sectionElement = within(navbar).queryByText(section, {
        exact: false, // case insensitive
      });
      expect(sectionElement).not.toBeInTheDocument();
    });
  });

  it("should render the saas navbar", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return app mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });
    const sectionsToInclude = ["git", "application", "credits", "api keys"];
    const sectionsToExclude = ["llm"];

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    sectionsToInclude.forEach((section) => {
      const sectionElement = within(navbar).getByText(section, {
        exact: false, // case insensitive
      });
      expect(sectionElement).toBeInTheDocument();
    });
    sectionsToExclude.forEach((section) => {
      const sectionElement = within(navbar).queryByText(section, {
        exact: false, // case insensitive
      });
      expect(sectionElement).not.toBeInTheDocument();
    });
  });
});
