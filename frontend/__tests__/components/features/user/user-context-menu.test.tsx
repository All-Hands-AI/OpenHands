import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { UserContextMenu } from "#/components/features/user/user-context-menu";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { GetComponentPropTypes } from "#/utils/get-component-prop-types";

type UserContextMenuProps = GetComponentPropTypes<typeof UserContextMenu>;

function UserContextMenuWithRootOutlet({ type }: UserContextMenuProps) {
  return (
    <div>
      <div data-testid="root-outlet" id="root-outlet" />
      <UserContextMenu type={type} />
    </div>
  );
}

const renderUserContextMenu = ({ type }: UserContextMenuProps) =>
  render(<UserContextMenuWithRootOutlet type={type} />, {
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
    renderUserContextMenu({ type: "user" });

    screen.getByText("Logout");
    screen.getByText("Settings");

    expect(screen.queryByText("Manage Team")).not.toBeInTheDocument();
    expect(screen.queryByText("Manage Account")).not.toBeInTheDocument();
    expect(
      screen.queryByText("Create New Organization"),
    ).not.toBeInTheDocument();
  });

  it("should render additional context items when user is an admin", () => {
    renderUserContextMenu({ type: "admin" });

    screen.getByText("Manage Team");
    screen.getByText("Manage Account");

    expect(
      screen.queryByText("Create New Organization"),
    ).not.toBeInTheDocument();
  });

  it("should render additional context items when user is a super admin", () => {
    renderUserContextMenu({ type: "superadmin" });

    screen.getByText("Manage Team");
    screen.getByText("Manage Account");
    screen.getByText("Create New Organization");
  });

  it("should call the logout handler when Logout is clicked", async () => {
    const logoutSpy = vi.spyOn(OpenHands, "logout");
    renderUserContextMenu({ type: "user" });

    const logoutButton = screen.getByText("Logout");
    await userEvent.click(logoutButton);

    expect(logoutSpy).toHaveBeenCalledOnce();
  });

  it("should navigate to /settings when Settings is clicked", async () => {
    renderUserContextMenu({ type: "user" });

    const settingsButton = screen.getByText("Settings");
    await userEvent.click(settingsButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings");
  });

  it("should navigate to /settings/team when Manage Team is clicked", async () => {
    renderUserContextMenu({ type: "admin" });

    const manageTeamButton = screen.getByText("Manage Team");
    await userEvent.click(manageTeamButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings/team");
  });

  it("should navigate to /settings/org when Manage Account is clicked", async () => {
    renderUserContextMenu({ type: "admin" });

    const manageTeamButton = screen.getByText("Manage Account");
    await userEvent.click(manageTeamButton);

    expect(navigateMock).toHaveBeenCalledExactlyOnceWith("/settings/org");
  });

  describe("Create New Organization", () => {
    it("should render a modal when Create New Organization is clicked", async () => {
      renderUserContextMenu({ type: "superadmin" });

      expect(screen.queryByTestId("create-org-modal")).not.toBeInTheDocument();

      const createOrgButton = screen.getByText("Create New Organization");
      await userEvent.click(createOrgButton);

      const rootOutlet = screen.getByTestId("root-outlet");
      expect(
        within(rootOutlet).getByTestId("create-org-modal"),
      ).toBeInTheDocument();
    });

    it("should close the modal when the close button is clicked", async () => {
      renderUserContextMenu({ type: "superadmin" });

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
      renderUserContextMenu({ type: "superadmin" });

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
});
