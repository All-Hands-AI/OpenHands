import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MicroagentStatusIndicator } from "../src/components/features/chat/microagent/microagent-status-indicator";
import { MicroagentStatus } from "#/types/microagent-status";

// Mock the translation hook
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "MICROAGENT$STATUS_CREATING": "Creating microagent...",
        "MICROAGENT$STATUS_RUNNING": "Microagent is running...",
        "MICROAGENT$STATUS_COMPLETED": "Microagent completed successfully",
        "MICROAGENT$STATUS_ERROR": "Microagent encountered an error",
      };
      return translations[key] || key;
    },
  }),
}));

// Mock the Spinner component
vi.mock("@heroui/react", () => ({
  Spinner: ({ size }: { size: string }) => <div data-testid="spinner" data-size={size} />,
}));

// Mock the SuccessIndicator component
vi.mock("../src/components/features/chat/success-indicator", () => ({
  SuccessIndicator: ({ status }: { status: string }) => (
    <div data-testid="success-indicator" data-status={status} />
  ),
}));

describe("MicroagentStatusIndicator", () => {
  it("renders creating status correctly", () => {
    render(<MicroagentStatusIndicator status={MicroagentStatus.CREATING} />);
    
    expect(screen.getByTestId("spinner")).toBeInTheDocument();
    expect(screen.getByText("Creating microagent...")).toBeInTheDocument();
  });

  it("renders running status correctly", () => {
    render(<MicroagentStatusIndicator status={MicroagentStatus.RUNNING} />);
    
    expect(screen.getByTestId("spinner")).toBeInTheDocument();
    expect(screen.getByText("Microagent is running...")).toBeInTheDocument();
  });

  it("renders completed status correctly", () => {
    render(<MicroagentStatusIndicator status={MicroagentStatus.COMPLETED} />);
    
    expect(screen.getByTestId("success-indicator")).toBeInTheDocument();
    expect(screen.getByText("Microagent completed successfully")).toBeInTheDocument();
  });

  it("renders error status correctly", () => {
    render(<MicroagentStatusIndicator status={MicroagentStatus.ERROR} />);
    
    expect(screen.getByTestId("success-indicator")).toBeInTheDocument();
    expect(screen.getByText("Microagent encountered an error")).toBeInTheDocument();
  });

  it("applies correct CSS classes for different statuses", () => {
    const { rerender } = render(<MicroagentStatusIndicator status={MicroagentStatus.CREATING} />);
    
    let statusText = screen.getByText("Creating microagent...");
    expect(statusText).toHaveClass("underline");

    rerender(<MicroagentStatusIndicator status={MicroagentStatus.COMPLETED} />);
    statusText = screen.getByText("Microagent completed successfully");
    expect(statusText).toHaveClass("underline");

    rerender(<MicroagentStatusIndicator status={MicroagentStatus.ERROR} />);
    statusText = screen.getByText("Microagent encountered an error");
    expect(statusText).toHaveClass("underline");
  });
});