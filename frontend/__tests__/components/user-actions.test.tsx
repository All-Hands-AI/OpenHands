import { render, screen } from "@testing-library/react";
import { describe, expect, it, test, vi, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { UserActions } from "#/components/features/sidebar/user-actions";

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
  });

  it("should render", () => {
    render(<UserActions onLogout={onLogoutMock} />);

    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
  });

  it("should toggle the user menu when the user avatar is clicked", async () => {
    render(<UserActions onLogout={onLogoutMock} />);

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

  it("should call onLogout and close the menu when the logout option is clicked", async () => {
    render(
      <UserActions
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  test("logout button is always enabled", async () => {
    render(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);

    expect(onLogoutMock).toHaveBeenCalledOnce();
  });
});
