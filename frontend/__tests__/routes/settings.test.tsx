import { render, screen, within } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "#/context/auth-context";
import SettingsScreen from "#/routes/settings";

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
    const sections = ["llm", "git", "application"];

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    sections.forEach((section) => {
      const sectionElement = within(navbar).getByText(section, {
        exact: false, // case insensitive
      });
      expect(sectionElement).toBeInTheDocument();
    });
  });
});
