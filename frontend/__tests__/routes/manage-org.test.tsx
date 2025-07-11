import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import OpenHands from "#/api/open-hands";
import ManageOrg from "#/routes/manage-org";

vi.mock("#/context/use-selected-organization", () => ({
  useSelectedOrganizationId: vi.fn(() => ({
    orgId: "1",
    setOrgId: vi.fn(),
  })),
}));

const renderManageOrg = () =>
  render(<ManageOrg />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("Manage Org Route", () => {
  it.todo("should navigate away from the page if not saas");

  it("should render the available credits", async () => {
    renderManageOrg();

    await waitFor(() => {
      const credits = screen.getByTestId("available-credits");
      expect(credits).toHaveTextContent("1000");
    });
  });

  it("should render account details", async () => {
    renderManageOrg();

    await waitFor(() => {
      const orgName = screen.getByTestId("org-name");
      expect(orgName).toHaveTextContent("Acme Corp");

      const billingInfo = screen.getByTestId("billing-info");
      expect(billingInfo).toHaveTextContent("**** **** **** 1234");
    });
  });

  it("should be able to add credits", async () => {
    const createCheckoutSessionSpy = vi.spyOn(
      OpenHands,
      "createCheckoutSession",
    );

    renderManageOrg();

    expect(screen.queryByTestId("add-credits-form")).not.toBeInTheDocument();
    // Simulate adding credits
    const addCreditsButton = screen.getByText(/add/i);
    await userEvent.click(addCreditsButton);

    const addCreditsForm = screen.getByTestId("add-credits-form");
    expect(addCreditsForm).toBeInTheDocument();

    const amountInput = within(addCreditsForm).getByTestId("amount-input");
    const nextButton = within(addCreditsForm).getByRole("button", {
      name: /next/i,
    });

    await userEvent.type(amountInput, "1000");
    await userEvent.click(nextButton);

    // expect redirect to payment page
    expect(createCheckoutSessionSpy).toHaveBeenCalledWith(1000);

    await waitFor(() =>
      expect(screen.queryByTestId("add-credits-form")).not.toBeInTheDocument(),
    );
  });

  it("should close the modal when clicking cancel", async () => {
    const createCheckoutSessionSpy = vi.spyOn(
      OpenHands,
      "createCheckoutSession",
    );
    renderManageOrg();

    expect(screen.queryByTestId("add-credits-form")).not.toBeInTheDocument();
    // Simulate adding credits
    const addCreditsButton = screen.getByText(/add/i);
    await userEvent.click(addCreditsButton);

    const addCreditsForm = screen.getByTestId("add-credits-form");
    expect(addCreditsForm).toBeInTheDocument();

    const cancelButton = within(addCreditsForm).getByRole("button", {
      name: /cancel/i,
    });

    await userEvent.click(cancelButton);

    expect(screen.queryByTestId("add-credits-form")).not.toBeInTheDocument();
    expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
  });

  describe("superadmin actions", () => {
    it.todo("should be able to update the organization name");

    it.todo("should be able to update the organization billing info");

    it.todo("should be able to delete an organization");
  });
});
