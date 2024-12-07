import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CollapsePanelButton } from "#/components/shared/buttons/collapse-panel-button";

describe("CollapsePanelButton", () => {
  it("should render with correct aria-label when expanded", () => {
    render(<CollapsePanelButton isCollapsed={false} onClick={() => {}} />);
    expect(screen.getByLabelText("Collapse panel")).toBeInTheDocument();
  });

  it("should render with correct aria-label when collapsed", () => {
    render(<CollapsePanelButton isCollapsed onClick={() => {}} />);
    expect(screen.getByLabelText("Expand panel")).toBeInTheDocument();
  });

  it("should call onClick when clicked", () => {
    const onClick = vi.fn();
    render(<CollapsePanelButton isCollapsed={false} onClick={onClick} />);
    fireEvent.click(screen.getByLabelText("Collapse panel"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("should have rotate-180 class when collapsed", () => {
    render(<CollapsePanelButton isCollapsed onClick={() => {}} />);
    const button = screen.getByLabelText("Expand panel");
    expect(button.querySelector("svg")).toHaveClass("rotate-180");
  });

  it("should not have rotate-180 class when expanded", () => {
    render(<CollapsePanelButton isCollapsed={false} onClick={() => {}} />);
    const button = screen.getByLabelText("Collapse panel");
    expect(button.querySelector("svg")).not.toHaveClass("rotate-180");
  });
});
