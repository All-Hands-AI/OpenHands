import { screen, within } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import OpenHands from "#/api/open-hands";

describe("UserBalance", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should show the current balance", async () => {
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "123",
    });
    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const balance = await screen.findByTestId("current-balance");
    expect(balance).toBeInTheDocument();

    await within(balance).findByText("$100.00");
  });

  it("should not show the current balance if not in saas mode", async () => {
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "123",
    });

    renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

    const balance = screen.queryByTestId("current-balance");
    expect(balance).not.toBeInTheDocument();
  });
});
