import { render, screen } from "@testing-library/react";
import { describe, expect, it, test, vi, afterEach, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { UserActions } from "#/components/features/sidebar/user-actions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Create a mock for useIsAuthed that we can control per test
const useIsAuthedMock = vi.fn().mockReturnValue({ data: true, isLoading: false });

// Mock the useIsAuthed hook
vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => useIsAuthedMock(),
}));

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  // Create a wrapper with QueryClientProvider
  const renderWithQueryClient = (ui) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    return render(ui, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });
  };

  beforeEach(() => {
    // Reset the mock to default value before each test
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });
  });

  afterEach(() => {
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    vi.clearAllMocks();
  });

  it("should render", () => {
    renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
  });

  it("should toggle the user menu when the user avatar is clicked", async () => {
    renderWithQueryClient(
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
    renderWithQueryClient(
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

  it("should NOT show context menu when user is undefined and avatar is clicked", async () => {
    // Set isAuthed to false for this test
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });

    renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should NOT appear because user is undefined and not authenticated
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should show context menu even when user has no avatar_url", async () => {
    renderWithQueryClient(<UserActions onLogout={onLogoutMock} user={{ avatar_url: "" }} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu SHOULD appear because user object exists (even with empty avatar_url)
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should NOT be able to access logout when no user is provided", async () => {
    // Set isAuthed to false for this test
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });

    renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Logout option should not be accessible because context menu doesn't appear
    expect(
      screen.queryByText("ACCOUNT_SETTINGS$LOGOUT"),
    ).not.toBeInTheDocument();
    expect(onLogoutMock).not.toHaveBeenCalled();
  });

  it("should handle user prop changing from undefined to defined", () => {
    // Start with no authentication
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });

    const { rerender } = renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    // Initially no user - context menu shouldn't work
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();

    // Set authentication to true for the rerender
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });

    // Add user prop
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />
      </QueryClientProvider>
    );

    // Component should still render correctly
    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
  });

  it("should handle user prop changing from defined to undefined", async () => {
    const { rerender } = renderWithQueryClient(
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

    // Set authentication to false for the rerender
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });

    // Remove user prop - menu should disappear
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <UserActions onLogout={onLogoutMock} />
      </QueryClientProvider>
    );

    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should work with loading state and user provided", async () => {
    renderWithQueryClient(
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
