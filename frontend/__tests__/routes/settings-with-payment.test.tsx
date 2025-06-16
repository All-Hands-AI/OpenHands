import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRoutesStub } from "react-router";
import { renderWithProviders } from "test-utils";
import OpenHands from "#/api/open-hands";
import SettingsScreen from "#/routes/settings";
import { PaymentForm } from "#/components/features/payment/payment-form";
import * as useSettingsModule from "#/hooks/query/use-settings";

// Mock the useSettings hook
vi.mock("#/hooks/query/use-settings", async () => {
  const actual = await vi.importActual<typeof import("#/hooks/query/use-settings")>("#/hooks/query/use-settings");
  return {
    ...actual,
    useSettings: vi.fn().mockReturnValue({
      data: {
        EMAIL_VERIFIED: true, // Mock email as verified to prevent redirection
      },
      isLoading: false,
    }),
  };
});

// Mock the i18next hook
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual<typeof import("react-i18next")>("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          "SETTINGS$NAV_INTEGRATIONS": "Integrations",
          "SETTINGS$NAV_APPLICATION": "Application",
          "SETTINGS$NAV_CREDITS": "Credits",
          "SETTINGS$NAV_API_KEYS": "API Keys",
          "SETTINGS$NAV_LLM": "LLM",
          "SETTINGS$NAV_USER": "User",
          "SETTINGS$TITLE": "Settings"
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: vi.fn(),
      },
    }),
  };
});

describe("Settings Billing", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

  const RoutesStub = createRoutesStub([
    {
      Component: SettingsScreen,
      path: "/settings",
      children: [
        {
          Component: () => <PaymentForm />,
          path: "/settings/billing",
        },
        {
          Component: () => <div data-testid="git-settings-screen" />,
          path: "/settings/integrations",
        },
        {
          Component: () => <div data-testid="user-settings-screen" />,
          path: "/settings/user",
        },
      ],
    },
  ]);

  const renderSettingsScreen = () =>
    renderWithProviders(<RoutesStub initialEntries={["/settings/billing"]} />);

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should not render the credits tab if OSS mode", async () => {
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

    const navbar = await screen.findByTestId("settings-navbar");
    const credits = within(navbar).queryByText("Credits");
    expect(credits).not.toBeInTheDocument();
  });

  it("should render the credits tab if SaaS mode and billing is enabled", async () => {
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
      FEATURE_FLAGS: {
        ENABLE_BILLING: true,
        HIDE_LLM_SETTINGS: false,
      },
    });

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    within(navbar).getByText("Credits");
  });

  it("should render the billing settings if clicking the credits item", async () => {
    const user = userEvent.setup();
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
      FEATURE_FLAGS: {
        ENABLE_BILLING: true,
        HIDE_LLM_SETTINGS: false,
      },
    });

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    const credits = within(navbar).getByText("Credits");
    await user.click(credits);

    const billingSection = await screen.findByTestId("billing-settings");
    expect(billingSection).toBeInTheDocument();
  });
});
