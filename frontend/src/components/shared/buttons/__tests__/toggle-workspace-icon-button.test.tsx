import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ToggleWorkspaceIconButton } from "../toggle-workspace-icon-button";

describe("ToggleWorkspaceIconButton", () => {
  it("renders with correct dimensions and styling", () => {
    const mockOnClick = vi.fn();
    render(
      <ToggleWorkspaceIconButton onClick={mockOnClick} isHidden={false} />,
    );

    const button = screen.getByTestId("toggle");
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass("h-[100px] w-[20px]");
    expect(button).toHaveClass("bg-neutral-800");
    expect(button).toHaveClass("hover:bg-neutral-700");
    expect(button).toHaveClass("rounded-md");
  });

  it("displays the correct icon based on isHidden prop", () => {
    const mockOnClick = vi.fn();

    const { rerender } = render(
      <ToggleWorkspaceIconButton onClick={mockOnClick} isHidden={false} />,
    );
    expect(screen.getByLabelText("Close workspace")).toBeInTheDocument();
    expect(screen.getByTestId("toggle")).toContainElement(
      screen.getByTestId("arrow-forward-icon"),
    );

    rerender(<ToggleWorkspaceIconButton onClick={mockOnClick} isHidden />);
    expect(screen.getByLabelText("Open workspace")).toBeInTheDocument();
    expect(screen.getByTestId("toggle")).toContainElement(
      screen.getByTestId("arrow-back-icon"),
    );
  });

  it("remains visible when workspace is collapsed", () => {
    const mockOnClick = vi.fn();
    render(<ToggleWorkspaceIconButton onClick={mockOnClick} isHidden />);

    const button = screen.getByTestId("toggle");
    expect(button).toBeVisible();
  });
});
