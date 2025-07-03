import { describe, expect, it, vi, test, beforeAll } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { INITIAL_MOCK_ORG_MEMBERS } from "#/mocks/org-handlers";
import { userService } from "#/api/user-service/user-service.api";
import OpenHands from "#/api/open-hands";
import ManageTeam from "#/routes/manage-team";

function ManageTeamWithPortalRoot() {
  return (
    <div>
      <ManageTeam />
      <div data-testid="portal-root" id="portal-root" />
    </div>
  );
}

const renderManageTeam = () =>
  render(<ManageTeamWithPortalRoot />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("Manage Team Route", () => {
  beforeAll(() => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return APP_MODE for these tests
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });
  });

  it.todo("should navigate away from the page if not saas");
  it.todo("should not allow an admin to change the superadmin's role");
  it.todo("should have a 'me' badge for the current user");

  it("should render the list of team members", async () => {
    const getOrganizationMembersSpy = vi.spyOn(
      organizationService,
      "getOrganizationMembers",
    );

    renderManageTeam();
    expect(getOrganizationMembersSpy).toHaveBeenCalledOnce();

    const memberListItems = await screen.findAllByTestId("member-item");
    expect(memberListItems).toHaveLength(INITIAL_MOCK_ORG_MEMBERS.length);

    INITIAL_MOCK_ORG_MEMBERS.forEach((member) => {
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

  describe("Inviting Team Members", () => {
    it("should render an invite team member button", () => {
      renderManageTeam();

      const inviteButton = screen.getByRole("button", {
        name: /invite team/i,
      });
      expect(inviteButton).toBeInTheDocument();
    });

    it("should render a modal when the invite button is clicked", async () => {
      renderManageTeam();

      expect(screen.queryByTestId("invite-modal")).not.toBeInTheDocument();
      const inviteButton = screen.getByRole("button", {
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

      const inviteButton = screen.getByRole("button", {
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

    it("should call the API to invite a new team member when the form is submitted (and pop a toast)", async () => {
      const inviteMemberSpy = vi.spyOn(organizationService, "inviteMember");

      renderManageTeam();

      const inviteButton = screen.getByRole("button", {
        name: /invite team/i,
      });
      await userEvent.click(inviteButton);

      const modal = screen.getByTestId("invite-modal");
      expect(modal).toBeInTheDocument();

      const emailInput = within(modal).getByTestId("email-input");
      await userEvent.type(emailInput, "someone@acme.org");
      expect(emailInput).toHaveValue("someone@acme.org");

      const submitButton = within(modal).getByRole("button", {
        name: /next/i,
      });
      await userEvent.click(submitButton);

      expect(inviteMemberSpy).toHaveBeenCalledExactlyOnceWith({
        email: "someone@acme.org",
      });
      expect(screen.queryByTestId("invite-modal")).not.toBeInTheDocument();
      expect(screen.getAllByTestId("member-item")).toHaveLength(
        INITIAL_MOCK_ORG_MEMBERS.length + 1,
      );
      expect(screen.getByText("someone@acme.org")).toBeInTheDocument();

      // TODO - verify that a toast is shown
    });
  });
});
