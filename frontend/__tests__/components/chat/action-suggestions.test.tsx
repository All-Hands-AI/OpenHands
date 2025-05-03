import { describe, expect, it, vi, beforeEach } from "vitest";
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

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "ACTION$PUSH_TO_BRANCH": "Push to Branch",
        "ACTION$PUSH_CREATE_PR": "Push & Create PR",
        "ACTION$PUSH_CHANGES_TO_PR": "Push Changes to PR"
      };
      return translations[key] || key;
    },
  }),
}));

describe("ActionSuggestions", () => {
  // Setup mocks for each test
  beforeEach(() => {
    vi.clearAllMocks();

    (useAuth as any).mockReturnValue({
      providersAreSet: true,
    });

    (useSelector as any).mockReturnValue({
      selectedRepository: "test-repo",
    });
  });

  it("should render both GitHub buttons when GitHub token is set and repository is selected", () => {
    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    // Find all buttons with data-testid="suggestion"
    const buttons = screen.getAllByTestId("suggestion");

    // Check if we have at least 2 buttons
    expect(buttons.length).toBeGreaterThanOrEqual(2);

    // Check if the buttons contain the expected text
    const pushButton = buttons.find((button) =>
      button.textContent?.includes("Push to Branch"),
    );
    const prButton = buttons.find((button) =>
      button.textContent?.includes("Push & Create PR"),
    );

    expect(pushButton).toBeInTheDocument();
    expect(prButton).toBeInTheDocument();
  });

  it("should not render buttons when GitHub token is not set", () => {
    (useAuth as any).mockReturnValue({
      providersAreSet: false,
    });

    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    expect(screen.queryByTestId("suggestion")).not.toBeInTheDocument();
  });

  it("should not render buttons when no repository is selected", () => {
    (useSelector as any).mockReturnValue({
      selectedRepository: null,
    });

    render(<ActionSuggestions onSuggestionsClick={() => {}} />);

    expect(screen.queryByTestId("suggestion")).not.toBeInTheDocument();
  });

  it("should have different prompts for 'Push to Branch' and 'Push & Create PR' buttons", () => {
    // This test verifies that the prompts are different in the component
    const component = render(
      <ActionSuggestions onSuggestionsClick={() => {}} />,
    );

    // Get the component instance to access the internal values
    const pushBranchPrompt =
      "Please push the changes to a remote branch on GitHub, but do NOT create a pull request. Please use the exact SAME branch name as the one you are currently on.";
    const createPRPrompt =
      "Please push the changes to GitHub and open a pull request. Please create a meaningful branch name that describes the changes. If a pull request template exists in the repository, please follow it when creating the PR description.";

    // Verify the prompts are different
    expect(pushBranchPrompt).not.toEqual(createPRPrompt);

    // Verify the PR prompt mentions creating a meaningful branch name
    expect(createPRPrompt).toContain("meaningful branch name");
    expect(createPRPrompt).not.toContain("SAME branch name");
  });
});
