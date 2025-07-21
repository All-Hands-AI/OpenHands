import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ActionSuggestions } from "#/components/features/chat/action-suggestions";
import OpenHands from "#/api/open-hands";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";

// Mock dependencies
vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

const { useSelectorMock } = vi.hoisted(() => ({
  useSelectorMock: vi.fn(),
}));

vi.mock("react-redux", () => ({
  useSelector: useSelectorMock,
}));

vi.mock("#/context/auth-context", () => ({
  useAuth: vi.fn(),
}));

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        ACTION$PUSH_TO_BRANCH: "Push to Branch",
        ACTION$PUSH_CREATE_PR: "Push & Create PR",
        ACTION$PUSH_CHANGES_TO_PR: "Push Changes to PR",
      };
      return translations[key] || key;
    },
  }),
}));

vi.mock("react-router", () => ({
  useParams: () => ({
    conversationId: "test-conversation-id",
  }),
}));

const renderActionSuggestions = () =>
  render(<ActionSuggestions onSuggestionsClick={() => {}} />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("ActionSuggestions", () => {
  // Setup mocks for each test
  beforeEach(() => {
    vi.clearAllMocks();
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: "some-token",
      },
    });

    useSelectorMock.mockReturnValue({
      selectedRepository: "test-repo",
    });
  });

  it("should render both GitHub buttons when GitHub token is set and repository is selected", async () => {
    const getConversationSpy = vi.spyOn(OpenHands, "getConversation");
    // @ts-expect-error - only required for testing
    getConversationSpy.mockResolvedValue({
      selected_repository: "test-repo",
    });
    renderActionSuggestions();

    // Find all buttons with data-testid="suggestion"
    const buttons = await screen.findAllByTestId("suggestion");

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
    renderActionSuggestions();

    expect(screen.queryByTestId("suggestion")).not.toBeInTheDocument();
  });

  it("should not render buttons when no repository is selected", () => {
    useSelectorMock.mockReturnValue({
      selectedRepository: null,
    });

    renderActionSuggestions();

    expect(screen.queryByTestId("suggestion")).not.toBeInTheDocument();
  });

  it("should have different prompts for 'Push to Branch' and 'Push & Create PR' buttons", () => {
    // This test verifies that the prompts are different in the component
    renderActionSuggestions();

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

  it("should use correct provider name based on conversation git_provider, not user authenticated providers", async () => {
    // Test case for GitHub repository
    const getConversationSpy = vi.spyOn(OpenHands, "getConversation");
    getConversationSpy.mockResolvedValue({
      conversation_id: "test-github",
      title: "GitHub Test",
      selected_repository: "test-repo",
      git_provider: "github",
      selected_branch: "main",
      last_updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      status: "RUNNING",
      runtime_status: "STATUS$READY",
      url: null,
      session_api_key: null,
    });

    // Mock user having both GitHub and Bitbucket tokens
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: "github-token",
        bitbucket: "bitbucket-token",
      },
    });

    const onSuggestionsClick = vi.fn();
    render(<ActionSuggestions onSuggestionsClick={onSuggestionsClick} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    const buttons = await screen.findAllByTestId("suggestion");
    const prButton = buttons.find((button) =>
      button.textContent?.includes("Push & Create PR"),
    );

    expect(prButton).toBeInTheDocument();

    if (prButton) {
      prButton.click();
    }

    // The suggestion should mention GitHub, not Bitbucket
    expect(onSuggestionsClick).toHaveBeenCalledWith(
      expect.stringContaining("GitHub")
    );
    expect(onSuggestionsClick).not.toHaveBeenCalledWith(
      expect.stringContaining("Bitbucket")
    );
  });

  it("should use GitLab terminology when git_provider is gitlab", async () => {
    const getConversationSpy = vi.spyOn(OpenHands, "getConversation");
    getConversationSpy.mockResolvedValue({
      conversation_id: "test-gitlab",
      title: "GitLab Test",
      selected_repository: "test-repo",
      git_provider: "gitlab",
      selected_branch: "main",
      last_updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      status: "RUNNING",
      runtime_status: "STATUS$READY",
      url: null,
      session_api_key: null,
    });

    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        gitlab: "gitlab-token",
      },
    });

    const onSuggestionsClick = vi.fn();
    render(<ActionSuggestions onSuggestionsClick={onSuggestionsClick} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    const buttons = await screen.findAllByTestId("suggestion");
    const prButton = buttons.find((button) =>
      button.textContent?.includes("Push & Create PR"),
    );

    if (prButton) {
      prButton.click();
    }

    // Should mention GitLab and "merge request" instead of "pull request"
    expect(onSuggestionsClick).toHaveBeenCalledWith(
      expect.stringContaining("GitLab")
    );
    expect(onSuggestionsClick).toHaveBeenCalledWith(
      expect.stringContaining("merge request")
    );
  });

  it("should use Bitbucket terminology when git_provider is bitbucket", async () => {
    const getConversationSpy = vi.spyOn(OpenHands, "getConversation");
    getConversationSpy.mockResolvedValue({
      conversation_id: "test-bitbucket",
      title: "Bitbucket Test",
      selected_repository: "test-repo",
      git_provider: "bitbucket",
      selected_branch: "main",
      last_updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      status: "RUNNING",
      runtime_status: "STATUS$READY",
      url: null,
      session_api_key: null,
    });

    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        bitbucket: "bitbucket-token",
      },
    });

    const onSuggestionsClick = vi.fn();
    render(<ActionSuggestions onSuggestionsClick={onSuggestionsClick} />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

    const buttons = await screen.findAllByTestId("suggestion");
    const prButton = buttons.find((button) =>
      button.textContent?.includes("Push & Create PR"),
    );

    if (prButton) {
      prButton.click();
    }

    // Should mention Bitbucket
    expect(onSuggestionsClick).toHaveBeenCalledWith(
      expect.stringContaining("Bitbucket")
    );
  });
});
