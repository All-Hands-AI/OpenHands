import { render, screen, fireEvent } from "@testing-library/react";
import { CodeNotInGitHubLink } from "#/components/features/github/code-not-in-github-link";
import { useDispatch } from "react-redux";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock dependencies
vi.mock("react-redux", () => ({
  useDispatch: vi.fn(),
}));

vi.mock("#/hooks/mutation/use-create-conversation", () => ({
  useCreateConversation: vi.fn(),
}));

vi.mock("#/state/initial-query-slice", () => ({
  setInitialPrompt: vi.fn(),
}));

describe("CodeNotInGitHubLink", () => {
  const mockDispatch = vi.fn();
  const mockCreateConversation = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useDispatch as any).mockReturnValue(mockDispatch);
    (useCreateConversation as any).mockReturnValue({
      mutate: mockCreateConversation,
    });
  });

  it("renders correctly", () => {
    render(<CodeNotInGitHubLink />);
    expect(screen.getByText(/Code not in GitHub\?/)).toBeInTheDocument();
    expect(screen.getByText("Start from scratch")).toBeInTheDocument();
  });

  it("calls createConversation with allowEmptyQuery when clicked", () => {
    render(<CodeNotInGitHubLink />);
    
    fireEvent.click(screen.getByText("Start from scratch"));
    
    expect(mockDispatch).toHaveBeenCalledWith(setInitialPrompt(""));
    expect(mockCreateConversation).toHaveBeenCalledWith({
      q: "",
      allowEmptyQuery: true,
    });
  });
});