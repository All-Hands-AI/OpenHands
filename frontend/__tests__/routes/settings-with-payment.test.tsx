import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRoutesStub } from "react-router";
import { renderWithProviders } from "test-utils";
import OpenHands from "#/api/open-hands";
import SettingsScreen from "#/routes/settings";
import { PaymentForm } from "#/components/features/payment/payment-form";
import * as FeatureFlags from "#/utils/feature-flags";

describe("Settings Billing", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
  vi.spyOn(FeatureFlags, "BILLING_SETTINGS").mockReturnValue(true);

  const RoutesStub = createRoutesStub([
    {
      Component: SettingsScreen,
      path: "/settings",
      children: [
        {
          Component: () => <PaymentForm />,
          path: "/settings/billing",
        },
      ],
    },
  ]);

  const renderSettingsScreen = () =>
    renderWithProviders(<RoutesStub initialEntries={["/settings"]} />);

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should not render the navbar if OSS mode", async () => {
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
    });

    renderSettingsScreen();

    await waitFor(() => {
      const navbar = screen.queryByTestId("settings-navbar");
      expect(navbar).not.toBeInTheDocument();
    });
  });

  it("should render the navbar if SaaS mode", async () => {
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
    });

    renderSettingsScreen();

    await waitFor(() => {
      const navbar = screen.getByTestId("settings-navbar");
      within(navbar).getByText("Account");
      within(navbar).getByText("Credits");
    });
  });

  it("should render the billing settings if clicking the credits item", async () => {
    const user = userEvent.setup();
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
    });

    renderSettingsScreen();

    const navbar = await screen.findByTestId("settings-navbar");
    const credits = within(navbar).getByText("Credits");
    await user.click(credits);

    const billingSection = await screen.findByTestId("billing-settings");
    within(billingSection).getByText("Manage Credits");
  });
});
