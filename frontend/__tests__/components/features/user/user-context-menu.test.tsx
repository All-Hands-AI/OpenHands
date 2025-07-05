import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { UserContextMenu } from "#/components/features/user/user-context-menu";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { GetComponentPropTypes } from "#/utils/get-component-prop-types";

type UserContextMenuProps = GetComponentPropTypes<typeof UserContextMenu>;

function UserContextMenuWithRootOutlet({
  type,
  onClose,
}: UserContextMenuProps) {
  return (
    <div>
      <div data-testid="root-outlet" id="root-outlet" />
      <UserContextMenu type={type} onClose={onClose} />
    </div>
  );
}

const renderUserContextMenu = ({ type, onClose }: UserContextMenuProps) =>
  render(<UserContextMenuWithRootOutlet type={type} onClose={onClose} />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

const { navigateMock } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
}));

vi.mock("react-router", async (importActual) => ({
  ...(await importActual()),
  useNavigate: () => navigateMock,
}));

describe("UserContextMenu", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the default context items for a user", () => {
    renderUserContextMenu({ type: "user", onClose: vi.fn });

    screen.getByText("Logout");
    screen.getByText("Settings");

    expect(screen.queryByText("Manage Team")).not.toBeInTheDocument();
    expect(screen.queryByText("Manage Account")).not.toBeInTheDocument();
    expect(
      screen.queryByText("Create New Organization"),
    ).not.toBeInTheDocument();
  });

  it("should render additional context items when user is an admin", () => {
    renderUserContextMenu({ type: "admin", onClose: vi.fn });

    screen.getByText("Manage Team");
    screen.getByText("Manage Account");

    expect(
      screen.queryByText("Create New Organization"),
    ).not.toBeInTheDocument();
  });

  it("should render additional context items when user is a super admin", () => {
    renderUserContextMenu({ type: "superadmin", onClose: vi.fn });

    screen.getByText("Manage Team");
    screen.getByText("Manage Account");
    screen.getByText("Create New Organization");
  });

  it("should call the logout handler when Logout is clicked", async () => {
    const logoutSpy = vi.spyOn(OpenHands, "logout");
    renderUserContextMenu({ type: "user", onClose: vi.fn });

    const logoutButton = screen.getByText("Logout");
    await userEvent.click(logoutButton);

    expect(logoutSpy).toHaveBeenCalledOnce();
  });

  it("should navigate to /settings when Settings is clicked", async () => {
    renderUserContextMenu({ type: "user", onClose: vi.fn });

    const settingsButton = screen.getByText("Settings");
    await userEvent.click(settingsButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings");
  });

  it("should navigate to /settings/team when Manage Team is clicked", async () => {
    renderUserContextMenu({ type: "admin", onClose: vi.fn });

    const manageTeamButton = screen.getByText("Manage Team");
    await userEvent.click(manageTeamButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings/team");
  });

  it("should navigate to /settings/org when Manage Account is clicked", async () => {
    renderUserContextMenu({ type: "admin", onClose: vi.fn });

    const manageTeamButton = screen.getByText("Manage Account");
    await userEvent.click(manageTeamButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings/org");
  });

  describe("Create New Organization", () => {
    it("should render a modal when Create New Organization is clicked", async () => {
      renderUserContextMenu({ type: "superadmin", onClose: vi.fn });

      expect(screen.queryByTestId("create-org-modal")).not.toBeInTheDocument();

      const createOrgButton = screen.getByText("Create New Organization");
      await userEvent.click(createOrgButton);

      const rootOutlet = screen.getByTestId("root-outlet");
      expect(
        within(rootOutlet).getByTestId("create-org-modal"),
      ).toBeInTheDocument();
    });

    it("should close the modal when the close button is clicked", async () => {
      renderUserContextMenu({ type: "superadmin", onClose: vi.fn });

      const createOrgButton = screen.getByText("Create New Organization");
      await userEvent.click(createOrgButton);

      expect(screen.getByTestId("create-org-modal")).toBeInTheDocument();

      // Simulate closing the modal
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      expect(screen.queryByTestId("create-org-modal")).not.toBeInTheDocument();
    });

    it("should call the API to create a new organization when the form is submitted", async () => {
      const createOrgSpy = vi.spyOn(organizationService, "createOrganization");
      renderUserContextMenu({ type: "superadmin", onClose: vi.fn });

      const createOrgButton = screen.getByText("Create New Organization");
      await userEvent.click(createOrgButton);

      expect(screen.getByTestId("create-org-modal")).toBeInTheDocument();

      const orgNameInput = screen.getByTestId("org-name-input");
      await userEvent.type(orgNameInput, "New Organization");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      expect(createOrgSpy).toHaveBeenCalledExactlyOnceWith({
        name: "New Organization",
      });
    });
  });

  it("should call the onClose handler when clicking outside the context menu", async () => {
    const onCloseMock = vi.fn();
    renderUserContextMenu({ type: "user", onClose: onCloseMock });

    const contextMenu = screen.getByTestId("user-context-menu");
    await userEvent.click(contextMenu);

    expect(onCloseMock).not.toHaveBeenCalled();

    // Simulate clicking outside the context menu
    await userEvent.click(document.body);

    expect(onCloseMock).toHaveBeenCalled();
  });

  it("should call the onClose handler after each action", async () => {
    const onCloseMock = vi.fn();
    renderUserContextMenu({ type: "superadmin", onClose: onCloseMock });

    const logoutButton = screen.getByText("Logout");
    await userEvent.click(logoutButton);
    expect(onCloseMock).toHaveBeenCalledTimes(1);

    const settingsButton = screen.getByText("Settings");
    await userEvent.click(settingsButton);
    expect(onCloseMock).toHaveBeenCalledTimes(2);

    const manageTeamButton = screen.getByText("Manage Team");
    await userEvent.click(manageTeamButton);
    expect(onCloseMock).toHaveBeenCalledTimes(3);

    const manageAccountButton = screen.getByText("Manage Account");
    await userEvent.click(manageAccountButton);
    expect(onCloseMock).toHaveBeenCalledTimes(4);

    const createOrgButton = screen.getByText("Create New Organization");
    await userEvent.click(createOrgButton);
    expect(onCloseMock).toHaveBeenCalledTimes(5);
  });
});
