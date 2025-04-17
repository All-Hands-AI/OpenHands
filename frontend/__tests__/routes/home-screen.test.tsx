import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { Provider } from "react-redux";
import { setupStore } from "test-utils";
import HomeScreen from "#/routes/new-home";
import { AuthProvider } from "#/context/auth-context";
import * as GitService from "#/api/git";
import { GitRepository } from "#/types/git";

const RouterStub = createRoutesStub([
  {
    Component: HomeScreen,
    path: "/",
  },
  {
    Component: () => <div data-testid="conversation-screen" />,
    path: "/conversations/:conversationId",
  },
]);

const renderHomeScreen = (initialProvidersAreSet = true) =>
  render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <AuthProvider initialProvidersAreSet={initialProvidersAreSet}>
          <QueryClientProvider client={new QueryClient()}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      </Provider>
    ),
  });

const MOCK_RESPOSITORIES: GitRepository[] = [
  { id: 1, full_name: "octocat/hello-world", git_provider: "github" },
  { id: 2, full_name: "octocat/earth", git_provider: "github" },
];

describe("HomeScreen", () => {
  it("should render", () => {
    renderHomeScreen();
    screen.getByTestId("home-screen");
  });

  it("should render the repository connector and suggested tasks sections", async () => {
    renderHomeScreen();

    screen.getByTestId("repo-connector");
    screen.getByTestId("task-suggestions");
  });

  it("should filter the suggested tasks based on the selected repository", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      GitService,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderHomeScreen();

    const taskSuggestions = screen.getByTestId("task-suggestions");

    // Initially, all tasks should be visible
    await waitFor(() => {
      within(taskSuggestions).getByText("octocat/hello-world");
      within(taskSuggestions).getByText("octocat/earth");
    });

    // Select a repository from the dropdown
    const repoConnector = screen.getByTestId("repo-connector");

    const dropdown = within(repoConnector).getByTestId("repo-dropdown");
    await userEvent.click(dropdown);

    const repoOption = screen.getAllByText("octocat/hello-world")[1];
    await userEvent.click(repoOption);

    // After selecting a repository, only tasks related to that repository should be visible
    await waitFor(() => {
      within(taskSuggestions).getByText("octocat/hello-world");
      expect(
        within(taskSuggestions).queryByText("octocat/earth"),
      ).not.toBeInTheDocument();
    });
  });

  it("should reset the filtered tasks when the selected repository is cleared", async () => {
    const retrieveUserGitRepositoriesSpy = vi.spyOn(
      GitService,
      "retrieveUserGitRepositories",
    );
    retrieveUserGitRepositoriesSpy.mockResolvedValue({
      data: MOCK_RESPOSITORIES,
      nextPage: null,
    });

    renderHomeScreen();

    const taskSuggestions = screen.getByTestId("task-suggestions");

    // Initially, all tasks should be visible
    await waitFor(() => {
      within(taskSuggestions).getByText("octocat/hello-world");
      within(taskSuggestions).getByText("octocat/earth");
    });

    // Select a repository from the dropdown
    const repoConnector = screen.getByTestId("repo-connector");

    const dropdown = within(repoConnector).getByTestId("repo-dropdown");
    await userEvent.click(dropdown);

    const repoOption = screen.getAllByText("octocat/hello-world")[1];
    await userEvent.click(repoOption);

    // After selecting a repository, only tasks related to that repository should be visible
    await waitFor(() => {
      within(taskSuggestions).getByText("octocat/hello-world");
      expect(
        within(taskSuggestions).queryByText("octocat/earth"),
      ).not.toBeInTheDocument();
    });

    // Clear the selected repository
    await userEvent.clear(dropdown);

    // All tasks should be visible again
    await waitFor(() => {
      within(taskSuggestions).getByText("octocat/hello-world");
      within(taskSuggestions).getByText("octocat/earth");
    });
  });

  describe("launch buttons", () => {
    const setupLaunchButtons = async () => {
      const headerLaunchButton = screen.getByTestId("header-launch-button");
      const repoLaunchButton = screen.getByTestId("repo-launch-button");
      const tasksLaunchButtons =
        await screen.findAllByTestId("task-launch-button");

      // Select a repository from the dropdown to enable the repo launch button
      const repoConnector = screen.getByTestId("repo-connector");
      const dropdown = within(repoConnector).getByTestId("repo-dropdown");
      await userEvent.click(dropdown);
      const repoOption = screen.getAllByText("octocat/hello-world")[1];
      await userEvent.click(repoOption);

      expect(headerLaunchButton).not.toBeDisabled();
      expect(repoLaunchButton).not.toBeDisabled();
      tasksLaunchButtons.forEach((button) => {
        expect(button).not.toBeDisabled();
      });

      return {
        headerLaunchButton,
        repoLaunchButton,
        tasksLaunchButtons,
      };
    };

    beforeEach(() => {
      const retrieveUserGitRepositoriesSpy = vi.spyOn(
        GitService,
        "retrieveUserGitRepositories",
      );
      retrieveUserGitRepositoriesSpy.mockResolvedValue({
        data: MOCK_RESPOSITORIES,
        nextPage: null,
      });
    });

    it("should disable the other launch buttons when the header launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton } =
        await setupLaunchButtons();

      // All other buttons should be disabled when the header button is clicked
      await userEvent.click(headerLaunchButton);

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      expect(headerLaunchButton).toBeDisabled();
      expect(repoLaunchButton).toBeDisabled();
      tasksLaunchButtonsAfter.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it("should disable the other launch buttons when the repo launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton } =
        await setupLaunchButtons();

      // All other buttons should be disabled when the header button is clicked
      await userEvent.click(repoLaunchButton);

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      expect(headerLaunchButton).toBeDisabled();
      expect(repoLaunchButton).toBeDisabled();
      tasksLaunchButtonsAfter.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it("should disable the other launch buttons when any task launch button is clicked", async () => {
      renderHomeScreen();
      const { headerLaunchButton, repoLaunchButton, tasksLaunchButtons } =
        await setupLaunchButtons();

      // All other buttons should be disabled when the header button is clicked
      await userEvent.click(tasksLaunchButtons[0]);

      const tasksLaunchButtonsAfter =
        await screen.findAllByTestId("task-launch-button");

      expect(headerLaunchButton).toBeDisabled();
      expect(repoLaunchButton).toBeDisabled();
      tasksLaunchButtonsAfter.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  it("should hide the suggested tasks section if not authed with git(hub|lab)", async () => {
    renderHomeScreen(false);

    const taskSuggestions = screen.queryByTestId("task-suggestions");
    const repoConnector = screen.getByTestId("repo-connector");

    expect(taskSuggestions).not.toBeInTheDocument();
    expect(repoConnector).toBeInTheDocument();
  });
});
