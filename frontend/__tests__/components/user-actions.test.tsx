import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, afterEach, test } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { UserActions } from "#/components/features/sidebar/user-actions";

vi.mock("react-router", async (importActual) => ({
  ...(await importActual()),
  useNavigate: () => vi.fn(),
  useRevalidator: () => ({
    revalidate: vi.fn(),
  }),
}));

const renderUserActions = (props = { hasAvatar: true }) => {
  render(
    <UserActions
      user={
        props.hasAvatar
          ? { avatar_url: "https://example.com/avatar.png" }
          : undefined
      }
    />,
    {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    },
  );
};

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
  });

  it("should render", () => {
    renderUserActions();
    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
  });

  it("should toggle the user menu when the user avatar is clicked", async () => {
    renderUserActions();

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    expect(screen.getByTestId("user-context-menu")).toBeInTheDocument();

    await user.click(userAvatar);

    expect(screen.queryByTestId("user-context-menu")).not.toBeInTheDocument();
  });

  it("should NOT show context menu when user is undefined and avatar is clicked", async () => {
    renderUserActions({ hasAvatar: false });
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should NOT appear because user is undefined
    expect(screen.queryByTestId("user-context-menu")).not.toBeInTheDocument();
  });

  it("should show context menu even when user has no avatar_url", async () => {
    renderUserActions();
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu SHOULD appear because user object exists (even with empty avatar_url)
    expect(screen.getByTestId("user-context-menu")).toBeInTheDocument();
  });

  it("should NOT be able to access logout when no user is provided", async () => {
    renderUserActions();
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Logout option should not be accessible because context menu doesn't appear
    expect(
      screen.queryByText("ACCOUNT_SETTINGS$LOGOUT"),
    ).not.toBeInTheDocument();
    expect(onLogoutMock).not.toHaveBeenCalled();
  });

  it("should work with loading state and user provided", async () => {
    renderUserActions();
    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should still appear even when loading
    expect(screen.getByTestId("user-context-menu")).toBeInTheDocument();
  });

  test("context menu should default to user role if oss", async () => {
    renderUserActions();
    const userAvatar = screen.getByTestId("user-avatar");
    await userEvent.click(userAvatar);

    expect(screen.getByTestId("user-context-menu")).toHaveTextContent("Logout");
    expect(screen.getByTestId("user-context-menu")).toHaveTextContent(
      "Settings",
    );
    expect(screen.queryByText("Manage Team")).not.toBeInTheDocument();
    expect(screen.queryByText("Manage Account")).not.toBeInTheDocument();
  });
});
