import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import { AccountSettingsContextMenu } from "#/components/features/context-menu/account-settings-context-menu";

const mockRef = { current: null };
let clickListener: ((event: MouseEvent) => void) | null = null;

vi.mock("#/hooks/use-click-outside-element", () => ({
  useClickOutsideElement: (callback: () => void) => {
    const handleClickOutside = (event: MouseEvent) => {
      if (event.target === document.body && mockRef.current) {
        callback();
      }
    };

    if (clickListener) {
      document.removeEventListener("click", clickListener);
    }
    clickListener = handleClickOutside;
    document.addEventListener("click", handleClickOutside);

    return mockRef;
  },
}));

describe("AccountSettingsContextMenu", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();
  const onCloseMock = vi.fn();

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    onCloseMock.mockClear();
    mockRef.current = null;
    if (clickListener) {
      document.removeEventListener("click", clickListener);
      clickListener = null;
    }
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
    expect(screen.getByText("Account Settings")).toBeInTheDocument();
    expect(screen.getByText("Logout")).toBeInTheDocument();
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

    const accountSettingsOption = screen.getByText("Account Settings");
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

    const logoutOption = screen.getByText("Logout");
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

    const logoutOption = screen.getByText("Logout");
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

    mockRef.current = screen.getByTestId("account-settings-context-menu");
    await user.click(document.body);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
