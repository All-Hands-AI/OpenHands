import { render, screen } from "@testing-library/react";
import { describe, expect, it, test, vi, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import React from "react";
import { UserAvatar } from "#/components/user-avatar";
import { AccountSettingsContextMenu } from "#/components/context-menu/account-settings-context-menu";

interface UserActionsProps {
  onClickAccountSettings: () => void;
  onLogout: () => void;
  user?: { avatar_url: string };
}

function UserActions({
  onClickAccountSettings,
  onLogout,
  user,
}: UserActionsProps) {
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  const toggleAccountMenu = () => {
    setAccountContextMenuIsVisible((prev) => !prev);
  };

  const closeAccountMenu = () => {
    setAccountContextMenuIsVisible(false);
  };

  const handleClickAccountSettings = () => {
    onClickAccountSettings();
    closeAccountMenu();
  };

  const handleLogout = () => {
    onLogout();
    closeAccountMenu();
  };

  return (
    <div data-testid="user-actions" className="w-8 h-8 relative">
      <UserAvatar avatarUrl={user?.avatar_url} onClick={toggleAccountMenu} />

      {accountContextMenuIsVisible && (
        <AccountSettingsContextMenu
          isLoggedIn={!!user}
          onClickAccountSettings={handleClickAccountSettings}
          onLogout={handleLogout}
          onClose={closeAccountMenu}
        />
      )}
    </div>
  );
}

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
  });

  it("should render", () => {
    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
      />,
    );

    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
  });

  it("should toggle the user menu when the user avatar is clicked", async () => {
    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();

    await user.click(userAvatar);

    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should call onClickAccountSettings and close the menu when the account settings option is clicked", async () => {
    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    const accountSettingsOption = screen.getByText("Account Settings");
    await user.click(accountSettingsOption);

    expect(onClickAccountSettingsMock).toHaveBeenCalledOnce();
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should call onLogout and close the menu when the logout option is clicked", async () => {
    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    const logoutOption = screen.getByText("Logout");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  test("onLogout should not be called when the user is not logged in", async () => {
    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    const logoutOption = screen.getByText("Logout");
    await user.click(logoutOption);

    expect(onLogoutMock).not.toHaveBeenCalled();
  });
});
