import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CreateInstructionsModal } from "../../../../../src/components/shared/modals/instructions/create-instructions-modal";

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

describe("CreateInstructionsModal", () => {
  const mockProps = {
    repoName: "test-org/test-repo",
    onClose: vi.fn(),
    onCreateInstructions: vi.fn(),
  };

  it("renders with title and description", () => {
    render(<CreateInstructionsModal {...mockProps} />);
    expect(screen.getByText(/CREATE_INSTRUCTIONS_MODAL\$TITLE/)).toBeInTheDocument();
    expect(screen.getByText(/CREATE_INSTRUCTIONS_MODAL\$DESCRIPTION/)).toBeInTheDocument();
  });

  it("calls onClose when cancel button is clicked", () => {
    render(<CreateInstructionsModal {...mockProps} />);
    fireEvent.click(screen.getByText(/CREATE_INSTRUCTIONS_MODAL\$CANCEL_BUTTON/));
    expect(mockProps.onClose).toBeCalled();
  });

  it("calls onCreateInstructions with input value when form is submitted", () => {
    render(<CreateInstructionsModal {...mockProps} />);

    // Type in the instructions
    const textarea = screen.getByPlaceholderText(/Enter repository instructions/);
    fireEvent.change(textarea, { target: { value: "# Test Instructions" } });

    // Submit the form
    fireEvent.click(screen.getByText(/CREATE_INSTRUCTIONS_MODAL\$CREATE_BUTTON/));

    expect(mockProps.onCreateInstructions).toBeCalledWith("# Test Instructions");
    expect(mockProps.onClose).toBeCalled();
  });
});
