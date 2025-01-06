import { screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { SettingsForm } from "#/components/shared/modals/settings/settings-form";
import OpenHands from "#/api/open-hands";

describe("SettingsForm", () => {
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
  getConfigSpy.mockResolvedValue({
    APP_MODE: "saas",
    GITHUB_CLIENT_ID: "123",
    POSTHOG_CLIENT_KEY: "123",
  });

  const RouterStub = createRoutesStub([
    {
      Component: () => (
        <SettingsForm
          settings={DEFAULT_SETTINGS}
          models={[]}
          agents={[]}
          securityAnalyzers={[]}
          onClose={() => {}}
        />
      ),
      path: "/",
    },
  ]);

  it("should not show runtime size selector by default", () => {
    renderWithProviders(<RouterStub />);
    expect(screen.queryByText("Runtime Size")).not.toBeInTheDocument();
  });

  it("should show runtime size selector when advanced options are enabled", async () => {
    renderWithProviders(<RouterStub />);
    const advancedSwitch = screen.getByRole("switch", {
      name: "SETTINGS_FORM$ADVANCED_OPTIONS_LABEL",
    });
    fireEvent.click(advancedSwitch);
    await screen.findByText("SETTINGS_FORM$RUNTIME_SIZE_LABEL");
  });
});
