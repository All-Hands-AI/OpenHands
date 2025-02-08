import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import { AccountSettingsContextMenu } from "#/components/features/context-menu/account-settings-context-menu";

describe("AccountSettingsContextMenu", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();
  const onCloseMock = vi.fn();

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    onCloseMock.mockClear();
  });

  it("should always render the right options", () => {
    render(
      <AccountSettingsContextMenu
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn
      />,
    );

    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
    expect(screen.getByText("ACCOUNT_SETTINGS$SETTINGS")).toBeInTheDocument();
    expect(screen.getByText("ACCOUNT_SETTINGS$LOGOUT")).toBeInTheDocument();
  });

  it("should call onClickAccountSettings when the account settings option is clicked", async () => {
    render(
      <AccountSettingsContextMenu
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn
      />,
    );

    const accountSettingsOption = screen.getByText("ACCOUNT_SETTINGS$SETTINGS");
    await user.click(accountSettingsOption);

    expect(onClickAccountSettingsMock).toHaveBeenCalledOnce();
  });

  it("should call onLogout when the logout option is clicked", async () => {
    render(
      <AccountSettingsContextMenu
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn
      />,
    );

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  test("onLogout should be disabled if the user is not logged in", async () => {
    render(
      <AccountSettingsContextMenu
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn={false}
      />,
    );

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).not.toHaveBeenCalled();
  });

  it("should call onClose when clicking outside of the element", async () => {
    render(
      <AccountSettingsContextMenu
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn
      />,
    );

    const accountSettingsButton = screen.getByText("ACCOUNT_SETTINGS$SETTINGS");
    await user.click(accountSettingsButton);
    await user.click(document.body);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
