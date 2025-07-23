import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import SettingsScreen from "#/routes/settings";
import OpenHands from "#/api/open-hands";

// Mock the i18next hook
vi.mock("react-i18next", async () => {
  const actual =
    await vi.importActual<typeof import("react-i18next")>("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          SETTINGS$NAV_INTEGRATIONS: "Integrations",
          SETTINGS$NAV_APPLICATION: "Application",
          SETTINGS$NAV_CREDITS: "Credits",
          SETTINGS$NAV_API_KEYS: "API Keys",
          SETTINGS$NAV_LLM: "LLM",
          SETTINGS$TITLE: "Settings",
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: vi.fn(),
      },
    }),
  };
});

// Mock react-router
vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet" />,
  };
});

describe("Settings Screen in SaaS Mode", () => {
  const { mockQueryClient } = vi.hoisted(() => ({
    mockQueryClient: (() => {
      const { QueryClient } = require("@tanstack/react-query");
      return new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
          },
        },
      });
    })(),
  }));

  vi.mock("#/query-client-config", () => ({
    queryClient: mockQueryClient,
  }));

  // Clear query client before test
  mockQueryClient.clear();

  it("should not render LLM settings in SaaS mode", async () => {
    // Mock SaaS mode
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only need APP_MODE for this test
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    // Set the query data directly to ensure the component sees it
    mockQueryClient.setQueryData(["config"], { APP_MODE: "saas" });

    // Set the pathname to /settings
    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        pathname: "/settings"
      },
      writable: true
    });

    // Render the settings screen directly with MemoryRouter
    render(
      <MemoryRouter initialEntries={["/settings"]}>
        <SettingsScreen />
      </MemoryRouter>,
      {
        wrapper: ({ children }) => (
          <QueryClientProvider client={mockQueryClient}>
            {children}
          </QueryClientProvider>
        ),
      }
    );

    // In SaaS mode, the outlet should not be rendered when pathname is /settings
    // This is the key fix that prevents the LLM settings from showing up
    const outlet = screen.queryByTestId("outlet");
    expect(outlet).not.toBeInTheDocument();

    // The issue is that when clicking the settings button twice in quick succession,
    // the second click might interrupt the redirect process, causing the LLM settings
    // to be shown momentarily before the useEffect redirect kicks in.
    // The fix ensures that even if the redirect is interrupted, the outlet is not rendered.

    getConfigSpy.mockRestore();
  });
});
