import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { ExpandableMessage } from "#/components/features/chat/expandable-message";

describe("ExpandableMessage", () => {
  it("should render with default colors for non-action messages", () => {
    renderWithProviders(<ExpandableMessage message="Hello" type="thought" />);
    const element = screen.getByText("Hello");
    const container = element.closest("div.flex.gap-2.items-center.justify-start");
    expect(container).toHaveClass("border-neutral-300");
  });

  it("should render with error colors for error messages", () => {
    renderWithProviders(<ExpandableMessage message="Error occurred" type="error" />);
    const element = screen.getByText("Error occurred");
    const container = element.closest("div.flex.gap-2.items-center.justify-start");
    expect(container).toHaveClass("border-danger");
  });

  it("should render with success colors for successful action messages", () => {
    renderWithProviders(
      <ExpandableMessage
        message="Command executed successfully"
        type="action"
        success={true}
      />
    );
    const element = screen.getByText("Command executed successfully");
    const container = element.closest("div.flex.gap-2.items-center.justify-start");
    expect(container).toHaveClass("border-success");
  });

  it("should render with error colors for failed action messages", () => {
    renderWithProviders(
      <ExpandableMessage
        message="Command failed"
        type="action"
        success={false}
      />
    );
    const element = screen.getByText("Command failed");
    const container = element.closest("div.flex.gap-2.items-center.justify-start");
    expect(container).toHaveClass("border-danger");
  });

  it("should render with neutral colors for action messages without success prop", () => {
    renderWithProviders(<ExpandableMessage message="Running command" type="action" />);
    const element = screen.getByText("Running command");
    const container = element.closest("div.flex.gap-2.items-center.justify-start");
    expect(container).toHaveClass("border-neutral-300");
  });
});