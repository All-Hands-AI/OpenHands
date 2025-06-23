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
  },
  {
    id: "2",
    full_name: "All-Hands-AI/OpenHands",
    git_provider: "github",
    is_public: true,
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
    retrieveUserGitRepositoriesSpy.mockResolvedValue(MOCK_RESPOSITORIES);

    renderRepoConnector();

    // Wait for the loading state to be replaced with the dropdown
    const dropdown = await waitFor(() => screen.getByTestId("repo-dropdown"));
    await userEvent.click(dropdown);

    await waitFor(() => {
      screen.getByText("rbren/polaris");
      screen.getByText("All-Hands-AI/OpenHands");
    });
  });

  it("should only enable the launch button if a repo is selected", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue(MOCK_RESPOSITORIES);

    renderRepoConnector();

    const launchButton = await screen.findByTestId("repo-launch-button");
    expect(launchButton).toBeDisabled();

    // Wait for the loading state to be replaced with the dropdown
    const dropdown = await waitFor(() => screen.getByTestId("repo-dropdown"));
    await userEvent.click(dropdown);
    await userEvent.click(screen.getByText("rbren/polaris"));

    expect(launchButton).toBeEnabled();
  });

  it("should render the 'add git(hub|lab) repos' links if saas mode", async () => {
    const getConfiSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return the APP_MODE
    getConfiSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    renderRepoConnector();

    await screen.findByText("Add GitHub repos");
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
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue(MOCK_RESPOSITORIES);

    renderRepoConnector();

    const repoConnector = screen.getByTestId("repo-connector");
    const launchButton =
      await within(repoConnector).findByTestId("repo-launch-button");
    await userEvent.click(launchButton);

    // repo not selected yet
    expect(createConversationSpy).not.toHaveBeenCalled();

    // select a repository from the dropdown
    const dropdown = await waitFor(() =>
      within(repoConnector).getByTestId("repo-dropdown"),
    );
    await userEvent.click(dropdown);

    const repoOption = screen.getByText("rbren/polaris");
    await userEvent.click(repoOption);
    await userEvent.click(launchButton);

    expect(createConversationSpy).toHaveBeenCalledExactlyOnceWith(
      "rbren/polaris",
      "github",
      undefined,
      [],
      undefined,
      undefined,
      undefined,
    );
  });

  it("should change the launch button text to 'Loading...' when creating a conversation", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      OpenHands,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue(MOCK_RESPOSITORIES);

    renderRepoConnector();

    const launchButton = await screen.findByTestId("repo-launch-button");

    // Wait for the loading state to be replaced with the dropdown
    const dropdown = await waitFor(() => screen.getByTestId("repo-dropdown"));
    await userEvent.click(dropdown);
    await userEvent.click(screen.getByText("rbren/polaris"));

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
    const dropdown = screen.queryByTestId("repo-dropdown");
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
