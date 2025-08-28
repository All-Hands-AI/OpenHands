import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import { AccountSettingsContextMenu } from "#/components/features/context-menu/account-settings-context-menu";
import { MemoryRouter } from "react-router";
import { renderWithProviders } from "../../../test-utils";

describe("AccountSettingsContextMenu", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  // Create a wrapper with MemoryRouter and renderWithProviders
  const renderWithRouter = (ui: React.ReactElement) => {
    return renderWithProviders(<MemoryRouter>{ui}</MemoryRouter>);
  };

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
  });

  it("should always render the right options", () => {
    renderWithRouter(<AccountSettingsContextMenu onLogout={onLogoutMock} />);

    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
    expect(screen.getByText("ACCOUNT_SETTINGS$LOGOUT")).toBeInTheDocument();
  });

  it("should call onLogout when the logout option is clicked", async () => {
    renderWithRouter(<AccountSettingsContextMenu onLogout={onLogoutMock} />);

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  test("logout button is always enabled", async () => {
    renderWithRouter(<AccountSettingsContextMenu onLogout={onLogoutMock} />);

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });
});
