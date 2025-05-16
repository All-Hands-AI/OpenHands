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
        onLogout={onLogoutMock}
        onClose={onCloseMock}
      />,
    );

    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
    expect(screen.getByText("ACCOUNT_SETTINGS$LOGOUT")).toBeInTheDocument();
  });

  it("should call onLogout when the logout option is clicked", async () => {
    render(
      <AccountSettingsContextMenu
        onLogout={onLogoutMock}
        onClose={onCloseMock}
      />,
    );

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  test("logout button is always enabled", async () => {
    render(
      <AccountSettingsContextMenu
        onLogout={onLogoutMock}
        onClose={onCloseMock}
      />,
    );

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  it("should call onClose when clicking outside of the element", async () => {
    render(
      <AccountSettingsContextMenu
        onLogout={onLogoutMock}
        onClose={onCloseMock}
      />,
    );

    const accountSettingsButton = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(accountSettingsButton);
    await user.click(document.body);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
