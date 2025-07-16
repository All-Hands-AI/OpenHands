import { describe, expect, it, vi, test, beforeAll, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { userService } from "#/api/user-service/user-service.api";
import OpenHands from "#/api/open-hands";
import ManageTeam from "#/routes/manage-team";
import SettingsScreen from "#/routes/settings";
import { ORGS_AND_MEMBERS } from "#/mocks/org-handlers";

function ManageTeamWithPortalRoot() {
  return (
    <div>
      <ManageTeam />
      <div data-testid="portal-root" id="portal-root" />
    </div>
  );
}

const RouteStub = createRoutesStub([
  {
    Component: SettingsScreen,
    path: "/settings",
    children: [
      {
        Component: ManageTeamWithPortalRoot,
        path: "/settings/team",
      },
    ],
  },
]);

let queryClient: QueryClient;

const selectOrganization = async ({ orgIndex }: { orgIndex: number }) => {
  const organizationSelect = screen.getByTestId("organization-select");
  const options =
    await within(organizationSelect).findAllByTestId("org-option");
  expect(options).toHaveLength(3);

  const selectedOption = options[orgIndex];
  if (!selectedOption) {
    expect.fail(`No organization option found at index ${orgIndex}`);
  }

  await userEvent.click(selectedOption);
};

describe("Manage Team Route", () => {
  beforeAll(() => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return APP_MODE for these tests
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });
  });

  beforeEach(() => {
    queryClient = new QueryClient();
  });

  const renderManageTeam = () =>
    render(<RouteStub initialEntries={["/settings/team"]} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

  it.todo("should navigate away from the page if not saas");

  it("should allow the user to select an organization", async () => {
    const getOrganizationMembersSpy = vi.spyOn(
      organizationService,
      "getOrganizationMembers",
    );

    renderManageTeam();

    expect(getOrganizationMembersSpy).not.toHaveBeenCalled();

    await selectOrganization({ orgIndex: 0 });
    expect(getOrganizationMembersSpy).toHaveBeenCalledExactlyOnceWith({
      orgId: "1",
    });
  });

  it("should render the list of team members", async () => {
    renderManageTeam();

    await selectOrganization({ orgIndex: 0 });
    const members = ORGS_AND_MEMBERS["1"];

    const memberListItems = await screen.findAllByTestId("member-item");
    expect(memberListItems).toHaveLength(members.length);

    members.forEach((member) => {
      expect(screen.getByText(member.email)).toBeInTheDocument();
      expect(screen.getByText(member.role)).toBeInTheDocument();
    });
  });

  test("an admin should be able to change the role of a team member", async () => {
    const getUserSpy = vi.spyOn(userService, "getMe");
    const updateMemberRoleSpy = vi.spyOn(
      organizationService,
      "updateMemberRole",
    );

    getUserSpy.mockResolvedValue({
      id: "some-user-id",
      email: "user@acme.org",
      role: "admin",
      status: "active",
    });

    renderManageTeam();

    await selectOrganization({ orgIndex: 0 });

    const memberListItems = await screen.findAllByTestId("member-item");
    const userRoleMember = memberListItems[2]; // third member is "user"

    let userCombobox = within(userRoleMember).getByText(/user/i);
    expect(userCombobox).toBeInTheDocument();
    await userEvent.click(userCombobox);

    const dropdown = within(userRoleMember).getByTestId("role-dropdown");
    const adminOption = within(dropdown).getByText(/admin/i);
    expect(adminOption).toBeInTheDocument();
    await userEvent.click(adminOption);

    expect(updateMemberRoleSpy).toHaveBeenCalledExactlyOnceWith({
      userId: "3", // assuming the third member is the one being updated
      orgId: "1",
      role: "admin",
    });
    expect(
      within(userRoleMember).queryByTestId("role-dropdown"),
    ).not.toBeInTheDocument();

    // Verify the role has been updated in the UI
    userCombobox = within(userRoleMember).getByText(/admin/i);
    expect(userCombobox).toBeInTheDocument();

    // revert the role back to user
    await userEvent.click(userCombobox);
    const userOption = within(
      within(userRoleMember).getByTestId("role-dropdown"),
    ).getByText(/user/i);
    expect(userOption).toBeInTheDocument();
    await userEvent.click(userOption);

    expect(updateMemberRoleSpy).toHaveBeenNthCalledWith(2, {
      userId: "3",
      orgId: "1",
      role: "user",
    });

    // Verify the role has been reverted in the UI
    userCombobox = within(userRoleMember).getByText(/user/i);
    expect(userCombobox).toBeInTheDocument();
  });

  test("a user should not be able to change other team members' roles", async () => {
    const getUserSpy = vi.spyOn(userService, "getMe");
    const updateMemberRoleSpy = vi.spyOn(
      organizationService,
      "updateMemberRole",
    );

    getUserSpy.mockResolvedValue({
      id: "some-user-id",
      email: "user@acme.org",
      role: "user",
      status: "active",
    });

    renderManageTeam();

    await selectOrganization({ orgIndex: 0 });

    const memberListItems = await screen.findAllByTestId("member-item");
    const adminRoleMember = memberListItems[1]; // first member is "admin"

    const userCombobox = within(adminRoleMember).getByText(/admin/i);
    expect(userCombobox).toBeInTheDocument();
    await userEvent.click(userCombobox);

    // Verify that the dropdown does not open for superadmin
    expect(
      within(adminRoleMember).queryByTestId("role-dropdown"),
    ).not.toBeInTheDocument();

    expect(updateMemberRoleSpy).not.toHaveBeenCalled();
  });

  it("should not allow a user to invite a new team member", async () => {
    const getUserSpy = vi.spyOn(userService, "getMe");
    getUserSpy.mockResolvedValue({
      id: "some-user-id",
      email: "someone@acme.org",
      role: "user",
      status: "active",
    });

    renderManageTeam();

    const inviteButton = screen.queryByRole("button", {
      name: /invite team/i,
    });
    expect(inviteButton).not.toBeInTheDocument();
  });

  it("should not allow an admin to change the superadmin's role", async () => {
    const getUserSpy = vi.spyOn(userService, "getMe");
    getUserSpy.mockResolvedValue({
      id: "some-user-id",
      email: "user@acme.org",
      role: "admin",
      status: "active",
    });

    renderManageTeam();

    await selectOrganization({ orgIndex: 0 });

    const memberListItems = await screen.findAllByTestId("member-item");
    const superAdminMember = memberListItems[0]; // first member is "superadmin
    const userCombobox = within(superAdminMember).getByText(/superadmin/i);
    expect(userCombobox).toBeInTheDocument();
    await userEvent.click(userCombobox);

    // Verify that the dropdown does not open for superadmin
    expect(
      within(superAdminMember).queryByTestId("role-dropdown"),
    ).not.toBeInTheDocument();
  });

  describe("Inviting Team Members", () => {
    it("should render an invite team member button", async () => {
      renderManageTeam();

      const inviteButton = await screen.findByRole("button", {
        name: /invite team/i,
      });
      expect(inviteButton).toBeInTheDocument();
    });

    it("should render a modal when the invite button is clicked", async () => {
      renderManageTeam();

      expect(screen.queryByTestId("invite-modal")).not.toBeInTheDocument();
      const inviteButton = await screen.findByRole("button", {
        name: /invite team/i,
      });
      await userEvent.click(inviteButton);

      const portalRoot = screen.getByTestId("portal-root");
      expect(
        within(portalRoot).getByTestId("invite-modal"),
      ).toBeInTheDocument();
    });

    it("should close the modal when the close button is clicked", async () => {
      renderManageTeam();

      const inviteButton = await screen.findByRole("button", {
        name: /invite team/i,
      });
      await userEvent.click(inviteButton);

      const modal = screen.getByTestId("invite-modal");
      const closeButton = within(modal).getByRole("button", {
        name: /skip/i,
      });
      await userEvent.click(closeButton);

      expect(screen.queryByTestId("invite-modal")).not.toBeInTheDocument();
    });

    it("should render a list item in an invited state when a the user is is invited", async () => {
      const getUserSpy = vi.spyOn(userService, "getMe");
      const getOrganizationMembersSpy = vi.spyOn(
        organizationService,
        "getOrganizationMembers",
      );

      getUserSpy.mockResolvedValue({
        id: "some-user-id",
        email: "user@acme.org",
        role: "admin",
        status: "active",
      });
      getOrganizationMembersSpy.mockResolvedValue([
        {
          id: "4",
          email: "tom@acme.org",
          role: "user",
          status: "invited",
        },
      ]);

      renderManageTeam();

      await selectOrganization({ orgIndex: 0 });

      const members = await screen.findAllByTestId("member-item");
      expect(members).toHaveLength(1);

      const invitedMember = members[0];
      expect(invitedMember).toBeInTheDocument();

      // should have an "invited" badge
      const invitedBadge = within(invitedMember).getByText(/invited/i);
      expect(invitedBadge).toBeInTheDocument();

      // should not have a role combobox
      await userEvent.click(within(invitedMember).getByText(/user/i));
      expect(
        within(invitedMember).queryByTestId("role-dropdown"),
      ).not.toBeInTheDocument();
    });
  });
});
