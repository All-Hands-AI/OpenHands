import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../../test-utils";
import { DeepPlanDocumentChain } from "#/components/features/chat/deep-plan-document-chain";

// A backend document that cites a requirement section, matching the reference
// chain the validator accepts.
const documents = {
  requirements: ["# Requirements", "", "## 3.1 Authentication"].join("\n"),
  backend: ["# Backend design", "", "## 4.2 Login endpoint [Req 3.1]"].join(
    "\n",
  ),
};

const setup = (docs = documents) =>
  renderWithProviders(
    <DeepPlanDocumentChain documents={docs} expandedPhase="backend" />,
  );

describe("DeepPlanDocumentChain", () => {
  it("renders only the produced documents, in phase order", () => {
    setup();
    expect(
      screen.getByTestId("deep-plan-document-requirements"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("deep-plan-document-backend"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("deep-plan-document-database")).toBeNull();
  });

  it("renders a citation as a link to the cited document section", () => {
    setup();
    const citation = screen.getByTestId("deep-plan-citation");
    expect(citation).toHaveAttribute("href", "deep-plan-doc:requirements#3.1");
  });

  it("stamps the cited heading with the id a citation targets", () => {
    setup();
    // The Markdown renderer stamps `{#id}` onto headings, so the anchor target
    // exists for the citation click handler to look up.
    const heading = screen.getByText("3.1 Authentication", { exact: false });
    expect(
      heading.closest("[id]")?.id ??
        document.getElementById("deep-plan-section-requirements-3.1")?.id,
    ).toBe("deep-plan-section-requirements-3.1");
  });

  it("scrolls to the cited section when a citation is clicked", async () => {
    const user = userEvent.setup();
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    setup();
    await user.click(screen.getByTestId("deep-plan-citation"));
    expect(scrollIntoView).toHaveBeenCalled();
  });

  it("marks the expanded phase document as open", () => {
    setup();
    expect(screen.getByTestId("deep-plan-document-backend")).toHaveAttribute(
      "data-open",
      "true",
    );
    expect(
      screen.getByTestId("deep-plan-document-requirements"),
    ).toHaveAttribute("data-open", "false");
  });
});
