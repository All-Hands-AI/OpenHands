import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ToggleWorkspaceIconButton } from "../toggle-workspace-icon-button";

describe("ToggleWorkspaceIconButton", () => {
  it("renders with correct placement and dimensions", () => {
    const mockOnClick = vi.fn();
    render(
      <ToggleWorkspaceIconButton onClick={mockOnClick} isHidden={false} />,
    );

    const button = screen.getByTestId("toggle");
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass("h-[100px] w-[20px]");
    expect(button).toHaveClass(
      "absolute right-0 top-1/2 transform -translate-y-1/2",
    );
    expect(button).toHaveClass("rounded-l-md");
  });

  it("displays the correct icon based on isHidden prop", () => {
    const mockOnClick = vi.fn();

    const { rerender } = render(
      <ToggleWorkspaceIconButton onClick={mockOnClick} isHidden={false} />,
    );
    expect(screen.getByLabelText("Close workspace")).toBeInTheDocument();
    expect(screen.getByTestId("toggle")).toContainElement(
      screen.getByTestId("arrow-back-icon"),
    );

    rerender(<ToggleWorkspaceIconButton onClick={mockOnClick} isHidden />);
    expect(screen.getByLabelText("Open workspace")).toBeInTheDocument();
    expect(screen.getByTestId("toggle")).toContainElement(
      screen.getByTestId("arrow-forward-icon"),
    );
  });
});
