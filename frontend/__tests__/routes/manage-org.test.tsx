import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import React from "react";
import { organizationService } from "#/api/organization-service/organization-service.api";

function ManageOrg() {
  const { data: organization } = useQuery({
    queryKey: ["organization", "about"],
    queryFn: () => organizationService.getOrganization({ orgId: "1" }),
  });
  const { data: organizationPaymentInfo } = useQuery({
    queryKey: ["organization", "payment"],
    queryFn: () =>
      organizationService.getOrganizationPaymentInfo({ orgId: "1" }),
  });

  const [addCreditsFormVisible, setAddCreditsFormVisible] =
    React.useState(false);

  return (
    <div>
      <div data-testid="available-credits">{organization?.balance}</div>
      <button type="button" onClick={() => setAddCreditsFormVisible(true)}>
        Add
      </button>
      {addCreditsFormVisible && (
        <div data-testid="add-credits-form">
          <input type="text" />
          <button type="button">Next</button>
        </div>
      )}
      <div data-testid="org-name">{organization?.name}</div>
      <div data-testid="billing-info">
        {organizationPaymentInfo?.cardNumber}
      </div>
    </div>
  );
}

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

  it.todo("should allow the user to add credits", async () => {
    renderManageOrg();
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
    renderManageOrg();

    expect(screen.queryByTestId("add-credits-form")).not.toBeInTheDocument();
    // Simulate adding credits
    const addCreditsButton = screen.getByText(/add/i);
    await userEvent.click(addCreditsButton);

    const addCreditsForm = screen.getByTestId("add-credits-form");
    expect(addCreditsForm).toBeInTheDocument();

    expect(within(addCreditsForm).getByRole("textbox")).toBeInTheDocument();
    expect(
      within(addCreditsForm).getByRole("button", { name: /next/i }),
    ).toBeInTheDocument();

    // expect redirect to payment page
  });

  it.todo("should be able to update the organization name");
  it.todo("should be able to update the organization billing info");
  it.todo("should be able to delete an organization");
});
