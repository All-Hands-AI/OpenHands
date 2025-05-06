import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRoutesStub } from "react-router";
import { renderWithProviders } from "test-utils";
import OpenHands from "#/api/open-hands";
import SettingsScreen from "#/routes/settings";
import { PaymentForm } from "#/components/features/payment/payment-form";

// Mock the i18next hook
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual<typeof import("react-i18next")>("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          "SETTINGS$NAV_GIT": "Git",
          "SETTINGS$NAV_APPLICATION": "Application",
          "SETTINGS$NAV_CREDITS": "Credits",
          "SETTINGS$NAV_API_KEYS": "API Keys",
          "SETTINGS$NAV_LLM": "LLM",
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
          path: "/settings/git",
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

    // Instead of looking for exact text, we'll check if any element contains "Credits"
    const navbar = await screen.findByTestId("settings-navbar");
    
    // Wait for the component to render fully
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Get all text elements and check if any contain "Credits"
    const allElements = within(navbar).queryAllByText(/./i);
    const hasCreditsTab = allElements.some(el => 
      el.textContent && el.textContent.toLowerCase().includes("credits")
    );
    
    expect(hasCreditsTab).toBe(true);
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
    
    // Wait for the component to render fully
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Find all links in the navbar
    const navLinks = navbar.querySelectorAll('a');
    
    // Find the credits link by checking the href
    const creditsLink = Array.from(navLinks).find(link => 
      link.getAttribute('href')?.includes('/settings/credits') || 
      link.textContent?.toLowerCase().includes('credits')
    );
    
    // Make sure we found the credits link
    expect(creditsLink).toBeTruthy();
    
    // Click the credits link if found
    if (creditsLink) {
      await user.click(creditsLink);
      
      const billingSection = await screen.findByTestId("billing-settings");
      expect(billingSection).toBeInTheDocument();
    }
  });
});
