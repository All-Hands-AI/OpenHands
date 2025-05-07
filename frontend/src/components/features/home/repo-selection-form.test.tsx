import { render, screen } from "@testing-library/react";
import { describe, test, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RepositorySelectionForm } from "./repo-selection-form";

// Create mock functions
const mockUseUserRepositories = vi.fn();
const mockUseRepositoryBranches = vi.fn();
const mockUseCreateConversation = vi.fn();
const mockUseIsCreatingConversation = vi.fn();
const mockUseTranslation = vi.fn();
const mockUseAuth = vi.fn();

// Setup default mock returns
mockUseUserRepositories.mockReturnValue({
  data: [],
  isLoading: false,
  isError: false,
});

mockUseRepositoryBranches.mockReturnValue({
  data: [],
  isLoading: false,
  isError: false,
});

mockUseCreateConversation.mockReturnValue({
  mutate: vi.fn(),
  isPending: false,
  isSuccess: false,
});

mockUseIsCreatingConversation.mockReturnValue(false);

mockUseTranslation.mockReturnValue({ t: (key: string) => key });

mockUseAuth.mockReturnValue({
  isAuthenticated: true,
  isLoading: false,
  providersAreSet: true,
  user: {
    id: 1,
    login: "testuser",
    avatar_url: "https://example.com/avatar.png",
    name: "Test User",
    email: "test@example.com",
    company: "Test Company",
  },
  login: vi.fn(),
  logout: vi.fn(),
});

// Mock the modules
vi.mock("#/hooks/query/use-user-repositories", () => ({
  useUserRepositories: () => mockUseUserRepositories(),
}));

vi.mock("#/hooks/query/use-repository-branches", () => ({
  useRepositoryBranches: () => mockUseRepositoryBranches(),
}));

vi.mock("#/hooks/mutation/use-create-conversation", () => ({
  useCreateConversation: () => mockUseCreateConversation(),
}));

vi.mock("#/hooks/use-is-creating-conversation", () => ({
  useIsCreatingConversation: () => mockUseIsCreatingConversation(),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => mockUseTranslation(),
}));

vi.mock("#/context/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

const renderRepositorySelectionForm = () =>
  render(<RepositorySelectionForm onRepoSelection={vi.fn()} />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("RepositorySelectionForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("shows loading indicator when repositories are being fetched", () => {
    // Setup loading state
    mockUseUserRepositories.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderRepositorySelectionForm();

    // Check if loading indicator is displayed
    expect(screen.getByTestId("repo-dropdown-loading")).toBeInTheDocument();
    expect(screen.getByText("HOME$LOADING_REPOSITORIES")).toBeInTheDocument();
  });

  test("shows dropdown when repositories are loaded", () => {
    // Setup loaded repositories
    mockUseUserRepositories.mockReturnValue({
      data: [
        {
          id: 1,
          full_name: "user/repo1",
          git_provider: "github",
          is_public: true,
        },
        {
          id: 2,
          full_name: "user/repo2",
          git_provider: "github",
          is_public: true,
        },
      ],
      isLoading: false,
      isError: false,
    });

    renderRepositorySelectionForm();

    // Check if dropdown is displayed
    expect(screen.getByTestId("repo-dropdown")).toBeInTheDocument();
  });

  test("shows error message when repository fetch fails", () => {
    // Setup error state
    mockUseUserRepositories.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Failed to fetch repositories"),
    });

    renderRepositorySelectionForm();

    // Check if error message is displayed
    expect(screen.getByTestId("repo-dropdown-error")).toBeInTheDocument();
    expect(
      screen.getByText("HOME$FAILED_TO_LOAD_REPOSITORIES"),
    ).toBeInTheDocument();
  });
});
