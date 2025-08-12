import { render, screen } from "@testing-library/react";
import { describe, expect, vi, beforeEach, it } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { RepositorySelectionForm } from "../../../../src/components/features/home/repo-selection-form";
import OpenHands from "#/api/open-hands";
import { GitRepository } from "#/types/git";

// Create mock functions
const mockUseUserRepositories = vi.fn();
const mockUseCreateConversation = vi.fn();
const mockUseIsCreatingConversation = vi.fn();
const mockUseTranslation = vi.fn();
const mockUseAuth = vi.fn();
const mockUseGitRepositories = vi.fn();
const mockUseUserProviders = vi.fn();

// Setup default mock returns
mockUseUserRepositories.mockReturnValue({
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

// Default mock for useGitRepositories
mockUseGitRepositories.mockReturnValue({
  data: { pages: [] },
  isLoading: false,
  isError: false,
  hasNextPage: false,
  isFetchingNextPage: false,
  fetchNextPage: vi.fn(),
  onLoadMore: vi.fn(),
});

vi.mock("react-i18next", () => ({
  useTranslation: () => mockUseTranslation(),
}));

vi.mock("#/hooks/use-user-providers", () => ({
  useUserProviders: () => mockUseUserProviders(),
}));

mockUseUserProviders.mockReturnValue({
  providers: ["github"],
});

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

vi.mock("#/hooks/use-debounce", () => ({
  useDebounce: (value: string) => value,
}));

vi.mock("react-router", async (importActual) => ({
  ...(await importActual()),
  useNavigate: vi.fn(),
}));

vi.mock("#/hooks/query/use-git-repositories", () => ({
  useGitRepositories: () => mockUseGitRepositories(),
}));

const mockOnRepoSelection = vi.fn();
const renderForm = () =>
  render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />, {
    wrapper: ({ children }) => (
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: {
              queries: {
                retry: false,
              },
            },
          })
        }
      >
        {children}
      </QueryClientProvider>
    ),
  });

describe("RepositorySelectionForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows dropdown when repositories are loaded", async () => {
    const MOCK_REPOS: GitRepository[] = [
      {
        id: "1",
        full_name: "user/repo1",
        git_provider: "github",
        is_public: true,
      },
      {
        id: "2",
        full_name: "user/repo2",
        git_provider: "github",
        is_public: true,
      },
    ];
    mockUseGitRepositories.mockReturnValue({
      data: { pages: [{ data: MOCK_REPOS }] },
      isLoading: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      onLoadMore: vi.fn(),
    });

    renderForm();
    expect(await screen.findByTestId("repo-dropdown")).toBeInTheDocument();
  });

  it("shows error message when repository fetch fails", async () => {
    mockUseGitRepositories.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      onLoadMore: vi.fn(),
    });

    renderForm();

    expect(
      await screen.findByTestId("repo-dropdown-error"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("HOME$FAILED_TO_LOAD_REPOSITORIES"),
    ).toBeInTheDocument();
  });

  it("should call the search repos API when searching a URL", async () => {
    const MOCK_REPOS: GitRepository[] = [
      {
        id: "1",
        full_name: "user/repo1",
        git_provider: "github",
        is_public: true,
      },
      {
        id: "2",
        full_name: "user/repo2",
        git_provider: "github",
        is_public: true,
      },
    ];

    const MOCK_SEARCH_REPOS: GitRepository[] = [
      {
        id: "3",
        full_name: "kubernetes/kubernetes",
        git_provider: "github",
        is_public: true,
      },
    ];

    const searchGitReposSpy = vi.spyOn(OpenHands, "searchGitRepositories");
    searchGitReposSpy.mockResolvedValue(MOCK_SEARCH_REPOS);

    mockUseGitRepositories.mockReturnValue({
      data: { pages: [{ data: MOCK_REPOS }] },
      isLoading: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      onLoadMore: vi.fn(),
    });

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

    renderForm();

    const dropdown = await screen.findByTestId("repo-dropdown");
    const input = dropdown.querySelector('input[type="text"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    await userEvent.type(input, "https://github.com/kubernetes/kubernetes");
    expect(searchGitReposSpy).toHaveBeenLastCalledWith(
      "kubernetes/kubernetes",
      3,
    );
  });

  it("should call onRepoSelection when a searched repository is selected", async () => {
    const MOCK_SEARCH_REPOS: GitRepository[] = [
      {
        id: "3",
        full_name: "kubernetes/kubernetes",
        git_provider: "github",
        is_public: true,
      },
    ];

    const searchGitReposSpy = vi.spyOn(OpenHands, "searchGitRepositories");
    searchGitReposSpy.mockResolvedValue(MOCK_SEARCH_REPOS);

    mockUseGitRepositories.mockReturnValue({
      data: { pages: [{ data: MOCK_SEARCH_REPOS }] },
      isLoading: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      onLoadMore: vi.fn(),
    });

    renderForm();

    const dropdown = await screen.findByTestId("repo-dropdown");
    const input = dropdown.querySelector('input[type="text"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    await userEvent.type(input, "https://github.com/kubernetes/kubernetes");
    expect(searchGitReposSpy).toHaveBeenLastCalledWith(
      "kubernetes/kubernetes",
      3,
    );
  });
});
