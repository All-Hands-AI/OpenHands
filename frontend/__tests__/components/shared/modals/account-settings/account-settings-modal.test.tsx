import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import OpenHands from "#/api/open-hands";

describe("AccountSettingsModal", () => {
  describe("Billing", () => {
    it("should show the current balance", async () => {
      const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
      getConfigSpy.mockResolvedValue({
        APP_MODE: "saas",
        GITHUB_CLIENT_ID: "123",
        POSTHOG_CLIENT_KEY: "123",
      });

      renderWithProviders(<AccountSettingsModal onClose={() => {}} />);

      const balance = await screen.findByTestId("current-balance");
      expect(balance).toBeInTheDocument();

      await within(balance).findByText("$12.34");
    });

    it("should not show the current balance if not in saas mode", async () => {
      const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
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
});
