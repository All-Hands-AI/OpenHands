import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider } from "react-redux";
import { createRoutesStub } from "react-router";
import { setupStore } from "test-utils";
import userEvent from "@testing-library/user-event";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { MOCK_TASKS } from "#/mocks/task-suggestions-handlers";
import { AuthProvider } from "#/context/auth-context";

const renderTaskSuggestions = (initialProvidersAreSet = true) => {
  const RouterStub = createRoutesStub([
    {
      Component: TaskSuggestions,
      path: "/",
    },
    {
      Component: () => <div data-testid="conversation-screen" />,
      path: "/conversations/:conversationId",
    },
    {
      Component: () => <div data-testid="settings-screen" />,
      path: "/settings",
    },
  ]);

  return render(<RouterStub />, {
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
};

describe("TaskSuggestions", () => {
  const getSuggestedTasksSpy = vi.spyOn(
    SuggestionsService,
    "getSuggestedTasks",
  );

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the task suggestions section", () => {
    renderTaskSuggestions();
    screen.getByTestId("task-suggestions");
  });

  it("should render an empty message if there are no tasks", async () => {
    getSuggestedTasksSpy.mockResolvedValue([]);
    renderTaskSuggestions();
    await screen.findByText(/No tasks available/i);
  });

  it("should render the task groups with the correct titles", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    await waitFor(() => {
      MOCK_TASKS.forEach((taskGroup) => {
        screen.getByText(taskGroup.title);
      });
    });
  });

  it("should render the task cards with the correct task details", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    await waitFor(() => {
      MOCK_TASKS.forEach((task) => {
        screen.getByText(task.title);
      });
    });
  });

  it("should render skeletons when loading", async () => {
    getSuggestedTasksSpy.mockResolvedValue(MOCK_TASKS);
    renderTaskSuggestions();

    const skeletons = screen.getAllByTestId("task-group-skeleton");
    expect(skeletons.length).toBeGreaterThan(0);

    await waitFor(() => {
      MOCK_TASKS.forEach((taskGroup) => {
        screen.getByText(taskGroup.title);
      });
    });

    expect(screen.queryByTestId("task-group-skeleton")).not.toBeInTheDocument();
  });

  it("should display a button to settings if the user needs to sign in with their git provider", async () => {
    renderTaskSuggestions(false);

    expect(getSuggestedTasksSpy).not.toHaveBeenCalled();
    const goToSettingsButton = await screen.findByTestId(
      "navigate-to-settings-button",
    );
    expect(goToSettingsButton).toBeInTheDocument();

    await userEvent.click(goToSettingsButton);
    await screen.findByTestId("settings-screen");
  });
});
