import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { setupStore } from "test-utils";
import { Provider } from "react-redux";
import { createRoutesStub, Outlet } from "react-router";
import OpenHands from "#/api/open-hands";
import { GitRepository } from "#/types/git";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";

const renderRepoConnector = () => {
  const mockRepoSelection = vi.fn();
  const RouterStub = createRoutesStub([
    {
      Component: () => <RepoConnector onRepoSelection={mockRepoSelection} />,
      path: "/",
    },
    {
      Component: () => <div data-testid="conversation-screen" />,
      path: "/conversations/:conversationId",
    },
    {
      Component: () => <Outlet />,
      path: "/settings",
      children: [
        {
          Component: () => <div data-testid="settings-screen" />,
          path: "/settings",
        },
        {
          Component: () => <div data-testid="git-settings-screen" />,
          path: "/settings/integrations",
        },
      ],
    },
  ]);

  return render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </Provider>
    ),
  });
};

const MOCK_RESPOSITORIES: GitRepository[] = [
  {
    id: "1",
    full_name: "rbren/polaris",
    git_provider: "github",
    is_public: true,
    main_branch: "main",
  },
  {
    id: "2",
    full_name: "All-Hands-AI/OpenHands",
    git_provider: "github",
    is_public: true,
    main_branch: "main",
  },
];

beforeEach(() => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
  getSettingsSpy.mockResolvedValue({
    ...MOCK_DEFAULT_USER_SETTINGS,
    provider_tokens_set: {
      github: "some-token",
      gitlab: null,
    },
  });
});

describe("RepoConnector", () => {
  it("should render the repository connector section", () => {
    renderRepoConnector();
    screen.getByTestId("repo-connector");
  });

  it("should render the available repositories in the dropdown", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    // Mock the search function that's used by the dropdown
    vi.spyOn(OpenHands, "searchGitRepositories").mockResolvedValue(
      MOCK_RESPOSITORIES,
    );

    renderRepoConnector();

    // First select the provider
    const providerDropdown = await waitFor(() =>
      screen.getByTestId("git-provider-dropdown"),
    );
    await userEvent.click(providerDropdown);
    await userEvent.click(screen.getByText("GitHub"));

    // Then interact with the repository dropdown
    const repoInput = await waitFor(() =>
      screen.getByTestId("git-repo-dropdown"),
    );
    await userEvent.click(repoInput);

    // Wait for the options to be loaded and displayed
    await waitFor(() => {
      expect(screen.getByText("rbren/polaris")).toBeInTheDocument();
      expect(screen.getByText("All-Hands-AI/OpenHands")).toBeInTheDocument();
    });
  });

  it("should only enable the launch button if a repo is selected", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderRepoConnector();

    const launchButton = await screen.findByTestId("repo-launch-button");
    expect(launchButton).toBeDisabled();

    // Mock the repository branches API call
    vi.spyOn(OpenHands, "getRepositoryBranches").mockResolvedValue({ branches: [
      { name: "main", commit_sha: "123", protected: false },
      { name: "develop", commit_sha: "456", protected: false },
    ], has_next_page: false, current_page: 1, per_page: 30, total_count: 2 });

    // First select the provider
    const providerDropdown = await waitFor(() =>
      screen.getByTestId("git-provider-dropdown"),
    );
    await userEvent.click(providerDropdown);
    await userEvent.click(screen.getByText("GitHub"));

    // Then select the repository
    const repoInput = await waitFor(() =>
      screen.getByTestId("git-repo-dropdown"),
    );

    await userEvent.click(repoInput);

    // Wait for the options to be loaded and displayed
    await waitFor(() => {
      expect(screen.getByText("rbren/polaris")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("rbren/polaris"));

    // Wait for the branch to be auto-selected
    await waitFor(() => {
      const branchInput = screen.getByTestId("git-branch-dropdown-input");
      expect(branchInput).toHaveValue("main");
    });

    expect(launchButton).toBeEnabled();
  });

  it("should render the 'add github repos' link if saas mode and github provider is set", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        github: "some-token",
        gitlab: null,
      },
    });

    renderRepoConnector();

    await screen.findByText("HOME$ADD_GITHUB_REPOS");
  });

  it("should not render the 'add github repos' link if github provider is not set", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {
        gitlab: "some-token",
        github: null,
      },
    });

    renderRepoConnector();

    expect(screen.queryByText("HOME$ADD_GITHUB_REPOS")).not.toBeInTheDocument();
  });

  it("should not render the 'add git(hub|lab) repos' links if oss mode", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "oss",
    });

    renderRepoConnector();

    expect(screen.queryByText("Add GitHub repos")).not.toBeInTheDocument();
    expect(screen.queryByText("Add GitLab repos")).not.toBeInTheDocument();
  });

  it("should create a conversation and redirect with the selected repo when pressing the launch button", async () => {
    const createConversationSpy = vi.spyOn(OpenHands, "createConversation");
    createConversationSpy.mockResolvedValue({
      conversation_id: "mock-conversation-id",
      title: "Test Conversation",
      selected_repository: "user/repo1",
      selected_branch: "main",
      git_provider: "github",
      last_updated_at: "2023-01-01T00:00:00Z",
      created_at: "2023-01-01T00:00:00Z",
      status: "STARTING",
      runtime_status: null,
      url: null,
      session_api_key: null,
    });
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderRepoConnector();

    const repoConnector = screen.getByTestId("repo-connector");
    const launchButton =
      await within(repoConnector).findByTestId("repo-launch-button");
    await userEvent.click(launchButton);

    // repo not selected yet
    expect(createConversationSpy).not.toHaveBeenCalled();

    // Mock the repository branches API call
    vi.spyOn(OpenHands, "getRepositoryBranches").mockResolvedValue({ branches: [
      { name: "main", commit_sha: "123", protected: false },
      { name: "develop", commit_sha: "456", protected: false },
    ], has_next_page: false, current_page: 1, per_page: 30, total_count: 2 });

    // First select the provider
    const providerDropdown = await waitFor(() =>
      screen.getByTestId("git-provider-dropdown"),
    );
    await userEvent.click(providerDropdown);
    await userEvent.click(screen.getByText("GitHub"));

    // Then select the repository
    const repoInput = await waitFor(() =>
      within(repoConnector).getByTestId("git-repo-dropdown"),
    );

    await userEvent.click(repoInput);

    // Wait for the options to be loaded and displayed
    await waitFor(() => {
      expect(screen.getByText("rbren/polaris")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("rbren/polaris"));

    // Wait for the branch to be auto-selected
    await waitFor(() => {
      const branchInput = screen.getByTestId("git-branch-dropdown-input");
      expect(branchInput).toHaveValue("main");
    });

    await userEvent.click(launchButton);

    expect(createConversationSpy).toHaveBeenCalledExactlyOnceWith(
      "rbren/polaris",
      "github",
      undefined,
      undefined,
      "main",
      undefined,
      undefined,
    );
  });

  it("should change the launch button text to 'Loading...' when creating a conversation", async () => {
    const createConversationSpy = vi.spyOn(OpenHands, "createConversation");
    createConversationSpy.mockImplementation(() => new Promise(() => {})); // Never resolves to keep loading state
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    // Mock the repository branches API call
    vi.spyOn(OpenHands, "getRepositoryBranches").mockResolvedValue({ branches: [
      { name: "main", commit_sha: "123", protected: false },
      { name: "develop", commit_sha: "456", protected: false },
    ], has_next_page: false, current_page: 1, per_page: 30, total_count: 2 });

    renderRepoConnector();

    const launchButton = await screen.findByTestId("repo-launch-button");

    // First select the provider
    const providerDropdown = await waitFor(() =>
      screen.getByTestId("git-provider-dropdown"),
    );
    await userEvent.click(providerDropdown);
    await userEvent.click(screen.getByText("GitHub"));

    // Then select the repository
    const repoInput = await waitFor(() =>
      screen.getByTestId("git-repo-dropdown"),
    );

    await userEvent.click(repoInput);

    // Wait for the options to be loaded and displayed
    await waitFor(() => {
      expect(screen.getByText("rbren/polaris")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("rbren/polaris"));

    // Wait for the branch to be auto-selected
    await waitFor(() => {
      const branchInput = screen.getByTestId("git-branch-dropdown-input");
      expect(branchInput).toHaveValue("main");
    });

    await userEvent.click(launchButton);
    expect(launchButton).toBeDisabled();
    expect(launchButton).toHaveTextContent(/Loading/i);
  });

  it("should not display a button to settings if the user is signed in with their git provider", async () => {
    renderRepoConnector();

    await waitFor(() => {
      expect(
        screen.queryByTestId("navigate-to-settings-button"),
      ).not.toBeInTheDocument();
    });
  });

  it("should display a button to settings if the user needs to sign in with their git provider", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      provider_tokens_set: {},
    });
    renderRepoConnector();

    const goToSettingsButton = await screen.findByTestId(
      "navigate-to-settings-button",
    );
    const dropdown = screen.queryByTestId("git-repo-dropdown");
    const launchButton = screen.queryByTestId("repo-launch-button");
    const providerLinks = screen.queryAllByText(/add git(hub|lab) repos/i);

    expect(dropdown).not.toBeInTheDocument();
    expect(launchButton).not.toBeInTheDocument();
    expect(providerLinks.length).toBe(0);

    expect(goToSettingsButton).toBeInTheDocument();

    await userEvent.click(goToSettingsButton);
    await screen.findByTestId("git-settings-screen");
  });
});
