import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ReasoningContent } from "./reasoning-content";

describe("ReasoningContent", () => {
  it("should not render when content is empty", () => {
    const { container } = render(<ReasoningContent content="" />);
    expect(container.firstChild).toBeNull();
  });

  it("should not render when content is null", () => {
    const { container } = render(
      <ReasoningContent content={null as string | null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("should render reasoning content when provided", () => {
    const content = "This is my reasoning for the action.";
    render(<ReasoningContent content={content} />);

    expect(screen.getByText("Reasoning")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("should expand and collapse reasoning content", () => {
    const content = "This is my reasoning for the action.";
    render(<ReasoningContent content={content} />);

    const button = screen.getByRole("button");

    // Initially collapsed
    expect(screen.queryByText(content)).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(button);
    expect(screen.getByText(content)).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(button);
    expect(screen.queryByText(content)).not.toBeInTheDocument();
  });

  it("should render markdown content correctly", () => {
    const content = "**Bold text** and `code`";
    render(<ReasoningContent content={content} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(screen.getByText("Bold text")).toBeInTheDocument();
    expect(screen.getByText("code")).toBeInTheDocument();
  });
});
