import { render, screen } from "@testing-library/react";
import { describe, expect, it, test, vi, afterEach, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { UserActions } from "#/components/features/sidebar/user-actions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactElement } from "react";

// Create mocks for all the hooks we need
const useIsAuthedMock = vi
  .fn()
  .mockReturnValue({ data: true, isLoading: false });

const useConfigMock = vi
  .fn()
  .mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });

const useUserProvidersMock = vi
  .fn()
  .mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

// Mock the hooks
vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => useIsAuthedMock(),
}));

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: () => useConfigMock(),
}));

vi.mock("#/hooks/use-user-providers", () => ({
  useUserProviders: () => useUserProvidersMock(),
}));

describe("UserActions", () => {
  const user = userEvent.setup();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();

  // Create a wrapper with QueryClientProvider
  const renderWithQueryClient = (ui: ReactElement) => {
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
    // Reset all mocks to default values before each test
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });
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

  it("should NOT show context menu when user is not authenticated and avatar is clicked", async () => {
    // Set isAuthed to false for this test
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });
    // Keep other mocks with default values
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

    renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should NOT appear because user is not authenticated
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();
  });

  it("should show context menu even when user has no avatar_url", async () => {
    renderWithQueryClient(
      <UserActions onLogout={onLogoutMock} user={{ avatar_url: "" }} />,
    );

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu SHOULD appear because user object exists (even with empty avatar_url)
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should NOT be able to access logout when user is not authenticated", async () => {
    // Set isAuthed to false for this test
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });
    // Keep other mocks with default values
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

    renderWithQueryClient(<UserActions onLogout={onLogoutMock} />);

    const userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);

    // Context menu should NOT appear because user is not authenticated
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();

    // Logout option should NOT be accessible when user is not authenticated
    expect(screen.queryByText("ACCOUNT_SETTINGS$LOGOUT")).not.toBeInTheDocument();
  });

  it("should handle user prop changing from undefined to defined", async () => {
    // Start with no authentication
    useIsAuthedMock.mockReturnValue({ data: false, isLoading: false });
    // Keep other mocks with default values
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

    const { rerender } = renderWithQueryClient(
      <UserActions onLogout={onLogoutMock} />,
    );

    // Initially no user and not authenticated - menu should not appear
    let userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();

    // Set authentication to true for the rerender
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });
    // Ensure config and providers are set correctly
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

    // Add user prop and create a new QueryClient to ensure fresh state
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />
      </QueryClientProvider>,
    );

    // Component should still render correctly
    expect(screen.getByTestId("user-actions")).toBeInTheDocument();
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();

    // Menu should now work with user defined and authenticated
    userAvatar = screen.getByTestId("user-avatar");
    await user.click(userAvatar);
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should handle user prop changing from defined to undefined", async () => {
    // Start with authentication and providers
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

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
    // Keep other mocks with default values
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

    // Remove user prop - menu should disappear because user is no longer authenticated
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <UserActions onLogout={onLogoutMock} />
      </QueryClientProvider>,
    );

    // Context menu should NOT be visible when user becomes unauthenticated
    expect(
      screen.queryByTestId("account-settings-context-menu"),
    ).not.toBeInTheDocument();

    // Logout option should not be accessible
    expect(screen.queryByText("ACCOUNT_SETTINGS$LOGOUT")).not.toBeInTheDocument();
  });

  it("should work with loading state and user provided", async () => {
    // Ensure authentication and providers are set correctly
    useIsAuthedMock.mockReturnValue({ data: true, isLoading: false });
    useConfigMock.mockReturnValue({ data: { APP_MODE: "saas" }, isLoading: false });
    useUserProvidersMock.mockReturnValue({ providers: [{ id: "github", name: "GitHub" }] });

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
