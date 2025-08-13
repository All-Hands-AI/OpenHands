import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import i18n from "../../src/i18n";
import { AccountSettingsContextMenu } from "../../src/components/features/context-menu/account-settings-context-menu";
import { renderWithProviders } from "../../test-utils";
import { MemoryRouter } from "react-router";

describe("Translations", () => {
  it("should render translated text", () => {
    i18n.changeLanguage("en");
    renderWithProviders(
      <MemoryRouter>
        <AccountSettingsContextMenu onLogout={() => {}} onClose={() => {}} />
      </MemoryRouter>,
    );
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });
});
