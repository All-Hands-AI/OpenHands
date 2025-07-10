import { within, screen, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { InviteOrganizationMemberModal } from "#/components/features/org/invite-organization-member-modal";

const renderInviteOrganizationMemberModal = (config?: {
  onClose: () => void;
}) =>
  render(
    <InviteOrganizationMemberModal onClose={config?.onClose || vi.fn()} />,
    {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    },
  );

describe("InviteOrganizationMemberModal", () => {
  it("should call onClose the modal when the close button is clicked", async () => {
    const onCloseMock = vi.fn();
    renderInviteOrganizationMemberModal({ onClose: onCloseMock });

    const modal = screen.getByTestId("invite-modal");
    const closeButton = within(modal).getByRole("button", {
      name: /skip/i,
    });
    await userEvent.click(closeButton);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });

  it("should call the API to invite a new team member when the form is submitted (and pop a toast)", async () => {
    const inviteMemberSpy = vi.spyOn(organizationService, "inviteMember");
    const onCloseMock = vi.fn();

    renderInviteOrganizationMemberModal({ onClose: onCloseMock });

    const modal = screen.getByTestId("invite-modal");

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

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
