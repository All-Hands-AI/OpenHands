import { render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { Provider } from "react-redux";
import { setupStore } from "test-utils";
import HomeScreen from "#/routes/new-home";
import { AuthProvider } from "#/context/auth-context";
import * as GitService from "#/api/git";
import { GitRepository } from "#/types/git";

const renderHomeScreen = () => {
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

  return render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <AuthProvider initialProvidersAreSet>
          <QueryClientProvider client={new QueryClient()}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      </Provider>
    ),
  });
};

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
      within(taskSuggestions).findByText("octocat/hello-world");
      within(taskSuggestions).findByText("octocat/earth");
    });

    // Select a repository from the dropdown
    const repoConnector = screen.getByTestId("repo-connector");

    const dropdown = within(repoConnector).getByTestId("repo-dropdown");
    await userEvent.click(dropdown);

    const repoOption = screen.getAllByText("octocat/hello-world")[1];
    await userEvent.click(repoOption);

    // After selecting a repository, only tasks related to that repository should be visible
    await waitFor(() => {
      within(taskSuggestions).findByText("octocat/hello-world");
      expect(
        within(taskSuggestions).queryByText("octocat/earth"),
      ).not.toBeInTheDocument();
    });
  });

  it.todo(
    "should create a conversation and redirect with the selected task when pressing the launch button in the task suggestions",
  );
});
