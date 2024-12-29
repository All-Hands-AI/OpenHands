import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ToggleWorkspaceIconButton } from "#/components/shared/buttons/toggle-workspace-icon-button";

describe("Workspace Toggle", () => {
  it("should render toggle button with correct icon and label", () => {
    const onClickMock = vi.fn();

    // Test initial state (workspace visible)
    const { rerender } = render(
      <ToggleWorkspaceIconButton onClick={onClickMock} isHidden={false} />
    );

    const button = screen.getByTestId("toggle");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "Close workspace");

    // Test hidden state
    rerender(
      <ToggleWorkspaceIconButton onClick={onClickMock} isHidden={true} />
    );
    expect(button).toHaveAttribute("aria-label", "Open workspace");
  });

  it("should call onClick handler when clicked", () => {
    const onClickMock = vi.fn();
    render(
      <ToggleWorkspaceIconButton onClick={onClickMock} isHidden={false} />
    );

    const button = screen.getByTestId("toggle");
    fireEvent.click(button);
    expect(onClickMock).toHaveBeenCalledTimes(1);
  });
});
