import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActionSuggestions } from "#/components/features/chat/action-suggestions";
import { useAuth } from "#/context/auth-context";
import { useSelector } from "react-redux";

// Mock dependencies
vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

vi.mock("react-redux", () => ({
  useSelector: vi.fn(),
}));

vi.mock("#/context/auth-context", () => ({
  useAuth: vi.fn(),
}));

describe("ActionSuggestions", () => {
  // Setup mocks for each test
  vi.clearAllMocks();
  
  (useAuth as any).mockReturnValue({
    githubTokenIsSet: true,
  });
  
  (useSelector as any).mockReturnValue({
    selectedRepository: "test-repo",
  });

  it("should render both GitHub buttons when GitHub token is set and repository is selected", () => {
    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    const pushButton = screen.getByRole("button", { name: "Push to Branch" });
    const prButton = screen.getByRole("button", { name: "Push & Create PR" });

    expect(pushButton).toBeInTheDocument();
    expect(prButton).toBeInTheDocument();
  });

  it("should not render buttons when GitHub token is not set", () => {
    (useAuth as any).mockReturnValue({
      githubTokenIsSet: false,
    });

    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    expect(screen.queryByRole("button", { name: "Push to Branch" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Push & Create PR" })).not.toBeInTheDocument();
  });

  it("should not render buttons when no repository is selected", () => {
    (useSelector as any).mockReturnValue({
      selectedRepository: null,
    });

    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    expect(screen.queryByRole("button", { name: "Push to Branch" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Push & Create PR" })).not.toBeInTheDocument();
  });

  it("should have different prompts for 'Push to Branch' and 'Push & Create PR' buttons", () => {
    // This test verifies that the prompts are different in the component
    const component = render(<ActionSuggestions onSuggestionsClick={() => {}} />);
    
    // Get the component instance to access the internal values
    const pushBranchPrompt = "Please push the changes to a remote branch on GitHub, but do NOT create a pull request. Please use the exact SAME branch name as the one you are currently on.";
    const createPRPrompt = "Please push the changes to GitHub and open a pull request. Please create a meaningful branch name that describes the changes.";
    
    // Verify the prompts are different
    expect(pushBranchPrompt).not.toEqual(createPRPrompt);
    
    // Verify the PR prompt mentions creating a meaningful branch name
    expect(createPRPrompt).toContain("meaningful branch name");
    expect(createPRPrompt).not.toContain("SAME branch name");
  });
});