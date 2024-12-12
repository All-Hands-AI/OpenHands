import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AccountSettingsContextMenu } from "#/components/features/context-menu/account-settings-context-menu";
import { useConfig } from "#/hooks/query/use-config";

describe("AccountSettingsContextMenu", () => {
  const queryClient = new QueryClient();
  const user = userEvent.setup();
  const onClickAddMoreRepositories = vi.fn();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();
  const onCloseMock = vi.fn();

  afterEach(() => {
    onClickAddMoreRepositories.mockClear();
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    onCloseMock.mockClear();
  });

  const renderWithQueryClient = (component: React.ReactNode) => {
    render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>,
    );
  };

  it("should always render the right options", () => {
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
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
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
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
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
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
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
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
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
        onClickAccountSettings={onClickAccountSettingsMock}
        onLogout={onLogoutMock}
        onClose={onCloseMock}
        isLoggedIn
      />,
    );

    const accountSettingsButton = screen.getByText("Account Settings");
    await user.click(accountSettingsButton);
    await user.click(document.body);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});

describe("AccountSettingsContextMenu", () => {
  const queryClient = new QueryClient();
  const user = userEvent.setup();
  const onClickAddMoreRepositories = vi.fn();
  const onClickAccountSettingsMock = vi.fn();
  const onLogoutMock = vi.fn();
  const onCloseMock = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();

    vi.mock("#/api/open-hands", async (importActual) => ({
      ...(await importActual<typeof import("#/api/open-hands")>()),
      getConfig: vi.fn().mockResolvedValue({
        APP_MODE: "standard",
      }),
    }));
  });

  afterEach(() => {
    onClickAddMoreRepositories.mockClear();
    onClickAccountSettingsMock.mockClear();
    onLogoutMock.mockClear();
    onCloseMock.mockClear();
  });

  const renderWithQueryClient = (component: React.ReactNode) => {
    render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>,
    );
  };

  it("should render 'Add More Repositories' when APP_MODE is 'saas'", () => {
    renderWithQueryClient(
      <AccountSettingsContextMenu
        onAddMoreRepositories={onClickAddMoreRepositories}
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
});
