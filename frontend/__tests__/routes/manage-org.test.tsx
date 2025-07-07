import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

const renderManageOrg = render(<ManageOrg />);

describe("Manage Org Route", () => {
  it.todo("should navigate away from the page if not saas");
  it("should render the available credits", async () => {
    render(<ManageOrg />);

    const credits = await screen.findByTestId("available-credits");
    expect(credits).toBeInTheDocument();
    expect(credits).toHaveTextContent("1000");
  });

  it.todo("should allow the user to add credits", async () => {
    render(<ManageOrg />);
  });

  it("should render account details", async () => {
    render(<ManageOrg />);

    expect(screen.getByTestId("org-name")).toBeInTheDocument();
    expect(screen.getByTestId("billing-info")).toBeInTheDocument();
  });
});
