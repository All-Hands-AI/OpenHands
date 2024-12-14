import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { InstructionsPanel } from "../../../../src/components/features/instructions/instructions-panel";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, string>) => {
      if (params?.repoName) {
        return key.replace("{{repoName}}", params.repoName);
      }
      return key;
    },
  }),
}));

describe("InstructionsPanel", () => {
  const mockProps = {
    repoName: "test-org/test-repo",
    hasInstructions: false,
    tutorialUrl: undefined,
    onAddInstructions: vi.fn(),
  };

  it("renders without instructions", () => {
    render(<InstructionsPanel {...mockProps} />);
    expect(screen.getByText(/INSTRUCTIONS_PANEL\$NO_INSTRUCTIONS/)).toBeInTheDocument();
  });

  it("renders with instructions", () => {
    render(
      <InstructionsPanel
        {...mockProps}
        hasInstructions={true}
        tutorialUrl="https://example.com"
      />
    );
    expect(screen.getByText(/INSTRUCTIONS_PANEL\$INSTRUCTIONS_FOUND/)).toBeInTheDocument();
    expect(screen.getByText(/INSTRUCTIONS_PANEL\$VIEW_TUTORIAL/)).toBeInTheDocument();
  });

  it("calls onAddInstructions when add button is clicked", () => {
    render(<InstructionsPanel {...mockProps} />);
    fireEvent.click(screen.getByText(/INSTRUCTIONS_PANEL\$ADD_BUTTON/));
    expect(mockProps.onAddInstructions).toBeCalled();
  });
});
