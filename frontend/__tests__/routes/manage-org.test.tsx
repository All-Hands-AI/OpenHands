import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { organizationService } from "#/api/organization-service/organization-service.api";

function ManageOrg() {
  const { data: organization } = useQuery({
    queryKey: ["organization", "about"],
    queryFn: organizationService.getOrganization,
  });

  return (
    <div>
      <div data-testid="available-credits">{organization?.balance}</div>
      <div data-testid="org-name" />
      <div data-testid="billing-info" />
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

    const credits = await screen.findByTestId("available-credits");
    expect(credits).toHaveTextContent("1000");
  });

  it.todo("should allow the user to add credits", async () => {
    renderManageOrg();
  });

  it("should render account details", async () => {
    renderManageOrg();

    await screen.findByTestId("org-name");
    await screen.findByTestId("billing-info");
  });

  it.todo("should be able to add credits");
  it.todo("should be able to update the organization name");
  it.todo("should be able to update the organization billing info");
  it.todo("should be able to delete an organization");
});
