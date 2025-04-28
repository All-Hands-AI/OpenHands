import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { createRoutesStub } from "react-router";
import { setupStore } from "test-utils";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import OpenHands from "#/api/open-hands";
import { AuthProvider } from "#/context/auth-context";
import { TaskCard } from "#/components/features/home/tasks/task-card";
import * as GitService from "#/api/git";
import { GitRepository } from "#/types/git";

const MOCK_TASK_1: SuggestedTask = {
  issue_number: 123,
  repo: "repo1",
  title: "Task 1",
  task_type: "MERGE_CONFLICTS",
  git_provider: "github",
};

const MOCK_TASK_2: SuggestedTask = {
  issue_number: 456,
  repo: "repo2",
  title: "Task 2",
  task_type: "FAILING_CHECKS",
  git_provider: "github",
};

const MOCK_TASK_3: SuggestedTask = {
  issue_number: 789,
  repo: "repo3",
  title: "Task 3",
  task_type: "UNRESOLVED_COMMENTS",
  git_provider: "gitlab",
};

const MOCK_TASK_4: SuggestedTask = {
  issue_number: 101112,
  repo: "repo4",
  title: "Task 4",
  task_type: "OPEN_ISSUE",
  git_provider: "gitlab",
};

const MOCK_RESPOSITORIES: GitRepository[] = [
  { id: 1, full_name: "repo1", git_provider: "github", is_public: true },
  { id: 2, full_name: "repo2", git_provider: "github", is_public: true },
  { id: 3, full_name: "repo3", git_provider: "gitlab", is_public: true },
  { id: 4, full_name: "repo4", git_provider: "gitlab", is_public: true },
];

const renderTaskCard = (task = MOCK_TASK_1) => {
  const RouterStub = createRoutesStub([
    {
      Component: () => <TaskCard task={task} />,
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

describe("TaskCard", () => {
  it("format the issue id", async () => {
    renderTaskCard();

    const taskId = screen.getByTestId("task-id");
    expect(taskId).toHaveTextContent(/#123/i);
  });

  it("should call createConversation when clicking the launch button", async () => {
    const createConversationSpy = vi.spyOn(OpenHands, "createConversation");

    renderTaskCard();

    const launchButton = screen.getByTestId("task-launch-button");
    await userEvent.click(launchButton);

    expect(createConversationSpy).toHaveBeenCalled();
  });

  describe("creating suggested task conversation", () => {
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

    it("should call create conversation with suggest task trigger and selected suggested task", async () => {
      const createConversationSpy = vi.spyOn(OpenHands, "createConversation");

      renderTaskCard(MOCK_TASK_1);

      const launchButton = screen.getByTestId("task-launch-button");
      await userEvent.click(launchButton);

      expect(createConversationSpy).toHaveBeenCalledWith(
        "suggested_task",
        MOCK_RESPOSITORIES[0],
        undefined,
        [],
        undefined,
        MOCK_TASK_1,
      );
    });
  });

  it("should disable the launch button and update text content when creating a conversation", async () => {
    renderTaskCard();

    const launchButton = screen.getByTestId("task-launch-button");
    await userEvent.click(launchButton);

    expect(launchButton).toHaveTextContent(/Loading/i);
    expect(launchButton).toBeDisabled();
  });
});
