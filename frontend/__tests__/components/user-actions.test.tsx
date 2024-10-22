import { render, screen } from "@testing-library/react";
import { describe, expect, it, test, vi, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
import * as Remix from "@remix-run/react";
import { UserActions } from "#/components/user-actions";

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  const useFetcherSpy = vi.spyOn(Remix, "useFetcher");
  // @ts-expect-error - Only returning the relevant properties for the test
  useFetcherSpy.mockReturnValue({ state: "idle" });

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    useFetcherSpy.mockClear();
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

  it("should display the loading spinner", () => {
    // @ts-expect-error - Only returning the relevant properties for the test
    useFetcherSpy.mockReturnValue({ state: "loading" });

    render(
      <UserActions
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        user={{ avatar_url: "https://example.com/avatar.png" }}
      />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    user.click(userAvatar);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(screen.queryByAltText("user avatar")).not.toBeInTheDocument();
  });
});
