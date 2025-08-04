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
    render(
      <UserActions
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
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

  it("should show context menu when user is undefined and avatar is clicked", async () => {
    render(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu SHOULD appear even when user is undefined
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should show context menu even when user has no avatar_url", async () => {
    render(<UserActions onLogout={onLogoutMock} user={{ avatar_url: "" }} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu SHOULD appear because user object exists (even with empty avatar_url)
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should be able to access logout even when no user is provided", async () => {
    render(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Logout option should be accessible even when no user is provided
    expect(
      screen.getByText("ACCOUNT_SETTINGS$LOGOUT"),
    ).toBeInTheDocument();

    // Verify logout works
    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);
    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  it("should handle user prop changing from undefined to defined", async () => {
    const { rerender } = render(<UserActions onLogout={onLogoutMock} />);

    // Initially no user - but we can still click to show the menu
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();

    // Close the menu
    await user.click(userAvatar);
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();

    // Add user prop
    rerender(
      <UserActions
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
      />,
    );

    // Component should still render correctly
    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();

    // Menu should still work with user defined
    await user.click(userAvatar);
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should handle user prop changing from defined to undefined", async () => {
    const { rerender } = render(
      <UserActions
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
      />,
    );

    // Click to open menu
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();

    // Remove user prop - menu should still be visible
    rerender(<UserActions onLogout={onLogoutMock} />);

    // Context menu should remain visible even when user becomes undefined
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();

    // Verify logout still works
    const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
    await user.click(logoutOption);
    expect(onLogoutMock).toHaveBeenCalledOnce();
  });

  it("should work with loading state and user provided", async () => {
    render(
      <UserActions
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
        isLoading={true}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should still appear even when loading
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });
});
