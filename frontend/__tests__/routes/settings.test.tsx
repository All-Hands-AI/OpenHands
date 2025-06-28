import { render, screen, within } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
      children: [
        {
          Component: () => <div data-testid="llm-settings-screen" />,
          path: "/settings",
        },
        {
          Component: () => <div data-testid="git-settings-screen" />,
          path: "/settings/integrations",
        },
        {
          Component: () => <div data-testid="application-settings-screen" />,
          path: "/settings/app",
        },
        {
          Component: () => <div data-testid="credits-settings-screen" />,
          path: "/settings/credits",
        },
        {
          Component: () => <div data-testid="api-keys-settings-screen" />,
          path: "/settings/api-keys",
        },
      ],
    },
  ]);

  const renderSettingsScreen = (path = "/settings") => {
    const queryClient = new QueryClient();
    return render(<RouterStub initialEntries={[path]} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });
  };

  it("should render the navbar", async () => {
    const sectionsToInclude = ["llm", "integrations", "application", "secrets"];
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
    const sectionsToInclude = [
      "integrations",
      "application",
      "credits",
      "secrets",
      "api keys",
    ];
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

  it("should not be able to access oss-restricted routes in oss", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return app mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
    });

    const { rerender } = renderSettingsScreen("/settings/credits");
    expect(
      screen.queryByTestId("credits-settings-screen"),
    ).not.toBeInTheDocument();

    rerender(<RouterStub initialEntries={["/settings/api-keys"]} />);
    expect(
      screen.queryByTestId("api-keys-settings-screen"),
    ).not.toBeInTheDocument();
    rerender(<RouterStub initialEntries={["/settings/billing"]} />);
    expect(
      screen.queryByTestId("billing-settings-screen"),
    ).not.toBeInTheDocument();
    rerender(<RouterStub initialEntries={["/settings"]} />);
  });

  it.todo("should not be able to access saas-restricted routes in saas");
});
